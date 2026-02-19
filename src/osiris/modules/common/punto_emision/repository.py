# src/osiris/modules/common/punto_emision/repository.py
from __future__ import annotations
from typing import Optional
from uuid import UUID

from sqlmodel import select

from osiris.domain.repository import BaseRepository
from .entity import PuntoEmision

class PuntoEmisionRepository(BaseRepository):
    model = PuntoEmision

    def apply_filters(self, stmt, *, empresa_id: Optional[UUID] = None, sucursal_id: Optional[UUID] = None,
                      only_active: Optional[bool] = None, **kw):
        if empresa_id:
            stmt = stmt.where(PuntoEmision.empresa_id == empresa_id)
        if sucursal_id:
            stmt = stmt.where(PuntoEmision.sucursal_id == sucursal_id)
        return stmt
