# src/osiris/modules/inventario/producto_bodega/models.py
from __future__ import annotations

from typing import Optional
from uuid import UUID

from osiris.domain.base_models import BaseOSModel


class ProductoBodegaCreate(BaseOSModel):
    producto_id: UUID
    bodega_id: UUID
    cantidad: int = 0


class ProductoBodegaUpdate(BaseOSModel):
    cantidad: Optional[int] = None


class ProductoBodegaRead(BaseOSModel):
    id: UUID
    producto_id: UUID
    bodega_id: UUID
    cantidad: int
