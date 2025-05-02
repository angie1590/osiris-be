from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.osiris.db.database import get_session
from src.osiris.services.rol_service import RolServicio
from src.osiris.models.rol_model import RolCrear, RolActualizar, RolRespuesta

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.post("/", response_model=RolRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_rol(
    rol: RolCrear,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await RolServicio.crear(db, rol)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[RolRespuesta])
async def listar_roles(db: AsyncSession = Depends(get_session)):
    return await RolServicio.listar(db)


@router.put("/{rol_id}", response_model=RolRespuesta)
async def actualizar_rol(
    rol_id: UUID,
    data: RolActualizar,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await RolServicio.actualizar(db, rol_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{rol_id}")
async def eliminar_rol(
    rol_id: UUID,
    usuario: str = Query(..., description="Usuario responsable de la eliminación"),
    db: AsyncSession = Depends(get_session),
):
    try:
        await RolServicio.eliminar(db, rol_id, usuario)
        return {"mensaje": "Rol eliminado correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
