# src/osiris/modules/inventario/atributo/router.py
from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import AtributoCreate, AtributoUpdate, AtributoRead
from .service import AtributoService

router = APIRouter()
service = AtributoService()

register_crud_routes(
    router=router,
    prefix="atributos",
    tags=["Atributos"],
    model_read=AtributoRead,
    model_create=AtributoCreate,
    model_update=AtributoUpdate,
    service=service,
)
