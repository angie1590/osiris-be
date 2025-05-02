from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.osiris.db.database import get_session
from src.osiris.services.tipo_cliente_service import TipoClienteServicio
from src.osiris.models.tipo_cliente_model import TipoClienteCrear, TipoClienteActualizar, TipoClienteRespuesta

router = APIRouter(prefix="/tipos-cliente", tags=["Tipos de Cliente"])

@router.post("/", response_model=TipoClienteRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_tipo_cliente(
    data: TipoClienteCrear,
    db: AsyncSession = Depends(get_session),
):
    return await TipoClienteServicio.crear(db, data)


@router.get("/", response_model=List[TipoClienteRespuesta])
async def listar_tipos_cliente(db: AsyncSession = Depends(get_session)):
    return await TipoClienteServicio.listar(db)


@router.put("/{tipo_id}", response_model=TipoClienteRespuesta)
async def actualizar_tipo_cliente(
    tipo_id: UUID,
    data: TipoClienteActualizar,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await TipoClienteServicio.actualizar(db, tipo_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
