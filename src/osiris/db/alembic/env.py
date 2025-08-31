from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool, create_engine, text
from sqlalchemy.engine.url import make_url, URL

from sqlmodel import SQLModel
target_metadata = SQLModel.metadata

from alembic import context
from src.osiris.db.database import Base

from dotenv import load_dotenv
from src.osiris.modules.common.rol import models as rol_models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.
# Paso 1: cargar variables de entorno dinámicamente
env = os.getenv("ENVIRONMENT", "development")
dotenv_path = f".env.{env}"
load_dotenv(dotenv_path=dotenv_path)

# Paso 2: asignar la URL desde .env
db_url = os.getenv("DB_URL_ALEMBIC")
if not db_url:
    raise Exception(f"DB_URL_ALEMBIC no está definido en {dotenv_path}")
config.set_main_option("sqlalchemy.url", db_url)

# Paso 3: incluir metadata para autogeneración
target_metadata = SQLModel.metadata

def _admin_url_for_postgres(target: URL) -> URL:
    """Misma URL pero apuntando a la BD administrativa 'postgres'."""
    return target.set(database="postgres")

def ensure_database_exists(db_url_str: str) -> None:
    """
    Si la base de datos (db_url_str.database) no existe, la crea.
    PostgreSQL no tiene 'CREATE DATABASE IF NOT EXISTS', por eso consultamos pg_database.
    """
    target_url = make_url(db_url_str)
    admin_url = _admin_url_for_postgres(target_url)

    # AUTOCOMMIT requerido para CREATE DATABASE
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT", future=True)
    dbname = target_url.database

    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :d"),
            {"d": dbname},
        ).scalar()
        if not exists:
            # Opcional: OWNER {target_url.username}, ENCODING/LC, TEMPLATE
            conn.execute(text(f'CREATE DATABASE "{dbname}"'))
    admin_engine.dispose()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
