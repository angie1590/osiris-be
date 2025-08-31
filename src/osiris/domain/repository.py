# src/domain/repository.py
from typing import Generic, Type, TypeVar, Optional, Dict, Any, List, Tuple
from sqlmodel import SQLModel, Session, select
from .strategies import DefaultCreate, DefaultUpdate, DefaultDelete, CreateStrategy, UpdateStrategy, DeleteStrategy
from src.osiris.core.errors import NotFoundError, InactiveRecordError

ModelT = TypeVar("ModelT", bound=SQLModel)

class BaseRepository(Generic[ModelT]):
    model: Type[ModelT]

    def __init__(
        self,
        create_strategy: CreateStrategy = DefaultCreate(),
        update_strategy: UpdateStrategy = DefaultUpdate(),
        delete_strategy: DeleteStrategy = DefaultDelete(),
    ):
        self.create_strategy = create_strategy
        self.update_strategy = update_strategy
        self.delete_strategy = delete_strategy

    def create(self, session: Session, data: Dict[str, Any]) -> ModelT:
        data = self.create_strategy.before_create(data, session)
        obj = self.model(**data)
        session.add(obj); session.commit(); session.refresh(obj)
        obj = self.create_strategy.after_create(obj, session)
        return obj

    def get(self, session: Session, id_) -> Optional[ModelT]:
        return session.get(self.model, id_)

    def list(self, session: Session, *, only_active: bool = True, limit=50, offset=0) -> Tuple[List[ModelT], int]:
        stmt = select(self.model)
        if hasattr(self.model, "activo") and only_active:
            stmt = stmt.where(self.model.activo == True)  # noqa
        total = session.exec(select(self.model).count()).one()
        rows = session.exec(stmt.offset(offset).limit(limit)).all()
        return rows, total

    def update(self, session: Session, id_, data: Dict[str, Any]) -> ModelT:
        data = self.update_strategy.before_update(data, session)
        obj = session.get(self.model, id_)
        if not obj:
            raise NotFoundError(f"{self.model.__name__} {id_} not found")
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        if hasattr(obj, "activo") and getattr(obj, "activo") is False:
            raise InactiveRecordError(f"{self.model.__name__} inactive")
        session.add(obj); session.commit(); session.refresh(obj)
        obj = self.update_strategy.after_update(obj, session)
        return obj

    def delete(self, session: Session, id_) -> None:
        obj = session.get(self.model, id_)
        if not obj:
            raise NotFoundError(f"{self.model.__name__} {id_} not found")
        self.delete_strategy.before_delete(obj, session)
        if hasattr(obj, "activo"):
            setattr(obj, "activo", False)
            session.add(obj)
        else:
            session.delete(obj)
        session.commit()
        self.delete_strategy.after_delete(obj, session)
