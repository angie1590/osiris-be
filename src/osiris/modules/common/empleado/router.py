# src/osiris/modules/common/empleado/router.py
from __future__ import annotations

from fastapi import APIRouter
from osiris.domain.router import register_crud_routes

from .models import EmpleadoCreate, EmpleadoRead, EmpleadoUpdate
from .service import EmpleadoService

router = APIRouter()
service = EmpleadoService()

register_crud_routes(
    router=router,
    prefix="empleados",
    tags=["Empleados"],
    model_read=EmpleadoRead,
    model_create=EmpleadoCreate,
    model_update=EmpleadoUpdate,
    service=service,
)
