\pset pager off
SELECT 'users' AS entity, count(*) AS total FROM users
UNION ALL SELECT 'messages', count(*) FROM messages;
SELECT column_name FROM information_schema.columns
WHERE table_name = 'users' AND column_name IN ('display_name', 'bio', 'profile_public', 'email_public', 'avatar_data', 'auth_version')
ORDER BY column_name;
SELECT count(*) AS avatars_saved FROM users WHERE avatar_data IS NOT NULL;
SELECT count(*) AS passwords_stored_as_hash FROM users WHERE password_hash LIKE 'scrypt:%' OR password_hash LIKE 'pbkdf2:%';
