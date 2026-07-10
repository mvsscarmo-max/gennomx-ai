\set ON_ERROR_STOP on

-- GennomX AI - PostgreSQL/pgvector bootstrap for the Hostinger VPS.
--
-- This file is intentionally psql-oriented because passwords must be supplied
-- through psql variables or the container environment, never committed here.
--
-- Required psql variables when run manually:
--   gennomx_migrator_password
--   gennomx_worker_password
--   gennomx_app_password
--   gennomx_readonly_password

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

SELECT format(
  'CREATE ROLE gennomx_migrator LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
  :'gennomx_migrator_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_migrator') \gexec

SELECT format(
  'CREATE ROLE gennomx_worker LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
  :'gennomx_worker_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_worker') \gexec

SELECT format(
  'CREATE ROLE gennomx_app LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
  :'gennomx_app_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_app') \gexec

SELECT format(
  'CREATE ROLE gennomx_readonly LOGIN PASSWORD %L NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS',
  :'gennomx_readonly_password'
)
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gennomx_readonly') \gexec

ALTER ROLE gennomx_migrator
  WITH LOGIN PASSWORD :'gennomx_migrator_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
ALTER ROLE gennomx_worker
  WITH LOGIN PASSWORD :'gennomx_worker_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
ALTER ROLE gennomx_app
  WITH LOGIN PASSWORD :'gennomx_app_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
ALTER ROLE gennomx_readonly
  WITH LOGIN PASSWORD :'gennomx_readonly_password' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;

SELECT format(
  'GRANT CONNECT ON DATABASE %I TO gennomx_migrator, gennomx_worker, gennomx_app, gennomx_readonly',
  current_database()
) \gexec
GRANT USAGE, CREATE ON SCHEMA public TO gennomx_migrator;
GRANT USAGE ON SCHEMA public TO gennomx_worker, gennomx_app, gennomx_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE gennomx_migrator IN SCHEMA public
  GRANT SELECT ON TABLES TO gennomx_app, gennomx_readonly;
ALTER DEFAULT PRIVILEGES FOR ROLE gennomx_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gennomx_worker;
ALTER DEFAULT PRIVILEGES FOR ROLE gennomx_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO gennomx_worker;
ALTER DEFAULT PRIVILEGES FOR ROLE gennomx_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO gennomx_readonly;

-- Re-run this grant block after Alembic migrations and after restores.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO gennomx_app, gennomx_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gennomx_worker;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gennomx_worker;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gennomx_readonly;

DO $$
DECLARE
  audit_table text;
BEGIN
  FOREACH audit_table IN ARRAY ARRAY['mcp_query_logs', 'security_events', 'manual_corrections']
  LOOP
    IF to_regclass(format('public.%I', audit_table)) IS NOT NULL THEN
      EXECUTE format('GRANT INSERT ON TABLE public.%I TO gennomx_app', audit_table);
    END IF;
  END LOOP;
END
$$;

SELECT rolname, rolsuper, rolbypassrls
FROM pg_roles
WHERE rolname IN ('gennomx_migrator', 'gennomx_worker', 'gennomx_app', 'gennomx_readonly')
ORDER BY rolname;
