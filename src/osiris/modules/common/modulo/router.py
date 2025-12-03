# src/osiris/modules/common/modulo/router.py

from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import ModuloCreate, ModuloUpdate, ModuloRead
from .service import ModuloService

router = APIRouter()
service = ModuloService()

register_crud_routes(
    router=router,
    prefix="modulos",
    tags=["Módulos"],
    model_read=ModuloRead,
    model_create=ModuloCreate,
    model_update=ModuloUpdate,
    service=service,
)
