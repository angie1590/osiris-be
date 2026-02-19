from __future__ import annotations

from typing import Generator

from sqlalchemy import event, true
from sqlalchemy.orm import with_loader_criteria
from sqlmodel import Session, SQLModel, create_engine

from osiris.core.settings import get_settings
from osiris.domain.base_models import SoftDeleteMixin


SOFT_DELETE_INCLUDE_INACTIVE_OPTION = "include_inactive"


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


@event.listens_for(Session, "do_orm_execute")
def _apply_soft_delete_filter(execute_state):
    if not execute_state.is_select:
        return
    if execute_state.execution_options.get(SOFT_DELETE_INCLUDE_INACTIVE_OPTION, False):
        return
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(
            SoftDeleteMixin,
            lambda cls: cls.activo.is_(True) if hasattr(cls, "activo") else true(),
            include_aliases=True,
        )
    )


def get_session() -> Generator[Session, None, None]:
    """Dependencia FastAPI: generador con yield (no contextmanager)."""
    with Session(engine) as session:
        yield session


__all__ = ["get_settings", "engine", "get_session", "SQLModel"]
