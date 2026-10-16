\pset pager off
SELECT 'users' AS entity, count(*) AS total FROM users
UNION ALL SELECT 'messages', count(*) FROM messages;
SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'email';
SELECT indexname FROM pg_indexes WHERE indexname = 'uq_users_email_lower';
