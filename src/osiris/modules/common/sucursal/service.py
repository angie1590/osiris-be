from __future__ import annotations

from typing import Optional, Tuple, List
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import Session, select

from src.osiris.domain.service import BaseService
from .repository import SucursalRepository
from .entity import Sucursal
from src.osiris.modules.common.empresa.entity import Empresa


class SucursalService(BaseService):
    fk_models = {"empresa_id": Empresa}
    repo = SucursalRepository()

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
