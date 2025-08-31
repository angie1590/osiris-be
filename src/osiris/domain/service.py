# src/domain/service.py
from typing import Generic, TypeVar, Dict, Any, Tuple, List
from sqlmodel import Session
from .repository import BaseRepository
from src.osiris.core.errors import NotFoundError

ModelT = TypeVar("ModelT")

class BaseService(Generic[ModelT]):
    def __init__(self, repo: BaseRepository[ModelT]) -> None:
        self.repo = repo

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

    def get(self, session: Session, id_) -> ModelT:
        obj = self.repo.get(session, id_)
        if not obj:
            raise NotFoundError(f"{self.repo.model.__name__} {id_} not found")
        return obj

    def list(self, session: Session, *, only_active=True, limit=50, offset=0) -> Tuple[List[ModelT], int]:
        return self.repo.list(session, only_active=only_active, limit=limit, offset=offset)

    def update(self, session: Session, id_, data: Dict[str, Any]) -> ModelT:
        self.validate_update(data, session)
        obj = self.repo.update(session, id_, data)
        self.on_updated(obj, session)
        return obj

    def delete(self, session: Session, id_) -> None:
        obj = self.get(session, id_)  # asegura existencia
        self.repo.delete(session, id_)
        self.on_deleted(obj, session)
