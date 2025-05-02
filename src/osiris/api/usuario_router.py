from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.osiris.db.database import get_async_session
from src.osiris.services.usuario_service import UsuarioServicio
from src.osiris.models.usuario_model import UsuarioCrear, UsuarioActualizar, UsuarioRespuesta

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.post("/", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    data: UsuarioCrear,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        return await UsuarioServicio.crear(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{usuario_id}", response_model=UsuarioRespuesta)
async def actualizar_usuario(
    usuario_id: UUID,
    data: UsuarioActualizar,
    db: AsyncSession = Depends(get_async_session),
):
    try:
        return await UsuarioServicio.actualizar(db, usuario_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{usuario_id}")
async def eliminar_usuario(
    usuario_id: UUID,
    usuario: str = Query(..., description="Usuario responsable de la eliminación"),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        await UsuarioServicio.eliminar(db, usuario_id, usuario)
        return {"mensaje": "Usuario eliminado correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
