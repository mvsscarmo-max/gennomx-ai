-- GennomX AI — Supabase database bootstrap
--
-- Run this once in the Supabase SQL Editor or with psql as an administrative
-- database user before running Alembic migrations.
--
-- Replace all CHANGE_ME_* placeholders before execution. Do not commit real
-- passwords or project credentials.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_migrator') THEN
    CREATE ROLE gennomx_migrator LOGIN PASSWORD 'CHANGE_ME_MIGRATOR_PASSWORD' NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_worker') THEN
    CREATE ROLE gennomx_worker LOGIN PASSWORD 'CHANGE_ME_WORKER_PASSWORD' NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_app') THEN
    CREATE ROLE gennomx_app LOGIN PASSWORD 'CHANGE_ME_APP_PASSWORD' NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_readonly') THEN
    CREATE ROLE gennomx_readonly LOGIN PASSWORD 'CHANGE_ME_READONLY_PASSWORD' NOCREATEDB NOCREATEROLE NOREPLICATION;
  END IF;
END
$$;

ALTER ROLE gennomx_migrator NOBYPASSRLS;
ALTER ROLE gennomx_worker NOBYPASSRLS;
ALTER ROLE gennomx_app NOBYPASSRLS;
ALTER ROLE gennomx_readonly NOBYPASSRLS;

GRANT CONNECT ON DATABASE postgres TO gennomx_migrator, gennomx_worker, gennomx_app, gennomx_readonly;
GRANT USAGE, CREATE ON SCHEMA public TO gennomx_migrator;
GRANT USAGE ON SCHEMA public TO gennomx_worker, gennomx_app, gennomx_readonly;

-- Re-run this grant block after migrations when new tables are created.
-- Supabase may reject ALTER DEFAULT PRIVILEGES for another role through the
-- managed postgres user, so grants are applied explicitly after Alembic.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO gennomx_app, gennomx_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO gennomx_worker;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gennomx_worker;

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
