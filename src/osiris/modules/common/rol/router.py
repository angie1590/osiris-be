# src/modules/common/rol/router.py
from fastapi import APIRouter
from src.osiris.domain.router import register_crud_routes
from .models import RolCreate, RolUpdate, RolRead
from .repository import RolRepository
from .service import RolService

router = APIRouter()
service = RolService(repo=RolRepository())

register_crud_routes(  # pyright: ignore[reportInvalidTypeForm]
    router=router,
    prefix="roles",
    tags=["Roles"],
    model_read=RolRead,
    model_create=RolCreate,
    model_update=RolUpdate,
    service=service,
)
