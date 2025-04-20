"""
Router de la API para la entidad Empresa, ubicado en src/osiris/api/empresa_router.py.
Define los endpoints RESTful para gestionar los datos de empresa.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from src.osiris.models.empresa_model import EmpresaCrear, EmpresaActualizar, EmpresaRespuesta
from src.osiris.db.database import get_session
from src.osiris.services.empresa_service import EmpresaServicio
from src.osiris.db.repositories.empresa_repository import RepositorioEmpresa
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/empresas", tags=["Empresas"])


def obtener_servicio_empresa(session: AsyncSession = Depends(get_session)) -> EmpresaServicio:
    repositorio = RepositorioEmpresa(session)
    return EmpresaServicio(repositorio)


@router.get("/", response_model=List[EmpresaRespuesta])
async def listar_empresas(servicio: EmpresaServicio = Depends(obtener_servicio_empresa)):
    return await servicio.listar_empresas()


@router.get("/{empresa_id}", response_model=EmpresaRespuesta)
async def obtener_empresa(empresa_id: UUID, servicio: EmpresaServicio = Depends(obtener_servicio_empresa)):
    return await servicio.obtener_por_id(empresa_id)


@router.post("/", response_model=EmpresaRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_empresa(datos: EmpresaCrear, servicio: EmpresaServicio = Depends(obtener_servicio_empresa)):
    return await servicio.crear_empresa(datos)


@router.put("/{empresa_id}", response_model=EmpresaRespuesta)
async def actualizar_empresa(empresa_id: UUID, datos: EmpresaActualizar, servicio: EmpresaServicio = Depends(obtener_servicio_empresa)):
    try:
        return await servicio.actualizar_empresa(empresa_id, datos)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{empresa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_empresa(empresa_id: UUID, servicio: EmpresaServicio = Depends(obtener_servicio_empresa)):
    await servicio.eliminar_empresa(empresa_id)
    return None