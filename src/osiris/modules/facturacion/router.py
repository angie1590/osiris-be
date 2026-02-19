from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.facturacion.fe_mapper_service import FEMapperService
from osiris.modules.facturacion.compra_service import CompraService
from osiris.modules.facturacion.models import (
    CompraCreate,
    CompraRegistroCreate,
    VentaCreate,
    VentaRead,
    VentaRegistroCreate,
)
from osiris.modules.facturacion.venta_service import VentaService

router = APIRouter()
venta_service = VentaService()
compra_service = CompraService()
fe_mapper_service = FEMapperService()


@router.post(
    "/ventas",
    response_model=VentaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_venta(
    payload: VentaCreate,
    session: Session = Depends(get_session),
):
    venta = venta_service.registrar_venta(session, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.post(
    "/ventas/desde-productos",
    response_model=VentaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_venta_desde_productos(
    payload: VentaRegistroCreate,
    session: Session = Depends(get_session),
):
    venta = venta_service.registrar_venta_desde_productos(session, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.post(
    "/compras",
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_compra(
    payload: CompraCreate,
    session: Session = Depends(get_session),
):
    compra = compra_service.registrar_compra(session, payload)
    return {"id": compra.id}


@router.post(
    "/compras/desde-productos",
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_compra_desde_productos(
    payload: CompraRegistroCreate,
    session: Session = Depends(get_session),
):
    compra = compra_service.registrar_compra_desde_productos(session, payload)
    return {"id": compra.id}


@router.get(
    "/ventas/{venta_id}/fe-payload",
    tags=["Facturacion"],
)
def obtener_payload_fe_venta(
    venta_id: UUID,
    session: Session = Depends(get_session),
):
    venta = venta_service.obtener_venta_read(session, venta_id)
    return fe_mapper_service.venta_to_fe_payload(venta)
