# src/osiris/modules/common/usuario/router.py
from typing import List
from fastapi import APIRouter, Depends, Path, Body, HTTPException, status
from sqlmodel import Session
from uuid import UUID

from osiris.core.db import get_session
from osiris.domain.router import register_crud_routes
from .models import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioRead,
    UsuarioResetPasswordRequest,
    UsuarioResetPasswordResponse,
    UsuarioVerifyPasswordRequest,
)
from .service import UsuarioService
from .repository import UsuarioRepository
from osiris.modules.common.rol_modulo_permiso.service import RolModuloPermisoService
from osiris.modules.common.rol_modulo_permiso.models import ModuloPermisoRead

router = APIRouter()
service = UsuarioService()
permiso_service = RolModuloPermisoService()

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


@router.get("/usuarios/{usuario_id}/permisos", response_model=List[ModuloPermisoRead], tags=["Usuarios", "Permisos"])
def obtener_permisos_usuario(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    session: Session = Depends(get_session)
):
    """
    Retorna los permisos por módulo del usuario.
    Devuelve lista de módulos con flags: puede_leer, puede_crear, puede_actualizar, puede_eliminar.
    """
    # Obtener usuario
    usuario = service.get(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Obtener permisos del rol
    permisos = permiso_service.obtener_permisos_por_rol(session, usuario.rol_id)
    return permisos


@router.get("/usuarios/{usuario_id}/menu", response_model=List[ModuloPermisoRead], tags=["Usuarios", "Permisos"])
def obtener_menu_usuario(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    session: Session = Depends(get_session)
):
    """
    Retorna el menú dinámico del usuario.
    Solo incluye módulos donde puede_leer = True.
    """
    # Obtener usuario
    usuario = service.get(session, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Obtener menú del rol
    menu = permiso_service.obtener_menu_por_rol(session, usuario.rol_id)
    return menu


@router.post(
    "/usuarios/{usuario_id}/reset-password",
    response_model=UsuarioResetPasswordResponse,
    tags=["Usuarios"],
)
def reset_password_usuario(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    payload: UsuarioResetPasswordRequest | None = Body(None),
    session: Session = Depends(get_session),
):
    updated, temp_password = service.reset_password(
        session,
        usuario_id,
        usuario_auditoria=payload.usuario_auditoria if payload else None,
    )
    return UsuarioResetPasswordResponse(
        usuario_id=updated.id,
        username=updated.username,
        password_temporal=temp_password,
        requiere_cambio_password=updated.requiere_cambio_password,
    )


@router.post("/usuarios/{usuario_id}/verify-password", response_model=bool, tags=["Usuarios"])
def verify_password_usuario(
    usuario_id: UUID = Path(..., description="ID del usuario"),
    payload: UsuarioVerifyPasswordRequest = Body(...),
    session: Session = Depends(get_session),
):
    """Devuelve True/False si la clave coincide con el hash almacenado."""
    return service.verify_password(session, usuario_id, payload.password)

