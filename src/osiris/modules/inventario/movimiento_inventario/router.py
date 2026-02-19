from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, status, Query
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.inventario.movimiento_inventario.models import (
    KardexResponse,
    MovimientoInventarioConfirmRequest,
    MovimientoInventarioCreate,
    MovimientoInventarioRead,
    ValoracionResponse,
)
from osiris.modules.inventario.movimiento_inventario.service import MovimientoInventarioService


router = APIRouter(prefix="/v1/inventario", tags=["Inventario"])
service = MovimientoInventarioService()


@router.post("/movimientos", response_model=MovimientoInventarioRead, status_code=status.HTTP_201_CREATED)
def crear_movimiento_borrador(
    payload: MovimientoInventarioCreate,
    session: Session = Depends(get_session),
):
    movimiento = service.crear_movimiento_borrador(session, payload)
    return service.obtener_movimiento_read(session, movimiento.id)


@router.post("/movimientos/{movimiento_id}/confirmar", response_model=MovimientoInventarioRead)
def confirmar_movimiento(
    movimiento_id: UUID,
    payload: MovimientoInventarioConfirmRequest,
    session: Session = Depends(get_session),
):
    movimiento = service.confirmar_movimiento(
        session,
        movimiento_id,
        motivo_ajuste=payload.motivo_ajuste,
        usuario_autorizador=payload.usuario_auditoria,
    )
    return service.obtener_movimiento_read(session, movimiento.id)


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
