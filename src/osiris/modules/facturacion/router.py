from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.facturacion.fe_mapper_service import FEMapperService
from osiris.modules.facturacion.compra_service import CompraService
from osiris.modules.facturacion.models import (
    CompraAnularRequest,
    CompraCreate,
    CompraRead,
    CompraRegistroCreate,
    CompraUpdate,
    GuardarPlantillaRetencionRequest,
    PlantillaRetencionRead,
    RetencionCreate,
    RetencionEmitRequest,
    RetencionRead,
    RetencionRecibidaAnularRequest,
    RetencionRecibidaCreate,
    RetencionRecibidaRead,
    RetencionSugeridaRead,
    VentaCreate,
    VentaRead,
    VentaRegistroCreate,
    VentaUpdate,
)
from osiris.modules.facturacion.retencion_service import RetencionService
from osiris.modules.facturacion.retencion_recibida_service import RetencionRecibidaService
from osiris.modules.facturacion.venta_service import VentaService

router = APIRouter()
venta_service = VentaService()
compra_service = CompraService()
fe_mapper_service = FEMapperService()
retencion_service = RetencionService()
retencion_recibida_service = RetencionRecibidaService()


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


@router.put(
    "/ventas/{venta_id}",
    response_model=VentaRead,
    tags=["Facturacion"],
)
def actualizar_venta(
    venta_id: UUID,
    payload: VentaUpdate,
    session: Session = Depends(get_session),
):
    venta = venta_service.actualizar_venta(session, venta_id, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.patch(
    "/ventas/{venta_id}",
    response_model=VentaRead,
    tags=["Facturacion"],
)
def actualizar_venta_parcial(
    venta_id: UUID,
    payload: VentaUpdate,
    session: Session = Depends(get_session),
):
    venta = venta_service.actualizar_venta(session, venta_id, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.post(
    "/compras",
    response_model=CompraRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_compra(
    payload: CompraCreate,
    session: Session = Depends(get_session),
):
    compra = compra_service.registrar_compra(session, payload)
    return compra


@router.post(
    "/compras/desde-productos",
    response_model=CompraRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_compra_desde_productos(
    payload: CompraRegistroCreate,
    session: Session = Depends(get_session),
):
    compra = compra_service.registrar_compra_desde_productos(session, payload)
    return compra


@router.put(
    "/compras/{compra_id}",
    response_model=CompraRead,
    tags=["Facturacion"],
)
def actualizar_compra(
    compra_id: UUID,
    payload: CompraUpdate,
    session: Session = Depends(get_session),
):
    return compra_service.actualizar_compra(session, compra_id, payload)


@router.post(
    "/compras/{compra_id}/anular",
    response_model=CompraRead,
    tags=["Facturacion"],
)
def anular_compra(
    compra_id: UUID,
    payload: CompraAnularRequest,
    session: Session = Depends(get_session),
):
    return compra_service.anular_compra(session, compra_id, payload)


@router.get(
    "/v1/compras/{compra_id}/sugerir-retencion",
    response_model=RetencionSugeridaRead,
    tags=["Facturacion"],
)
def sugerir_retencion_compra(
    compra_id: UUID,
    session: Session = Depends(get_session),
):
    return retencion_service.sugerir_retencion(session, compra_id)


@router.post(
    "/v1/compras/{compra_id}/guardar-plantilla-retencion",
    response_model=PlantillaRetencionRead,
    tags=["Facturacion"],
)
def guardar_plantilla_retencion_desde_compra(
    compra_id: UUID,
    payload: GuardarPlantillaRetencionRequest,
    session: Session = Depends(get_session),
):
    return retencion_service.guardar_plantilla_desde_retencion_digitada(session, compra_id, payload)


@router.post(
    "/v1/compras/{compra_id}/retenciones",
    response_model=RetencionRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_retencion_compra(
    compra_id: UUID,
    payload: RetencionCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    return retencion_service.crear_retencion(
        session,
        compra_id,
        payload,
        encolar_sri=True,
        background_tasks=background_tasks,
    )


@router.post(
    "/v1/retenciones/{retencion_id}/emitir",
    response_model=RetencionRead,
    tags=["Facturacion"],
)
def emitir_retencion(
    retencion_id: UUID,
    payload: RetencionEmitRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    return retencion_service.emitir_retencion(
        session,
        retencion_id,
        payload,
        background_tasks=background_tasks,
    )


@router.get(
    "/v1/retenciones/{retencion_id}/fe-payload",
    tags=["Facturacion"],
)
def obtener_payload_fe_retencion(
    retencion_id: UUID,
    session: Session = Depends(get_session),
):
    return retencion_service.obtener_payload_fe_retencion(session, retencion_id)


@router.post(
    "/v1/retenciones-recibidas",
    response_model=RetencionRecibidaRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def crear_retencion_recibida(
    payload: RetencionRecibidaCreate,
    session: Session = Depends(get_session),
):
    return retencion_recibida_service.crear_retencion_recibida(session, payload)


@router.post(
    "/v1/retenciones-recibidas/{retencion_id}/anular",
    response_model=RetencionRecibidaRead,
    tags=["Facturacion"],
)
def anular_retencion_recibida(
    retencion_id: UUID,
    payload: RetencionRecibidaAnularRequest,
    session: Session = Depends(get_session),
):
    return retencion_recibida_service.anular_retencion_recibida(
        session,
        retencion_id,
        motivo=payload.motivo,
        usuario_auditoria=payload.usuario_auditoria,
    )


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
