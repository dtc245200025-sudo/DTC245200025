"""Read-only Loki/Grafana proof, using internal wget without publishing Loki's port."""
import argparse
import json
from pathlib import Path
import subprocess
import time
from urllib.parse import urlencode

from verify_monitoring import api, env_values


QUERIES = (
    '{service="app"} |~ "chat_message_saved|direct_message_saved|chat_attachment_saved"',
    '{service="nginx"} | json | route="/healthz" | status=200',
    '{service="app"} | json | event="http_request_rejected" | status>=400',
)


def internal_get(url):
    result = subprocess.run(['docker', 'compose', 'exec', '-T', 'grafana', 'wget', '-q', '-T', '10', '-O', '-', url],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    if result.returncode: raise RuntimeError('Internal logging endpoint unavailable')
    return result.stdout.decode()


def rows(query, start, end=None):
    params = {'query': query, 'start': start, 'end': str(time.time_ns()) if end is None else end,
              'limit': '1000', 'direction': 'forward'}
    result = json.loads(internal_get('http://loki:3100/loki/api/v1/query_range?' + urlencode(params)))
    assert result['status'] == 'success'
    return [(stream['stream'], value) for stream in result['data']['result'] for value in stream['values']]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', default='.env')
    parser.add_argument('--evidence', default='work/logging-evidence.json')
    parser.add_argument('--save')
    parser.add_argument('--persistence')
    args = parser.parse_args()
    evidence = json.loads(Path(args.evidence).read_text(encoding='utf-8'))
    deadline = time.monotonic() + 90
    while True:
        try:
            assert internal_get('http://loki:3100/ready').strip() == 'ready'
            assert 'Ready' in internal_get('http://promtail:9080/ready')
            all_rows = rows('{service=~"app|nginx"}', evidence['start'])
            assert {label['service'] for label, _ in all_rows} == {'app', 'nginx'}
            for expression in QUERIES:
                assert rows(expression, evidence['start'])
            for item in evidence['messages']:
                query = '{service="app"} | json | event="' + item['event'] + '" | message_id="' + str(item['id']) + '"'
                assert rows(query, evidence['start'])
            break
        except (AssertionError, RuntimeError):
            assert time.monotonic() < deadline, 'Logs not ingested within90s'
            time.sleep(3)
    print('[OK] Loki va Promtail ready; log app/Nginx that, du3truyvan LogQL')
    for labels, (_, line) in all_rows:
        record = json.loads(line)
        assert labels['service'] in ('app', 'nginx')
        # Loki may attach these two bounded, inferred metadata fields.
        assert set(labels) <= {'service', 'event', 'level', 'detected_level', 'service_name'}
        assert labels.get('service_name', labels['service']) == labels['service']
        assert evidence['canary'] not in line, 'Private canary leaked into Loki'
        assert not (set(record) & {'username', 'email', 'password', 'token', 'content', 'filename', 'user_agent', 'remote_addr', 'request'})
    print('[OK] Canary noi dung/ten tep/query/path/UA khong vao Loki; nhan khong co ID nguoi dung')
    values = env_values(args.env); auth = (values['GRAFANA_ADMIN_USER'], values['GRAFANA_ADMIN_PASSWORD'])
    for key, secret in values.items():
        if ('PASSWORD' in key or key == 'SECRET_KEY') and len(secret) >= 8:
            assert all(secret not in line for _, (_, line) in all_rows), 'A configured secret leaked into Loki'
    health = api('http://127.0.0.1:3000', '/api/datasources/uid/loki/health', auth)
    assert health['status'].upper() == 'OK'
    now = int(time.time() * 1000)
    rendered = api('http://127.0.0.1:3000', '/api/ds/query', auth, {'from': str(int(evidence['start']) // 1000000), 'to': str(now),
        'queries': [{'refId': chr(65 + index), 'datasource': {'type': 'loki', 'uid': 'loki'}, 'expr': query,
                     'queryType': 'range', 'maxLines': 100, 'intervalMs': 1000} for index, query in enumerate(QUERIES)]})
    assert len(rendered['results']) == 3
    assert all(not result.get('error') and result.get('frames') and any(frame.get('data', {}).get('values') and all(frame['data']['values']) for frame in result['frames']) for result in rendered['results'].values())
    print('[OK] Grafana Loki datasource OK; 3/3 truyvan qua datasource API co log')
    if args.save:
        end = str(time.time_ns()); snapshot = rows('{service="app"}', evidence['start'], end)
        Path(args.save).write_text(json.dumps({'start': evidence['start'], 'end': end,
            'samples': [[labels, value] for labels, value in snapshot]}), encoding='utf-8')
        print('[OK] Luu mau audit khong noi dung rieng tu de doi chieu persistence')
    if args.persistence:
        saved = json.loads(Path(args.persistence).read_text(encoding='utf-8'))
        current = rows('{service="app"}', saved['start'], saved['end'])
        assert sorted(json.dumps(row, sort_keys=True) for row in current) == sorted(json.dumps(row, sort_keys=True) for row in saved['samples'])
        print('LOGGING_PERSISTENCE_OK: giu log cu va khong lap audit app sau recreate Loki/Promtail')
    print('GIAI_DOAN_6_OK')


if __name__ == '__main__': main()
