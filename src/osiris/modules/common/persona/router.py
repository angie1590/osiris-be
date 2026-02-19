# src/osiris/modules/common/persona/router.py
from fastapi import APIRouter
from osiris.domain.router import register_crud_routes

from .models import PersonaCreate, PersonaUpdate, PersonaRead
from .service import PersonaService
from .repository import PersonaRepository

router = APIRouter()
service = PersonaService(repo=PersonaRepository())

register_crud_routes(
    router=router,
    prefix="personas",
    tags=["Personas"],
    model_read=PersonaRead,
    model_create=PersonaCreate,
    model_update=PersonaUpdate,
    service=service,
)
