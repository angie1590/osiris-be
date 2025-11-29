from __future__ import annotations

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from uuid import UUID

from osiris.core.db import get_session
from osiris.modules.aux.impuesto_catalogo.models import (
    ImpuestoCatalogoCreate,
    ImpuestoCatalogoUpdate,
    ImpuestoCatalogoRead,
)
from osiris.modules.aux.impuesto_catalogo.service import ImpuestoCatalogoService
from osiris.modules.aux.impuesto_catalogo.entity import TipoImpuesto
from osiris.domain.schemas import PaginatedResponse
from osiris.utils.pagination import build_pagination_meta

router = APIRouter()
service = ImpuestoCatalogoService()


@router.get("/catalogo", response_model=PaginatedResponse[ImpuestoCatalogoRead], tags=["Impuestos"])
def listar_catalogo_impuestos(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tipo_impuesto: Optional[TipoImpuesto] = None,
    solo_vigentes: bool = False,
    session: Session = Depends(get_session),
):
    """Lista todos los impuestos del catálogo con paginación y filtros."""
    if tipo_impuesto:
        if solo_vigentes:
            items = service.list_by_tipo(session, tipo_impuesto, solo_vigentes=True)
        else:
            items = service.list_by_tipo(session, tipo_impuesto, solo_vigentes=False)
        total = len(items)
        items = items[offset : offset + limit]
    else:
        items, total = service.list_paginated(session, limit=limit, offset=offset)

    return PaginatedResponse(
        items=[ImpuestoCatalogoRead.model_validate(item) for item in items],
        meta=build_pagination_meta(total, limit, offset),
    )


@router.get("/catalogo/activos-vigentes", response_model=List[ImpuestoCatalogoRead], tags=["Impuestos"])
def listar_impuestos_activos_vigentes(
    fecha: Optional[date] = Query(None, description="Fecha de vigencia (por defecto hoy)"),
    session: Session = Depends(get_session),
):
    """Lista todos los impuestos activos y vigentes en una fecha específica."""
    items = service.list_activos_vigentes(session, fecha)
    return [ImpuestoCatalogoRead.model_validate(item) for item in items]


@router.get("/catalogo/{impuesto_id}", response_model=ImpuestoCatalogoRead, tags=["Impuestos"])
def obtener_impuesto(
    impuesto_id: UUID,
    session: Session = Depends(get_session),
):
    """Obtiene un impuesto específico por ID."""
    impuesto = service.get(session, impuesto_id)
    return ImpuestoCatalogoRead.model_validate(impuesto)


@router.post("/catalogo", response_model=ImpuestoCatalogoRead, status_code=201, tags=["Impuestos"])
def crear_impuesto(
    payload: ImpuestoCatalogoCreate,
    session: Session = Depends(get_session),
):
    """Crea un nuevo impuesto en el catálogo."""
    impuesto = service.create(session, payload.model_dump(exclude_unset=True))
    return ImpuestoCatalogoRead.model_validate(impuesto)


@router.put("/catalogo/{impuesto_id}", response_model=ImpuestoCatalogoRead, tags=["Impuestos"])
def actualizar_impuesto(
    impuesto_id: UUID,
    payload: ImpuestoCatalogoUpdate,
    session: Session = Depends(get_session),
):
    """Actualiza un impuesto existente."""
    impuesto = service.update(session, impuesto_id, payload.model_dump(exclude_unset=True))
    return ImpuestoCatalogoRead.model_validate(impuesto)


@router.delete("/catalogo/{impuesto_id}", status_code=204, tags=["Impuestos"])
def desactivar_impuesto(
    impuesto_id: UUID,
    session: Session = Depends(get_session),
):
    """Desactiva (soft delete) un impuesto del catálogo."""
    service.delete(session, impuesto_id)
    return None
