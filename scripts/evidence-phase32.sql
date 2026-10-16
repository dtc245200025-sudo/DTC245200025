\pset pager off
SELECT 'users' AS entity, count(*) AS total FROM users
UNION ALL SELECT 'rooms', count(*) FROM rooms
UNION ALL SELECT 'messages', count(*) FROM messages;
SELECT visibility, join_mode, count(*) AS rooms FROM rooms GROUP BY visibility, join_mode ORDER BY visibility, join_mode;
SELECT count(*) AS over_capacity_rooms FROM rooms r
WHERE max_members IS NOT NULL AND (SELECT count(*) FROM room_members m WHERE m.room_id=r.id) > max_members;
SELECT status, count(*) AS requests FROM room_join_requests GROUP BY status ORDER BY status;
SELECT count(*) AS room_passwords_hashed FROM rooms WHERE password_hash LIKE 'scrypt:%' OR password_hash LIKE 'pbkdf2:%';
SELECT count(*) AS invitation_hashes_only FROM rooms WHERE length(invite_token_hash)=64;
