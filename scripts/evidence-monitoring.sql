\echo QUYEN ROLE GIAM SAT POSTGRESQL
SELECT rolname, rolsuper, rolcreatedb, rolcreaterole,
       pg_has_role(rolname, 'pg_monitor', 'member') AS pg_monitor_member
FROM pg_roles WHERE rolname = 'postgres_exporter';
