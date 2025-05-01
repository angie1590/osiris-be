# src/osiris/api/punto_emision_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.osiris.db.database import get_session
from src.osiris.services.punto_emision_service import PuntoEmisionServicio
from src.osiris.models.punto_emision_model import (
    PuntoEmisionCrear,
    PuntoEmisionActualizar,
    PuntoEmisionRespuesta
)

router = APIRouter(prefix="/puntos-emision", tags=["Puntos de Emisión"])

@router.post("/", response_model=PuntoEmisionRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_punto_emision(entrada: PuntoEmisionCrear, db: AsyncSession = Depends(get_session)):
    return await PuntoEmisionServicio.crear(db, entrada)

@router.get("/", response_model=list[PuntoEmisionRespuesta])
async def listar_puntos_emision(incluir_inactivos: bool = False, db: AsyncSession = Depends(get_session)):
    return await PuntoEmisionServicio.listar(db, incluir_inactivos)

@router.patch("/{id}", response_model=PuntoEmisionRespuesta)
async def actualizar_punto_emision(id: UUID, datos: PuntoEmisionActualizar, db: AsyncSession = Depends(get_session)):
    actualizado = await PuntoEmisionServicio.actualizar(db, id, datos)
    if not actualizado:
        raise HTTPException(status_code=404, detail="Punto de emisión no encontrado")
    return actualizado

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_logico_punto_emision(id: UUID, db: AsyncSession = Depends(get_session)):
    await PuntoEmisionServicio.eliminar_logico(db, id)

