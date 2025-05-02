from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.osiris.db.database import get_session
from src.osiris.services.cliente_service import ClienteServicio
from src.osiris.models.cliente_model import ClienteCrear, ClienteActualizar, ClienteRespuesta

router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=ClienteRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_cliente(
    data: ClienteCrear,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await ClienteServicio.crear(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[ClienteRespuesta])
async def listar_clientes(db: AsyncSession = Depends(get_session)):
    return await ClienteServicio.listar(db)


@router.put("/{cliente_id}", response_model=ClienteRespuesta)
async def actualizar_cliente(
    cliente_id: UUID,
    data: ClienteActualizar,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await ClienteServicio.actualizar(db, cliente_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{cliente_id}")
async def eliminar_cliente(
    cliente_id: UUID,
    usuario: str = Query(..., description="Usuario responsable de la eliminación"),
    db: AsyncSession = Depends(get_session),
):
    try:
        await ClienteServicio.eliminar(db, cliente_id, usuario)
        return {"mensaje": "Cliente eliminado correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
