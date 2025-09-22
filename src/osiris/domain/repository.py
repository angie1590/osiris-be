from __future__ import annotations

from typing import Any, Iterable, Optional, Tuple, List
from sqlmodel import Session, select
from sqlalchemy import func
from sqlalchemy.sql import Select
from pydantic import BaseModel

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


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

    # ------------------------------
    # 🆕 Handler genérico de integridad
    # ------------------------------
    def _raise_integrity(self, e: IntegrityError) -> None:
        """
        Traduce errores de integridad (PostgreSQL) a HTTPException con mensaje claro.
        - 23505: unique violation
        - 23503: foreign key violation
        """
        orig = getattr(e, "orig", None)
        pgcode: Optional[str] = getattr(orig, "pgcode", None)  # '23505', '23503', etc.
        diag = getattr(orig, "diag", None)
        constraint = getattr(diag, "constraint_name", None)
        column = getattr(diag, "column_name", None)
        table = getattr(diag, "table_name", None)
        CONSTRAINT_MESSAGES = {
            # ejemplo: índice único de persona en cliente
            "ix_tbl_cliente_persona_id": "La persona ya está registrada como cliente (persona_id duplicado).",
            # añade otras restricciones si quieres mensajes custom
            "uq_codigo_por_entidad": "El código ya existe para esa entidad.",
            "ix_tbl_persona_identificacion": "La identificación ya existe.",
        }

        if pgcode == "23505":  # unique violation
            if constraint and constraint in CONSTRAINT_MESSAGES:
                detail = CONSTRAINT_MESSAGES[constraint]
            else:
                # Mensaje genérico, intentando aportar algo de contexto
                if column:
                    detail = f"Registro duplicado: el valor de '{column}' ya existe."
                elif constraint:
                    detail = f"Registro duplicado: se violó la restricción única '{constraint}'."
                else:
                    detail = "Registro duplicado (violación de restricción única)."
            raise HTTPException(status_code=409, detail=detail) from e

        if pgcode == "23503":  # foreign key violation
            if constraint and table:
                detail = (
                    f"Violación de llave foránea '{constraint}' en tabla '{table}'. "
                    "Verifica que las referencias existan y estén activas."
                )
            else:
                detail = "Violación de llave foránea. Verifica que las claves referenciadas existan y estén activas."
            raise HTTPException(status_code=409, detail=detail) from e

        # Fallback: cualquier otro error de integridad
        tech = str(orig) if orig else str(e)
        raise HTTPException(status_code=409, detail=f"Violación de integridad: {tech}") from e

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
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self._raise_integrity(e)
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
        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self._raise_integrity(e)
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

        try:
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self._raise_integrity(e)
        return True
