-- GennomX AI — PostgreSQL initialization
-- Executed once when container starts fresh

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector

-- Group roles only. Login/service principals and credentials are provisioned
-- outside this repository and receive membership in one of these roles.
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_app') THEN
    CREATE ROLE gennomx_app NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_worker') THEN
    CREATE ROLE gennomx_worker NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'gennomx_readonly') THEN
    CREATE ROLE gennomx_readonly NOLOGIN;
  END IF;
END
$$;

GRANT CONNECT ON DATABASE gennomx TO gennomx_app;
GRANT CONNECT ON DATABASE gennomx TO gennomx_worker;
GRANT CONNECT ON DATABASE gennomx TO gennomx_readonly;
GRANT USAGE ON SCHEMA public TO gennomx_app, gennomx_worker, gennomx_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT ON TABLES TO gennomx_app, gennomx_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO gennomx_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO gennomx_worker;
