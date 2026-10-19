"""Read-only runtime audit. Never print inspect Env, hashes, cookies, user data or secrets."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import subprocess
import tarfile
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from verify_monitoring import env_values


ROOT = Path(__file__).resolve().parents[1]
SERVICES = {'app', 'nginx', 'postgres', 'pgadmin', 'grafana', 'prometheus', 'cadvisor',
            'postgres-exporter', 'nginx-exporter', 'loki', 'promtail'}


def run(*args):
    proc = subprocess.run(list(args), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    assert proc.returncode == 0, 'Audit command failed: ' + args[0]
    return proc.stdout.decode()


def inspect(*args): return json.loads(run('docker', 'inspect', *args))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--save'); parser.add_argument('--record-live', action='store_true')
    args = parser.parse_args(); checks = []
    ids = run('docker', 'compose', '--profile', 'monitoring', '--profile', 'logging', 'ps', '-q').split()
    objects = inspect(*ids)
    containers = {item['Config']['Labels']['com.docker.compose.service']: item for item in objects}
    assert set(containers) == SERVICES
    assert all(item['State']['Running'] and not item['State']['OOMKilled'] for item in objects)
    for service, uid in (('app', '10001'), ('nginx', '101')):
        item = containers[service]; host = item['HostConfig']
        assert item['Config']['User'].split(':')[0] == uid
        assert host['ReadonlyRootfs'] and not host['Privileged'] and host['CapDrop'] == ['ALL']
        assert 'no-new-privileges:true' in host['SecurityOpt']
        status = run('docker', 'compose', 'exec', '-T', service, 'cat', '/proc/1/status')
        fields = dict(line.split(':', 1) for line in status.splitlines() if ':' in line)
        assert fields['Uid'].split() == [uid] * 4 and int(fields['CapEff'].strip(), 16) == 0
        assert fields['NoNewPrivs'].strip() == '1' and fields['Seccomp'].strip() == '2'
        assert all(not mount['RW'] for mount in item['Mounts'] if mount['Type'] == 'bind')
        assert '/tmp' in host['Tmpfs'] and 'noexec' in host['Tmpfs']['/tmp'] and 'nosuid' in host['Tmpfs']['/tmp']
        print(f'[OK] {service}: UID={uid}, read-only, CapEff=0, NoNewPrivs=1, seccomp=2')
    checks.append('non-root/read-only/cap-drop/no-new-privileges/seccomp')
    for service, source, target in (('nginx', 'nginx/nginx.conf', '/etc/nginx/nginx.conf'),
                                    ('app', 'app/chatapp/routes.py', '/srv/app/chatapp/routes.py')):
        digest = hashlib.sha256((ROOT / source).read_bytes()).hexdigest()
        assert run('docker', 'compose', 'exec', '-T', service, 'sha256sum', target).split()[0] == digest, 'Running source differs: ' + service
    expected = {'nginx': {'8080/tcp': '80'}, 'pgadmin': {'80/tcp': '5050'},
                'grafana': {'3000/tcp': '3000'}, 'prometheus': {'9090/tcp': '9090'}}
    for service, item in containers.items():
        bindings = item['HostConfig'].get('PortBindings') or {}
        assert set(bindings) == set(expected.get(service, {})), 'Unexpected published port: ' + service
        for port, entries in bindings.items():
            assert len(entries) == 1 and entries[0]['HostPort'] == expected[service][port]
            assert entries[0]['HostIp'] == ('0.0.0.0' if service == 'nginx' else '127.0.0.1')
    backend = json.loads(run('docker', 'network', 'inspect', 'de32-chat_backend'))[0]
    assert backend['Internal']
    assert 'de32-chat_backend' not in containers['nginx']['NetworkSettings']['Networks']
    assert 'de32-chat_backend' not in containers['grafana']['NetworkSettings']['Networks']
    assert set(containers['postgres']['NetworkSettings']['Networks']) == {'de32-chat_backend'}
    print('[OK] Docker: chi Nginx public80; admin localhost; app/DB/Loki/Promtail/exporter khong published')
    print('[OK] Backend internal; Nginx/Grafana khong tham gia mang database')
    checks.append('network/ports')
    headers = {'X-Frame-Options': 'SAMEORIGIN', 'X-Content-Type-Options': 'nosniff',
               'Referrer-Policy': 'strict-origin-when-cross-origin',
               'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'}
    for path, expected in (('/healthz',200),('/metrics',404),('/nginx_status',404)):
        try: response = urlopen(Request('http://127.0.0.1' + path, method='HEAD'), timeout=10)
        except HTTPError as error: response = error
        with response:
            assert response.code == expected
            assert all(response.headers.get_all(key) == [value] for key,value in headers.items()), 'Missing or duplicate proxy security header'
    for service in ('app', 'nginx'):
        config = containers[service]['HostConfig']['LogConfig']
        assert config['Type'] == 'json-file' and config['Config']['max-size'] == '10m' and config['Config']['max-file'] == '3'
    sql = """SELECT json_build_object(
      'roles', (SELECT json_agg(json_build_object('name',rolname,'super',rolsuper,'createdb',rolcreatedb,
        'createrole',rolcreaterole,'replication',rolreplication,'bypassrls',rolbypassrls,
        'monitor',pg_has_role(rolname,'pg_monitor','member'))) FROM pg_roles WHERE rolname IN ('chatuser','postgres_exporter')),
      'exporter_write',has_table_privilege('postgres_exporter','public.messages','INSERT,UPDATE,DELETE'),
      'hashes_ok',(SELECT coalesce(bool_and(password_hash LIKE 'scrypt:%' OR password_hash LIKE 'pbkdf2:%'),false) FROM users),
      'app_authid_read',has_table_privilege('chatuser','pg_catalog.pg_authid','SELECT'))::text;"""
    result = json.loads(run('docker', 'compose', 'exec', '-T', 'postgres', 'psql', '-X', '-U', 'postgres', '-d', 'chatdb', '-At', '-c', sql))
    assert {row['name'] for row in result['roles']} == {'chatuser', 'postgres_exporter'}
    for row in result['roles']:
        assert not any(row[field] for field in ('super', 'createdb', 'createrole', 'replication', 'bypassrls'))
        assert row['monitor'] == (row['name'] == 'postgres_exporter')
    assert not result['exporter_write'] and not result['app_authid_read'] and result['hashes_ok']
    app_env = dict(value.split('=', 1) for value in containers['app']['Config']['Env'] if '=' in value)
    assert app_env['DB_USER'] == 'chatuser' and app_env['APP_ENV'] == 'production'
    print('[OK] DB: chatuser/exporter khong superuser/createDB/createRole; exporter pg_monitor, khong ghi messages')
    print('[OK] Mat khau tai khoan deu la hash; app khong doc pg_authid (khong in hash/du lieu)')
    checks.append('database-roles/password-hash')
    values = env_values(ROOT / '.env')
    assert stat.S_IMODE((ROOT / '.env').stat().st_mode) == 0o600
    assert stat.S_IMODE((ROOT / 'work').stat().st_mode) == 0o700
    required = ['POSTGRES_PASSWORD','APP_DB_PASSWORD','POSTGRES_EXPORTER_PASSWORD','SECRET_KEY',
                'PGADMIN_DEFAULT_PASSWORD','GRAFANA_ADMIN_PASSWORD']
    secrets = [values[key] for key in required]
    assert all(len(value) >= 20 and not value.startswith(('change_me_', 'development-only')) for value in secrets)
    assert len(set(secrets)) == len(secrets)
    for name in ('.env', 'work/audit-probe', 'outputs/audit-probe'):
        run('git', 'check-ignore', '--quiet', name)
    forbidden = re.compile(r'(^|/)(\.env|work|outputs)(/|$)|id_ed25519|authorized_keys|known_hosts')
    for revision in run('git', 'rev-list', '--all').splitlines():
        names = run('git', 'ls-tree', '-r', '--name-only', revision).splitlines()
        assert not any(forbidden.search(name) for name in names), 'Private path tracked in Git history'
        archive = subprocess.run(['git','archive','--format=tar',revision], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as saved:
            for member in saved:
                if member.isfile():
                    payload = saved.extractfile(member).read()
                    assert not any(secret.encode() in payload for secret in secrets), 'Configured secret found in Git history'
                    assert not re.search(rb'(?m)^[\t ]*-----BEGIN [A-Z ]*PRIVATE KEY-----[\t ]*$', payload), 'Private key in Git history'
    print('[OK] .env=600/work=700; secret khong mac dinh/khong trung; Git va lich su khong co secret/private path')
    checks.append('secrets/git-history')
    strong = containers['cadvisor']['HostConfig']['Privileged']
    socket_users = sorted(service for service,item in containers.items() if any(mount['Destination'].endswith('docker.sock') or mount['Destination'] == '/var/run' for mount in item['Mounts']))
    assert strong and socket_users == ['cadvisor', 'promtail']
    print('[LIMIT] HTTP lab: chua TLS/Secure cookie; cAdvisor privileged, Promtail root/Docker socket la ngoai le')
    print('HARDENING_INFRA_OK')
    if args.save:
        Path(args.save).write_text(json.dumps({'checks': checks, 'services': len(containers), 'limits': ['HTTP_no_TLS', 'cAdvisor_privileged', 'Promtail_Docker_API']}), encoding='utf-8')
    if args.record_live:
        path = ROOT / 'work/hardening-live.json'
        evidence = json.loads(path.read_text(encoding='utf-8'))
        assert 0 <= time.time() - evidence['at'] < 600, 'Live evidence must be freshly generated'
        assert all(evidence[key] for key in ('headers','csrf','cookie_tamper','socket_origin','private_access','download_headers','logout_revocation'))
        evidence['app_image'] = containers['app']['Image']
        evidence['nginx_config'] = hashlib.sha256((ROOT / 'nginx/nginx.conf').read_bytes()).hexdigest()
        path.write_text(json.dumps(evidence), encoding='utf-8'); path.chmod(0o600)
        print('[OK] Gan ket qua live vua chay voi image app hien tai; khong luu cookie/secret')


if __name__ == '__main__': main()
