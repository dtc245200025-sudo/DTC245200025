\pset pager off
\echo CAC BANG DU LIEU
SELECT tablename, tableowner
FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
\echo CAC TIN NHAN DA LUU TRONG POSTGRESQL
SELECT m.id, r.name AS room, u.username, m.content
FROM messages m
JOIN users u ON u.id = m.user_id
JOIN rooms r ON r.id = m.room_id
ORDER BY m.id DESC LIMIT 10;
