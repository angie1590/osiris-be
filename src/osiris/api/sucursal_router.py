# src/osiris/api/sucursal_router.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.osiris.db.database import get_session
from src.osiris.services.sucursal_service import SucursalServicio
from src.osiris.models.sucursal_model import SucursalCrear, SucursalActualizar, SucursalRespuesta

router = APIRouter(prefix="/sucursales", tags=["Sucursales"])

@router.post("/", response_model=SucursalRespuesta)
async def crear_sucursal(entrada: SucursalCrear, db: AsyncSession = Depends(get_session)):
    return await SucursalServicio.crear(db, entrada)

@router.get("/", response_model=list[SucursalRespuesta])
async def listar_sucursales(incluir_inactivos: bool = True, db: AsyncSession = Depends(get_session)):
    return await SucursalServicio.listar(db, incluir_inactivos)

@router.patch("/{id}", response_model=SucursalRespuesta)
async def actualizar_sucursal(id: UUID, datos: SucursalActualizar, db: AsyncSession = Depends(get_session)):
    suc = await SucursalServicio.actualizar(db, id, datos)
    if not suc:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return suc

@router.delete("/{id}", response_model=SucursalRespuesta)
async def eliminar_sucursal(id: UUID, db: AsyncSession = Depends(get_session)):
    suc = await SucursalServicio.eliminar_logico(db, id)
    if not suc:
        raise HTTPException(status_code=404, detail="Sucursal no encontrada")
    return suc
