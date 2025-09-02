from __future__ import annotations

from typing import Optional
from uuid import UUID
from fastapi import HTTPException
from sqlmodel import Session, select

from src.osiris.domain.service import BaseService
from .repository import PuntoEmisionRepository
from .entity import PuntoEmision
from src.osiris.modules.common.empresa.entity import Empresa
from src.osiris.modules.common.sucursal.entity import Sucursal


class PuntoEmisionService(BaseService):
    repo = PuntoEmisionRepository()

    # ---------- overrides para validar FKs ----------
    def _assert_fks(self, session: Session, empresa_id: UUID, sucursal_id: Optional[UUID]):
        if not session.exec(select(Empresa).where(Empresa.id == empresa_id)).first():
            raise HTTPException(status_code=404, detail=f"Empresa {empresa_id} not found")
        if sucursal_id:
            if not session.exec(select(Sucursal).where(Sucursal.id == sucursal_id)).first():
                raise HTTPException(status_code=404, detail=f"Sucursal {sucursal_id} not found")

    def create(self, session: Session, data):
        # data puede venir como dict o DTO
        empresa_id = data["empresa_id"] if isinstance(data, dict) else data.empresa_id
        sucursal_id = data.get("sucursal_id") if isinstance(data, dict) else getattr(data, "sucursal_id", None)
        self._assert_fks(session, empresa_id, sucursal_id)
        return super().create(session, data)

    def update(self, session: Session, item_id: UUID, data):
        empresa_id = None
        sucursal_id = None
        if isinstance(data, dict):
            empresa_id = data.get("empresa_id")
            sucursal_id = data.get("sucursal_id")
        else:
            empresa_id = getattr(data, "empresa_id", None)
            sucursal_id = getattr(data, "sucursal_id", None)

        if empresa_id or sucursal_id:
            # Necesitamos los valores actuales si alguno no vino
            current = self.get(session, item_id)
            if current is None:
                return None
            empresa_id = empresa_id or current.empresa_id
            sucursal_id = sucursal_id if sucursal_id is not None else current.sucursal_id
            self._assert_fks(session, empresa_id, sucursal_id)

        return super().update(session, item_id, data)

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
