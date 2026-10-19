import json
import logging
import sys

from test_app import make_app
from chatapp.safe_logging import SafeJsonFormatter


def test_audit_formatter_only_allows_safe_fields():
    formatter = SafeJsonFormatter()
    for message, event in (
        ('chat_message_saved room_id=2 message_id=3', 'chat_message_saved'),
        ('direct_message_saved conversation_id=2 message_id=3', 'direct_message_saved'),
        ('chat_attachment_saved scope=direct target_id=2 message_id=3 bytes=42', 'chat_attachment_saved'),
        ('http_request_rejected endpoint=chat_tools.history status=404', 'http_request_rejected'),
    ):
        result = json.loads(formatter.format(logging.makeLogRecord({'msg': message, 'levelname': 'INFO', 'levelno': logging.INFO})))
        assert result['event'] == event
        assert 'message' not in result and 'content' not in result


def test_arbitrary_message_and_exception_never_leak():
    formatter = SafeJsonFormatter()
    try:
        raise ValueError('PRIVATE_PASSWORD_CANARY')
    except ValueError:
        record = logging.makeLogRecord({'msg': 'email=%s token=PRIVATE_TOKEN', 'args': ('private@example.test',),
                                       'levelno': logging.ERROR, 'levelname': 'ERROR', 'exc_info': sys.exc_info()})
        rendered = formatter.format(record)
    assert json.loads(rendered)['event'] == 'application_error'
    for secret in ('PRIVATE_PASSWORD', 'PRIVATE_TOKEN', 'private@example', 'ValueError'):
        assert secret not in rendered
    record = logging.makeLogRecord({'msg': 'chat_message_saved room_id=2 message_id=3 secret=CANARY', 'levelno': logging.INFO})
    assert json.loads(formatter.format(record))['event'] == 'application_event'


def test_http_rejection_logs_endpoint_not_path_or_query():
    app = make_app()
    captured = []
    class Capture(logging.Handler):
        def emit(self, record): captured.append(SafeJsonFormatter().format(record))
    handler = Capture(); app.logger.addHandler(handler)
    try:
        assert app.test_client().get('/private-path-canary?token=PRIVATE_QUERY').status_code == 404
    finally:
        app.logger.removeHandler(handler)
    rows = [json.loads(line) for line in captured]
    assert any(row.get('event') == 'http_request_rejected' and row['status'] == '404' for row in rows)
    assert 'PRIVATE_QUERY' not in str(captured) and 'private-path-canary' not in str(captured)
