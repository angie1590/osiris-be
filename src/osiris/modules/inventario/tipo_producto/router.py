# src/osiris/modules/inventario/tipo_producto/router.py
from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import TipoProductoCreate, TipoProductoUpdate, TipoProductoRead
from .service import TipoProductoService

router = APIRouter()
service = TipoProductoService()

register_crud_routes(
    router=router,
    prefix="tipos-producto",
    tags=["TiposProducto"],
    model_read=TipoProductoRead,
    model_create=TipoProductoCreate,
    model_update=TipoProductoUpdate,
    service=service,
)
