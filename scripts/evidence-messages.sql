\pset pager off
SELECT 'users' AS entity,count(*) AS total FROM users
UNION ALL SELECT 'room_messages',count(*) FROM messages
UNION ALL SELECT 'direct_messages',count(*) FROM direct_messages
UNION ALL SELECT 'attachments',count(*) FROM chat_attachments
UNION ALL SELECT 'receipts',count(*) FROM message_receipts;
SELECT count(*) AS delivered, count(seen_at) AS seen FROM message_receipts WHERE delivered_at IS NOT NULL;
SELECT count(*) AS invalid_receipt_times FROM message_receipts WHERE seen_at IS NOT NULL AND (delivered_at IS NULL OR seen_at < delivered_at);
SELECT count(*) AS oversized_attachments FROM chat_attachments WHERE byte_size > 10485760;
SELECT count(*) AS legacy_room_messages FROM messages WHERE NOT receipts_tracked;
