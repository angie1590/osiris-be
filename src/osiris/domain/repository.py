from __future__ import annotations

from typing import Any, Iterable, Optional, Tuple, List
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.sql import Select
from pydantic import BaseModel


class BaseRepository:
    """
    Repositorio base genérico.
    - self.model: debe ser asignado por la subclase (SQLModel).
    - Hooks para Strategy: apply_filters / apply_order
    """

    model = None  # Sobrescribir en subclases

    # --------- Hooks (Strategy) ----------
    def apply_filters(
        self,
        stmt: Select,
        *,
        only_active: Optional[bool] = None,
        **filters: Any,
    ) -> Select:
        """
        Punto de extensión para filtros.
        - Por defecto, si el modelo tiene 'activo' y llega only_active, filtra por ello.
        - Puedes extender en subclases o inyectar Strategy para filtros complejos.
        """
        if only_active is not None and hasattr(self.model, "activo"):
            stmt = stmt.where(self.model.activo == only_active)
        # Ejemplo de filtros adicionales (si los pasas via **filters):
        # for field, value in filters.items():
        #     if hasattr(self.model, field) and value is not None:
        #         stmt = stmt.where(getattr(self.model, field) == value)
        return stmt

    def apply_order(self, stmt: Select, *, order_by: Optional[Iterable] = None) -> Select:
        """
        Punto de extensión para ordenamiento.
        - order_by puede ser una lista de columnas del modelo, e.g. [self.model.id.desc()]
        """
        if order_by:
            stmt = stmt.order_by(*order_by)
        return stmt

    # --------- API pública ----------
    def list(
        self,
        session: Session,
        *,
        only_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: Optional[Iterable] = None,
        **filters: Any,
    ) -> Tuple[List[Any], int]:
        """
        Retorna (items, total) aplicando filtros y paginación.
        - total es el conteo de registros que cumplen los filtros (independiente de limit/offset).
        """
        if self.model is None:
            raise ValueError("BaseRepository.model no está definido en la subclase.")

        # SELECT base
        base_stmt = select(self.model)

        # Filtros (Strategy/hook)
        filtered_stmt = self.apply_filters(
            base_stmt, only_active=only_active, **filters
        )

        # Orden (Strategy/hook)
        ordered_stmt = self.apply_order(filtered_stmt, order_by=order_by)

        # ---- TOTAL (seguro) ----
        # Contamos sobre un subquery que ya incluye todos los filtros (y joins si los hubiere)
        count_stmt = select(func.count()).select_from(ordered_stmt.subquery())
        total: int = session.exec(count_stmt).one()

        # ---- ITEMS (paginados) ----
        items = session.exec(
            ordered_stmt.offset(offset).limit(limit)
        ).all()

        return items, total

    def get(self, session: Session, item_id: Any) -> Any:
        return session.get(self.model, item_id)

    def create(self, session: Session, obj: Any) -> Any:
        # Acepta dict o Pydantic y lo convierte al modelo SQLModel
        if isinstance(obj, BaseModel):
            data = obj.model_dump(exclude_unset=True)
        elif isinstance(obj, dict):
            data = obj
        else:
            data = None

        if data is not None:
            obj = self.model(**data)  # instancia del modelo

        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def update(self, session: Session, db_obj: Any, data: dict) -> Any:
        """
        Actualiza un objeto existente.
        - `db_obj` debe ser una instancia ya cargada del modelo (ej: session.get()).
        - `data` puede ser un dict o un Pydantic model.
        """
        # Normalizar data a dict
        if isinstance(data, BaseModel):
            data = data.model_dump(exclude_unset=True)
        elif not isinstance(data, dict):
            raise ValueError("update() solo acepta dict o BaseModel como data")

        # Asignar campos
        for field, value in data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        return db_obj

    def delete(self, session: Session, db_obj: Any) -> bool:
        # Si el modelo tiene campo 'activo', hacemos borrado lógico
        if hasattr(db_obj, "activo"):
            setattr(db_obj, "activo", False)
            session.add(db_obj)
        else:
            # fallback: borrado físico
            session.delete(db_obj)

        session.commit()
        return True
