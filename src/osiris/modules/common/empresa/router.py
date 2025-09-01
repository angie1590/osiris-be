# src/osiris/modules/common/empresa/router.py
from fastapi import APIRouter
from src.osiris.domain.router import register_crud_routes
from .models import EmpresaCreate, EmpresaUpdate, EmpresaRead
from .service import EmpresaService

router = APIRouter()
service = EmpresaService()

register_crud_routes(
    router=router,
    prefix="empresa",
    tags=["Empresa"],
    model_read=EmpresaRead,
    model_create=EmpresaCreate,   # POST y PUT usan este schema (full replace, seguro)
    model_update=EmpresaUpdate,   # solo por consistencia del helper; PATCH NO se expone
    service=service,
)
