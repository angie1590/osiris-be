from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from src.osiris.db.database import get_session
from src.osiris.services.persona_service import PersonaServicio
from osiris.models.persona_model import PersonaCrear, PersonaActualizar, PersonaRespuesta

router = APIRouter(prefix="/personas", tags=["Personas"])


@router.post("/", response_model=PersonaRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_persona(
    persona: PersonaCrear,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await PersonaServicio.crear(db, persona)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[PersonaRespuesta])
async def listar_personas(db: AsyncSession = Depends(get_session)):
    return await PersonaServicio.listar(db)


@router.get("/buscar", response_model=List[PersonaRespuesta])
async def buscar_persona(
    identificacion: Optional[str] = Query(None),
    apellido: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    if identificacion:
        persona = await PersonaServicio.buscar_por_identificacion(db, identificacion)
        return [persona] if persona else []
    if apellido:
        return await PersonaServicio.buscar_por_apellido(db, apellido)
    raise HTTPException(status_code=400, detail="Debe proporcionar una identificación o un apellido para buscar.")


@router.put("/{persona_id}", response_model=PersonaRespuesta)
async def actualizar_persona(
    persona_id: UUID,
    data: PersonaActualizar,
    db: AsyncSession = Depends(get_session),
):
    try:
        return await PersonaServicio.actualizar(db, persona_id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{persona_id}")
async def eliminar_persona(
    persona_id: UUID,
    usuario: str = Query(..., description="Usuario responsable de la eliminación"),
    db: AsyncSession = Depends(get_session),
):
    try:
        await PersonaServicio.eliminar(db, persona_id, usuario)
        return {"mensaje": "Persona eliminada correctamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
