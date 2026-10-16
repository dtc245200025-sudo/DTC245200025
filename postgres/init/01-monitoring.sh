#!/bin/sh
set -eu

psql --set ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set exporter_password="$POSTGRES_EXPORTER_PASSWORD" \
  --set app_user="$APP_DB_USER" --set app_password="$APP_DB_PASSWORD" \
  --set db_name="$POSTGRES_DB" <<'SQL'
CREATE USER :"app_user" WITH PASSWORD :'app_password';
GRANT CONNECT ON DATABASE :"db_name" TO :"app_user";
GRANT USAGE, CREATE ON SCHEMA public TO :"app_user";
CREATE USER postgres_exporter WITH PASSWORD :'exporter_password';
GRANT pg_monitor TO postgres_exporter;
GRANT CONNECT ON DATABASE :"db_name" TO postgres_exporter;
SQL
