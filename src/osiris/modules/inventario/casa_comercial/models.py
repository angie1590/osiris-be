# src/osiris/modules/inventario/casa_comercial/models.py
from typing import Optional
from uuid import UUID
from src.osiris.domain.base_models import BaseOSModel

# DTOs (Pydantic-only)
class CasaComercialCreate(BaseOSModel):
    nombre: str
    usuario_auditoria: Optional[str] = None

class CasaComercialUpdate(BaseOSModel):
    nombre: Optional[str] = None
    usuario_auditoria: Optional[str] = None

class CasaComercialRead(BaseOSModel):
    id: UUID
    nombre: str
    activo: bool
