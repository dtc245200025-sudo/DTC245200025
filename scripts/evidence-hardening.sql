\pset pager off
\echo ROLE POSTGRESQL - KHONG CO QUYEN QUAN TRI
SELECT rolname, rolsuper AS superuser, rolcreatedb AS create_db, rolcreaterole AS create_role,
       pg_has_role(rolname, 'pg_monitor', 'member') AS monitor
FROM pg_roles WHERE rolname IN ('chatuser', 'postgres_exporter') ORDER BY rolname;
