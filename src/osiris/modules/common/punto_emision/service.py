from __future__ import annotations

from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import Session, select

from osiris.domain.service import BaseService
from .repository import PuntoEmisionRepository
from .entity import PuntoEmision
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.sucursal.entity import Sucursal


class PuntoEmisionService(BaseService):
    repo = PuntoEmisionRepository()
    fk_models = {
        "empresa_id": Empresa,
        "sucursal_id": Sucursal,
    }

    # ---------- atajos ----------
    def list_by_empresa_sucursal(
        self, session: Session, *, empresa_id: UUID, sucursal_id: Optional[UUID],
        limit: int, offset: int, only_active: bool = True
    ):
        kwargs = {"empresa_id": empresa_id}
        if sucursal_id is not None:
            kwargs["sucursal_id"] = sucursal_id
        return self.list_paginated(session, limit=limit, offset=offset, only_active=only_active, **kwargs)

    def get_by_clave_natural(
        self, session: Session, *, empresa_id: UUID, codigo: str,
        sucursal_id: Optional[UUID] = None, only_active: Optional[bool] = None
    ) -> Optional[PuntoEmision]:
        stmt = select(PuntoEmision).where(
            PuntoEmision.empresa_id == empresa_id,
            PuntoEmision.codigo == codigo,
        )
        if sucursal_id is not None:
            stmt = stmt.where(PuntoEmision.sucursal_id == sucursal_id)
        if only_active is True:
            stmt = stmt.where(PuntoEmision.activo.is_(True))
        return session.exec(stmt).first()
