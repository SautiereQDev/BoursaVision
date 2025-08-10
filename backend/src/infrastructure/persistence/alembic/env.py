import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Ensure versions dir exists to prevent FileNotFoundError on revision
VERSIONS_DIR = Path(__file__).parent / "versions"
VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Add your model's MetaData object here for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")),
)
import src.infrastructure.persistence.models.alerts  # noqa: E402,F401
import src.infrastructure.persistence.models.fundamental  # noqa: E402,F401
import src.infrastructure.persistence.models.instruments  # noqa: E402,F401
import src.infrastructure.persistence.models.market_data  # noqa: E402,F401
import src.infrastructure.persistence.models.performance  # noqa: E402,F401
import src.infrastructure.persistence.models.portfolios  # noqa: E402,F401
import src.infrastructure.persistence.models.system  # noqa: E402,F401
import src.infrastructure.persistence.models.transactions  # noqa: E402,F401
import src.infrastructure.persistence.models.users  # noqa: E402,F401
from src.infrastructure.persistence.models.base import Base  # noqa: E402

# Set your metadata
# If you have multiple Base classes, merge their metadata
# target_metadata = [Base1.metadata, Base2.metadata, ...]
target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
