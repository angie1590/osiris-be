# src/domain/service.py
from typing import Generic, TypeVar, Dict, Any, Tuple, List
from sqlmodel import Session
from .repository import BaseRepository
from src.osiris.core.errors import NotFoundError
from src.osiris.utils.pagination import build_pagination_meta, PaginationMeta

ModelT = TypeVar("ModelT")

class BaseService(Generic[ModelT]):
    repo = None  # cada subclase la setea

    def list(self, session: Session, *, only_active=True, limit=50, offset=0, **kw):
        return self.repo.list(session, only_active=only_active, limit=limit, offset=offset, **kw)

    def list_paginated(self, session: Session, *, only_active=True, limit=50, offset=0, **kw):
        items, total = self.repo.list(session, only_active=only_active, limit=limit, offset=offset, **kw)
        meta = build_pagination_meta(total=total, limit=limit, offset=offset)
        return items, meta

    # Hooks de dominio
    def validate_create(self, data: Dict[str, Any], session: Session) -> None: ...
    def validate_update(self, data: Dict[str, Any], session: Session) -> None: ...
    def on_created(self, obj: ModelT, session: Session) -> None: ...
    def on_updated(self, obj: ModelT, session: Session) -> None: ...
    def on_deleted(self, obj: ModelT, session: Session) -> None: ...

    # Operaciones
    def create(self, session: Session, data: Dict[str, Any]) -> ModelT:
        self.validate_create(data, session)
        obj = self.repo.create(session, data)
        self.on_created(obj, session)
        return obj

    def get(self, session: Session, item_id: Any):
        return self.repo.get(session, item_id)

    def update(self, session: Session, item_id: Any, data: Any):
        db_obj = self.repo.get(session, item_id)
        if not db_obj:
            return None
        return self.repo.update(session, db_obj, data)

    def delete(self, session: Session, item_id: Any) -> bool | None:
        db_obj = self.repo.get(session, item_id)
        if not db_obj:
            return None
        return self.repo.delete(session, db_obj)
