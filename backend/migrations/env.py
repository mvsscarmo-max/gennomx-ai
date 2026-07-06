import os
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.db_url import coerce_database_url

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is part of the project runtime
    load_dotenv = None

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if load_dotenv is not None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Override sqlalchemy.url from environment variable if set
db_url = os.getenv("DATABASE_URL_SYNC")
if db_url:
    config.set_main_option("sqlalchemy.url", coerce_database_url(db_url, async_driver=False))

target_metadata = None
cmd_opts = getattr(config, "cmd_opts", None)
needs_model_metadata = bool(getattr(cmd_opts, "autogenerate", False))
if not context.is_offline_mode() and needs_model_metadata:
    # Model metadata is needed for online autogeneration, not deterministic migrations.
    import app.models.db  # noqa: F401 — triggers all model imports
    from app.database import Base

    target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
