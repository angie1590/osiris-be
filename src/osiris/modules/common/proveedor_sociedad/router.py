from fastapi import APIRouter
from osiris.domain.router import register_crud_routes

from .models import (
    ProveedorSociedadRead,
    ProveedorSociedadCreate,
    ProveedorSociedadUpdate,
)
from .service import ProveedorSociedadService

router = APIRouter()
service = ProveedorSociedadService()

register_crud_routes(
    router=router,
    prefix="proveedores-sociedad",
    tags=["Proveedor Sociedad"],
    model_read=ProveedorSociedadRead,
    model_create=ProveedorSociedadCreate,
    model_update=ProveedorSociedadUpdate,
    service=service,
)
