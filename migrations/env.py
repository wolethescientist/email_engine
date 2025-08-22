from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Ensure project root is on sys.path so 'app' can be imported
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# add your model's MetaData object here
# for 'autogenerate' support
from app.db.session import Base
from app.db.models.user import User  # noqa: F401
from app.db.models.email import Email, Attachment  # noqa: F401

target_metadata = Base.metadata


def get_url():
    # Prefer app settings (loads from .env via pydantic-settings or python-dotenv fallback)
    try:
        from app.core.config import get_settings
        return get_settings().DATABASE_URL
    except Exception:
        # Fallback to environment variable or alembic.ini value
        return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()