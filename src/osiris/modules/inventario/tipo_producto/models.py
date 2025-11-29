# src/osiris/modules/inventario/tipo_producto/models.py
from __future__ import annotations

from typing import Optional
from uuid import UUID

from osiris.domain.base_models import BaseOSModel

class TipoProductoCreate(BaseOSModel):
    producto_id: UUID
    atributo_id: UUID
    orden: Optional[int] = None
    obligatorio: Optional[bool] = None
    usuario_auditoria: Optional[str] = None

class TipoProductoUpdate(BaseOSModel):
    orden: Optional[int] = None
    obligatorio: Optional[bool] = None
    usuario_auditoria: Optional[str] = None

class TipoProductoRead(BaseOSModel):
    id: UUID
    producto_id: UUID
    atributo_id: UUID
    orden: Optional[int] = None
    obligatorio: Optional[bool] = None
    activo: bool
