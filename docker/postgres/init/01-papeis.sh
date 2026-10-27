#!/bin/bash
# Papéis do banco (executado uma vez, na criação do volume, pelo superusuário do container).
#   app_owner: dono de todos os objetos; NOLOGIN; BYPASSRLS só para migrações/seeds e funções SECURITY DEFINER.
#   app_user:  conexão da API; NOBYPASSRLS (o RLS vale de verdade).
#   app_etl:   conexão dos workers de carga; NOBYPASSRLS, com políticas próprias.
# As migrações conectam como superusuário e fazem SET ROLE app_owner (ver backend/alembic/env.py).
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
     -v app_user_pwd="$APP_USER_PASSWORD" \
     -v app_etl_pwd="$APP_ETL_PASSWORD" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
CREATE ROLE app_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS;
CREATE ROLE app_user  LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'app_user_pwd';
CREATE ROLE app_etl   LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS PASSWORD :'app_etl_pwd';
SELECT format('ALTER DATABASE %I OWNER TO app_owner', current_database()) \gexec
SQL
