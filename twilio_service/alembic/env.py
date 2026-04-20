"""alembic/env.py for twilio_service.

This service may share one PostgreSQL database with other services.
To prevent migration/version conflicts, Alembic uses a dedicated schema
and stores its alembic_version table in that same schema.
"""
import os
import re
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# ── Make app importable from twilio_service/ ─────────────────────────────────
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.sql_db import Base  # noqa: E402
# Import all models so their metadata is registered with Base
from app.models import Targets, TwilioCalls, TwilioResponses  # noqa: E402, F401

# ── Alembic config ────────────────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override DB URL from the service's own .env so alembic.ini doesn't need
# a hard-coded password.
from app.config import POSTGRES_DB_URL, TWILIO_DB_SCHEMA  # noqa: E402
config.set_main_option("sqlalchemy.url", POSTGRES_DB_URL)

target_metadata = Base.metadata

_VALID_SCHEMA_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _normalize_schema_name(raw_schema: str) -> str:
    schema = (raw_schema or "").strip()
    if not schema:
        return "twilio"
    if not _VALID_SCHEMA_RE.match(schema):
        raise ValueError(
            "Invalid TWILIO_DB_SCHEMA. Use only letters, numbers, and underscores."
        )
    return schema


DB_SCHEMA = _normalize_schema_name(TWILIO_DB_SCHEMA)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_schemas=True,
        version_table_schema=DB_SCHEMA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
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
        # SQLAlchemy 2.x opens an implicit transaction on first execute.
        # Commit schema/search_path setup explicitly so migration DDL is not
        # accidentally rolled back when the connection context exits.
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{DB_SCHEMA}"'))
        connection.execute(text(f'SET search_path TO "{DB_SCHEMA}", public'))
        connection.commit()
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            version_table_schema=DB_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
