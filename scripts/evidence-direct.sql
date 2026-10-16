\pset pager off
SELECT 'users' AS entity, count(*) AS total FROM users
UNION ALL SELECT 'rooms', count(*) FROM rooms
UNION ALL SELECT 'messages', count(*) FROM messages
UNION ALL SELECT 'direct_conversations', count(*) FROM direct_conversations
UNION ALL SELECT 'direct_messages', count(*) FROM direct_messages;
SELECT count(*) AS duplicate_direct_pairs FROM (
  SELECT user_low_id, user_high_id FROM direct_conversations GROUP BY user_low_id, user_high_id HAVING count(*) > 1
) repeated;
SELECT count(*) AS invalid_direct_authors FROM direct_messages m JOIN direct_conversations d ON d.id = m.conversation_id
WHERE m.user_id NOT IN (d.user_low_id, d.user_high_id);
