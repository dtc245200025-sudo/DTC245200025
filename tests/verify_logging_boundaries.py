"""Negative collector-boundary fixtures, not presented as application activity."""
import json
import secrets
import subprocess
import time

from verify_logging import rows


def main():
    marker = 'LOGGING_BOUNDARY_' + secrets.token_hex(12)
    start = str(time.time_ns())
    code = 'import json,os,time;print(json.dumps({"time":"boundary-test","level":"INFO","service":"app","event":"chat_message_saved","probe":os.environ["PROBE"]}),flush=True);time.sleep(20)'
    for project, oneoff in (('de32-chat', 'True'), ('de32-boundary-test', 'False')):
        subprocess.run(['docker', 'run', '--detach', '--rm', '--network', 'none',
            '--label', 'com.docker.compose.project=' + project,
            '--label', 'com.docker.compose.service=app', '--label', 'com.docker.compose.oneoff=' + oneoff,
            '-e', 'PROBE=' + marker, '--entrypoint', 'python', 'de32-chat-app', '-u', '-c', code],
            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
    time.sleep(12)  # More than two5s discovery cycles and a batch interval.
    assert not rows('{service="app"} |= "' + marker + '"', start), 'Collector included one-off or other project'
    print('LOGGING_BOUNDARIES_OK: bo one-off va project khac; fixture tu ket thuc va tu xoa')


if __name__ == '__main__': main()
