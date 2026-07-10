from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.unit
def test_postgres_vps_compose_does_not_publish_database_port_and_backup_uses_tls():
    compose_path = PROJECT_ROOT / "infra" / "docker-compose.postgres-vps.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    postgres_service = compose["services"]["postgres"]
    backup_service = compose["services"]["backup"]

    assert "ports" not in postgres_service
    assert postgres_service["expose"] == ["5432"]
    assert compose["networks"]["gennomx_ai_private"]["internal"] is True
    assert backup_service["environment"]["PGSSLMODE"] == "require"
    assert backup_service["environment"]["PGSSLROOTCERT"] == "/run/secrets/postgres/ca.crt"


@pytest.mark.unit
def test_postgres_vps_bootstrap_is_rerunnable_and_not_database_name_hardcoded():
    bootstrap_path = PROJECT_ROOT / "infra" / "postgres" / "bootstrap_roles_vps.sql"
    bootstrap = bootstrap_path.read_text(encoding="utf-8")

    assert "GRANT CONNECT ON DATABASE gennomx" not in bootstrap
    assert "current_database()" in bootstrap
    assert "ALTER ROLE gennomx_app" in bootstrap
    assert "PASSWORD :'gennomx_app_password'" in bootstrap
    assert "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO gennomx_readonly" in bootstrap


@pytest.mark.unit
def test_vps_app_compose_does_not_publish_ports_and_uses_internal_networks():
    """The VPS app compose (redis+worker+beat+api) must not publish any port
    publicly and must connect to the Postgres via the internal external network."""
    compose_path = PROJECT_ROOT / "infra" / "docker-compose.vps-app.yml"
    compose = yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    services = compose["services"]
    for name, svc in services.items():
        assert "ports" not in svc, f"service {name} must not publish ports"

    assert services["redis"]["healthcheck"] is not None
    assert "--concurrency=1" in services["worker"]["command"]
    assert services["beat"]["command"][3] == "beat"

    assert "gennomx-ai-postgres-ready-private" in compose["networks"]
    assert compose["networks"]["gennomx-ai-postgres-ready-private"]["external"] is True
    assert compose["networks"]["gennomx_ai_app"]["internal"] is True

    assert "profiles" in services["api"]
    assert "api" in services["api"]["profiles"]
