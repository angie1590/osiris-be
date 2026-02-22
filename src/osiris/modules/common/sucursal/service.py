from __future__ import annotations

from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from osiris.domain.service import BaseService
from .repository import SucursalRepository
from .entity import Sucursal
from osiris.modules.common.empresa.entity import Empresa


class SucursalService(BaseService):
    fk_models = {"empresa_id": Empresa}
    repo = SucursalRepository()

    def create(self, session: Session, data: dict) -> Sucursal:
        self.validate_create(data, session)
        self._check_fk_active_and_exists(session, data)

        obj = Sucursal(**data)
        session.add(obj)
        try:
            session.commit()
            session.refresh(obj)
            self.on_created(obj, session)
            return obj
        except IntegrityError as exc:
            session.rollback()
            diag = getattr(getattr(exc, "orig", None), "diag", None)
            constraint_name = getattr(diag, "constraint_name", "") or ""
            lower_error = str(exc).lower()

            if (
                constraint_name == "uq_sucursal_empresa_codigo"
                or "uq_sucursal_empresa_codigo" in lower_error
                or "unique constraint failed: tbl_sucursal.empresa_id, tbl_sucursal.codigo" in lower_error
            ):
                raise HTTPException(
                    status_code=400,
                    detail="La empresa ya posee una sucursal con ese código",
                ) from exc

            if (
                constraint_name == "ck_sucursal_matriz_codigo"
                or "ck_sucursal_matriz_codigo" in lower_error
                or "check constraint failed" in lower_error
            ):
                raise HTTPException(
                    status_code=400,
                    detail="La sucursal matriz debe tener código '001' y las demás no pueden marcarse como matriz",
                ) from exc

            raise HTTPException(status_code=400, detail="Error de integridad al crear sucursal") from exc

    # ---------- atajos que ya tenías ----------
    def list_by_empresa(
        self,
        session: Session,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        only_active: bool = True,
    ):
        return self.list_paginated(
            session,
            limit=limit,
            offset=offset,
            only_active=only_active,
            empresa_id=empresa_id,
        )

    def get_by_empresa_y_codigo(
        self,
        session: Session,
        *,
        empresa_id: UUID,
        codigo: str,
        only_active: Optional[bool] = None,
    ) -> Optional[Sucursal]:
        stmt = select(Sucursal).where(
            Sucursal.empresa_id == empresa_id,
            Sucursal.codigo == codigo,
        )
        if only_active is True:
            stmt = stmt.where(Sucursal.activo.is_(True))
        return session.exec(stmt).first()
