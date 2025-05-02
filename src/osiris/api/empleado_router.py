from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from src.osiris.db.database import get_session
from src.osiris.services.empleado_service import EmpleadoServicio
from src.osiris.models.empleado_model import EmpleadoCrear, EmpleadoActualizar, EmpleadoRespuesta

router = APIRouter(prefix="/empleados", tags=["Empleados"])


@router.post("/", response_model=EmpleadoRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_empleado(
    data: EmpleadoCrear,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await EmpleadoServicio.crear(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[EmpleadoRespuesta])
async def listar_empleados(db: AsyncSession = Depends(get_session)):
    return await EmpleadoServicio.listar(db)


@router.put("/{empleado_id}", response_model=EmpleadoRespuesta)
async def actualizar_empleado(
    empleado_id: UUID,
    data: EmpleadoActualizar,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await EmpleadoServicio.actualizar(db, empleado_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{empleado_id}")
async def eliminar_empleado(
    empleado_id: UUID,
    usuario: str = Query(..., description="Usuario responsable de la eliminación"),
    db: AsyncSession = Depends(get_session),
):
    try:
        await EmpleadoServicio.eliminar(db, empleado_id, usuario)
        return {"mensaje": "Empleado eliminado correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
