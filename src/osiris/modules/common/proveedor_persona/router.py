from __future__ import annotations

from fastapi import APIRouter
from src.osiris.domain.router import register_crud_routes

from .service import ProveedorPersonaService
from .models import ProveedorPersonaCreate, ProveedorPersonaUpdate, ProveedorPersonaRead

router = APIRouter()
service = ProveedorPersonaService()

register_crud_routes(
    router=router,
    prefix="proveedores-persona",  # → /api/proveedores-persona
    tags=["Proveedor Persona"],
    model_read=ProveedorPersonaRead,
    model_create=ProveedorPersonaCreate,
    model_update=ProveedorPersonaUpdate,
    service=service,
)
