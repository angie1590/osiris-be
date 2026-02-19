from __future__ import annotations

from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from osiris.core.settings import get_settings


def get_engine():
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        echo=settings.SQL_ECHO,
        pool_pre_ping=True,
    )
    return engine


# Engine global practico para imports
engine = get_engine()


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI: generador con yield (no contextmanager)."""
    with Session(engine) as session:
        yield session


__all__ = ["get_settings", "engine", "get_session", "SQLModel"]
