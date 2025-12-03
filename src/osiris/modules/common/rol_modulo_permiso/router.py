# src/osiris/modules/common/rol_modulo_permiso/router.py

from fastapi import APIRouter
from osiris.domain.router import register_crud_routes
from .models import RolModuloPermisoCreate, RolModuloPermisoUpdate, RolModuloPermisoRead
from .service import RolModuloPermisoService

router = APIRouter()
service = RolModuloPermisoService()

register_crud_routes(
    router=router,
    prefix="roles-modulos-permisos",
    tags=["Permisos"],
    model_read=RolModuloPermisoRead,
    model_create=RolModuloPermisoCreate,
    model_update=RolModuloPermisoUpdate,
    service=service,
)
