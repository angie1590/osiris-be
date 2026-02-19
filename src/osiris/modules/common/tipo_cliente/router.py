from fastapi import APIRouter
from osiris.domain.router import register_crud_routes

from .models import TipoClienteCreate, TipoClienteUpdate, TipoClienteRead
from .service import TipoClienteService

router = APIRouter()
service = TipoClienteService()

register_crud_routes(
    router=router,
    prefix="tipos-cliente",
    tags=["Tipos de Cliente"],
    model_read=TipoClienteRead,
    model_create=TipoClienteCreate,
    model_update=TipoClienteUpdate,
    service=service,
)
