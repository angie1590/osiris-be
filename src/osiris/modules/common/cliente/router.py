# src/osiris/modules/common/cliente/router.py
from __future__ import annotations
from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import ClienteCreate, ClienteUpdate, ClienteRead
from .service import ClienteService

router = APIRouter()
service = ClienteService()

register_crud_routes(
    router=router,
    prefix="clientes",
    tags=["Clientes"],
    model_read=ClienteRead,
    model_create=ClienteCreate,
    model_update=ClienteUpdate,
    service=service,
)
