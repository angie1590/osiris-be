from fastapi import APIRouter
from src.osiris.domain.router import register_crud_routes
from .models import PuntoEmisionCreate, PuntoEmisionUpdate, PuntoEmisionRead
from .service import PuntoEmisionService

router = APIRouter()
service = PuntoEmisionService()

register_crud_routes(
    router=router,
    prefix="puntos-emision",
    tags=["Puntos de Emisión"],
    model_read=PuntoEmisionRead,
    model_create=PuntoEmisionCreate,
    model_update=PuntoEmisionUpdate,
    service=service,
)
