# src/osiris/modules/inventario/casa_comercial/router.py

from fastapi import APIRouter
from src.osiris.domain.router import register_crud_routes
from .models import CasaComercialCreate, CasaComercialUpdate, CasaComercialRead
from .service import CasaComercialService

router = APIRouter()
service = CasaComercialService()

register_crud_routes(
    router=router,
    prefix="casas-comerciales",
    tags=["Casas Comerciales"],
    model_read=CasaComercialRead,
    model_create=CasaComercialCreate,
    model_update=CasaComercialUpdate,
    service=service,
)
