from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.osiris.db.database import get_session
from src.osiris.services.proveedor_sociedad_service import ProveedorSociedadServicio
from src.osiris.models.proveedor_sociedad_model import (
    ProveedorSociedadCrear,
    ProveedorSociedadInput,
    ProveedorSociedadActualizar,
    ProveedorSociedadRespuesta
)

router = APIRouter(prefix="/proveedores-sociedad", tags=["Proveedores Sociedad"])


@router.post("/", response_model=ProveedorSociedadRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_proveedor_sociedad(
    data: ProveedorSociedadInput,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await ProveedorSociedadServicio.crear(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ProveedorSociedadRespuesta])
async def listar_proveedores_sociedad(db: AsyncSession = Depends(get_session)):
    return await ProveedorSociedadServicio.listar(db)


@router.put("/{proveedor_id}", response_model=ProveedorSociedadRespuesta)
async def actualizar_proveedor_sociedad(
    proveedor_id: UUID,
    data: ProveedorSociedadActualizar,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await ProveedorSociedadServicio.actualizar(db, proveedor_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{proveedor_id}")
async def eliminar_proveedor_sociedad(
    proveedor_id: UUID,
    usuario: str = Query(..., description="Usuario responsable de la eliminación"),
    db: AsyncSession = Depends(get_session),
):
    try:
        await ProveedorSociedadServicio.eliminar(db, proveedor_id, usuario)
        return {"mensaje": "Proveedor eliminado correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
