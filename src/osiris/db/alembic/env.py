from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlmodel import SQLModel

# Usa la misma configuración que la app
from src.osiris.core.db import get_settings

# IMPORTA tus modelos para que Alembic detecte las tablas
from osiris.modules.aux.tipo_contribuyente import entity as tipo_contribuyente_entity
from src.osiris.modules.common.rol import entity as rol_entity  # noqa: F401
from src.osiris.modules.common.empresa import entity as empresa_entity  # noqa: F401
from src.osiris.modules.common.sucursal import entity as sucursal_entity  # noqa: F401
from src.osiris.modules.common.punto_emision import entity as punto_emision_entity  # noqa: F401
from src.osiris.modules.common.persona import entity as persona_entity  # noqa: F401
from src.osiris.modules.common.tipo_cliente import entity as tipo_cliente_entity  # noqa: F401
from src.osiris.modules.common.usuario import entity as usuario_entity  # noqa: F401
from src.osiris.modules.common.cliente import entity as cliente_entity  # noqa: F401
from src.osiris.modules.common.cargo import entity as cargo_entity  # noqa: F401


# Config Alembic y logging
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata global para autogenerate
target_metadata = SQLModel.metadata


def _get_database_url() -> str:
    """
    Prioridad:
    1) DB_URL_ALEMBIC (útil en CI/CD)
    2) settings.DATABASE_URL (si está definida en .env)
    3) settings.build_url() con variables POSTGRES_*
    """
    override = os.getenv("DB_URL_ALEMBIC")
    if override:
        return override
    settings = get_settings()
    return settings.DATABASE_URL or settings.build_url()


def run_migrations_offline() -> None:
    """Modo offline: sin Engine."""
    url = _get_database_url()
    config.set_main_option("sqlalchemy.url", url)

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
    """Modo online: con Engine y conexión activa."""
    url = _get_database_url()
    config.set_main_option("sqlalchemy.url", url)

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,  # Alembic maneja la conexión
        future=True,
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
