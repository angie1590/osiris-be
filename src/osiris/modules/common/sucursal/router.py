from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import SucursalCreate, SucursalUpdate, SucursalRead
from .service import SucursalService

router = APIRouter()
service = SucursalService()

register_crud_routes(
    router=router,
    prefix="sucursales",
    tags=["Sucursales"],
    model_read=SucursalRead,
    model_create=SucursalCreate,
    model_update=SucursalUpdate,
    service=service,
)
