import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.append(os.getcwd())

# Import shared Base and DB URL
from app.sql_db import Base
from app.config import POSTGRES_DB_URL

# Import ALL models so their tables are registered in Base.metadata
from app.models import (  # noqa: F401
    Targets, Calls, Emotions, Models, Admins,
    PasswordResetTokens, ErrorLogs, FlaggedTargets,
)
from app.twilio.models import (  # noqa: F401
    TwilioTargets, TwilioCalls, TwilioResponses,
)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", POSTGRES_DB_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
