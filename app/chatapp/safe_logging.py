"""Small allowlisted JSON audit records: never format arbitrary text or exceptions."""
from datetime import datetime, timezone
import json
import logging
import re


PATTERNS = (
    re.compile(r'(?P<event>chat_message_saved) room_id=(?P<room_id>\d+) message_id=(?P<message_id>\d+)'),
    re.compile(r'(?P<event>direct_message_saved) conversation_id=(?P<conversation_id>\d+) message_id=(?P<message_id>\d+)'),
    re.compile(r'(?P<event>chat_attachment_saved) scope=(?P<scope>room|direct) target_id=(?P<target_id>\d+) message_id=(?P<message_id>\d+) bytes=(?P<bytes>\d+)'),
    re.compile(r'(?P<event>http_request_rejected) endpoint=(?P<endpoint>[a-zA-Z0-9_.]{1,100}) status=(?P<status>[45]\d\d)'),
)


class SafeJsonFormatter(logging.Formatter):
    def format(self, record):
        fields = {
            'time': datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            'level': record.levelname,
            'service': 'app',
            'event': 'application_error' if record.levelno >= logging.ERROR else 'application_event',
        }
        try:
            message = record.getMessage()
            for pattern in PATTERNS:
                match = pattern.fullmatch(message)
                if match:
                    fields.update(match.groupdict())
                    break
        except Exception:
            pass
        return json.dumps(fields, ensure_ascii=True, separators=(',', ':'))


def configure(logger):
    handler = logging.StreamHandler()
    handler.setFormatter(SafeJsonFormatter())
    logger.handlers[:] = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
