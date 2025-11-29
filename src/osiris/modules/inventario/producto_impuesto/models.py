from __future__ import annotations

from typing import Optional
from uuid import UUID

from osiris.domain.base_models import BaseOSModel
from osiris.modules.aux.impuesto_catalogo.models import ImpuestoCatalogoRead


class ProductoImpuestoCreate(BaseOSModel):
    producto_id: UUID
    impuesto_catalogo_id: UUID
    usuario_auditoria: Optional[str] = None


class ProductoImpuestoRead(BaseOSModel):
    id: UUID
    producto_id: UUID
    impuesto_catalogo_id: UUID
    activo: bool
    impuesto: Optional[ImpuestoCatalogoRead] = None  # Datos completos del impuesto
