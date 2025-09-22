from __future__ import annotations

from functools import lru_cache
from typing import Generator, Optional

from pydantic_settings import BaseSettings
from sqlmodel import Session, SQLModel, create_engine


class Settings(BaseSettings):
    # URL completa (preferida). En tu .env.development debe usar driver síncrono:
    # postgresql+psycopg://usuario:password@host/db
    DATABASE_URL: Optional[str] = None

    # Fallback si no pasas DATABASE_URL (se arma con POSTGRES_*)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "postgres"

    # Log SQL (respeta SQL_ECHO=true/false en .env)
    SQL_ECHO: bool = False

    # Nota: el archivo .env se inyecta por docker-compose (env_file).
    # No fijamos env_file aquí para mantenerlo simple y sin acoplar rutas.

    def build_url(self) -> str:
        # Driver síncrono por defecto
        driver = "postgresql+psycopg"
        return (
            f"{driver}://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_engine():
    settings = get_settings()
    url = settings.DATABASE_URL or settings.build_url()
    # Alembic controla el esquema; aquí no llamamos a create_all
    engine = create_engine(
        url,
        echo=settings.SQL_ECHO,
        pool_pre_ping=True,
    )
    return engine


# Engine global práctico para imports
engine = get_engine()


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI: generador con yield (no contextmanager)."""
    with Session(engine) as session:
        yield session


__all__ = ["Settings", "get_settings", "engine", "get_session", "SQLModel"]
