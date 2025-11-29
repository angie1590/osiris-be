from __future__ import annotations

from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import CategoriaCreate, CategoriaUpdate, CategoriaRead
from .service import CategoriaService

router = APIRouter()
service = CategoriaService()

register_crud_routes(
    router=router,
    prefix="categorias",
    tags=["Categoria"],
    model_read=CategoriaRead,
    model_create=CategoriaCreate,
    model_update=CategoriaUpdate,
    service=service,
)
