from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.inventario.movimiento_inventario.models import (
    KardexResponse,
    ValoracionResponse,
)
from osiris.modules.inventario.movimiento_inventario.service import MovimientoInventarioService


router = APIRouter(prefix="/v1/inventario", tags=["Inventario"])
service = MovimientoInventarioService()


@router.get("/kardex", response_model=KardexResponse)
def obtener_kardex(
    producto_id: UUID = Query(...),
    bodega_id: UUID = Query(...),
    fecha_inicio: date | None = Query(default=None),
    fecha_fin: date | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return service.obtener_kardex(
        session,
        producto_id=producto_id,
        bodega_id=bodega_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


@router.get("/valoracion", response_model=ValoracionResponse)
def obtener_valoracion(
    session: Session = Depends(get_session),
):
    return service.obtener_valoracion(session)
