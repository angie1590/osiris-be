# src/osiris/modules/common/usuario/router.py
from fastapi import APIRouter, Depends, Path, Body, HTTPException, status
from sqlmodel import Session
from uuid import UUID

from src.osiris.core.db import get_session
from src.osiris.domain.router import register_crud_routes
from .models import UsuarioCreate, UsuarioUpdate, UsuarioRead
from .service import UsuarioService
from .repository import UsuarioRepository

router = APIRouter()
service = UsuarioService()

# Genera las rutas CRUD genéricas (excepto PUT)
register_crud_routes(
    router=router,
    prefix="usuarios",
    tags=["Usuarios"],
    model_read=UsuarioRead,
    model_create=UsuarioCreate,
    model_update=UsuarioUpdate,   # 👈 se ignora el update genérico
    service=service,
)

