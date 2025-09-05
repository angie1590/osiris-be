from fastapi import APIRouter
from src.osiris.domain.router import register_crud_routes
from .models import CargoCreate, CargoUpdate, CargoRead
from .service import CargoService

router = APIRouter()
service = CargoService()

register_crud_routes(
    router=router,
    prefix="cargos",
    tags=["Cargos"],
    model_read=CargoRead,
    model_create=CargoCreate,
    model_update=CargoUpdate,
    service=service,
)
