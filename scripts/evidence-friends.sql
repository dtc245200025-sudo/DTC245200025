\pset pager off
SELECT 'users' AS entity, count(*) AS total FROM users
UNION ALL SELECT 'rooms', count(*) FROM rooms
UNION ALL SELECT 'messages', count(*) FROM messages;
SELECT status, count(*) AS relations FROM friendships GROUP BY status ORDER BY status;
SELECT count(*) AS duplicate_pairs FROM (
  SELECT user_low_id, user_high_id FROM friendships GROUP BY user_low_id, user_high_id HAVING count(*) > 1
) repeated;
SELECT count(*) AS invalid_pairs FROM friendships
WHERE user_low_id >= user_high_id OR requester_id NOT IN (user_low_id, user_high_id);
