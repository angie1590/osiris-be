from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.sri.facturacion_electronica.services.fe_mapper_service import FEMapperService
from osiris.modules.ventas.schemas import (
    CuentaPorCobrarRead,
    FEPayloadRead,
    PagoCxCCreate,
    PagoCxCRead,
    RetencionRecibidaAnularRequest,
    RetencionRecibidaCreate,
    RetencionRecibidaRead,
    VentaAnularRequest,
    VentaCreate,
    VentaEmitRequest,
    VentaRead,
    VentaRegistroCreate,
    VentaUpdate,
)
from osiris.modules.ventas.services.cxc_service import CuentaPorCobrarService
from osiris.modules.ventas.services.retencion_recibida_service import RetencionRecibidaService
from osiris.modules.ventas.services.venta_service import VentaService


COMMON_RESPONSES = {
    400: {"description": "Solicitud inválida para la regla de negocio."},
    404: {"description": "Recurso no encontrado."},
}

router = APIRouter(tags=["Ventas"])
venta_service = VentaService()
fe_mapper_service = FEMapperService()
retencion_recibida_service = RetencionRecibidaService()
cxc_service = CuentaPorCobrarService()


@router.post(
    "/ventas",
    response_model=VentaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venta",
    responses=COMMON_RESPONSES,
)
def crear_venta(payload: VentaCreate, session: Session = Depends(get_session)):
    """Crea una venta en estado borrador calculando impuestos según la configuración tributaria."""
    venta = venta_service.registrar_venta(session, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.post(
    "/ventas/desde-productos",
    response_model=VentaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar venta desde catálogo",
    responses=COMMON_RESPONSES,
)
def crear_venta_desde_productos(payload: VentaRegistroCreate, session: Session = Depends(get_session)):
    """Crea una venta usando productos existentes y replica snapshot de impuestos al detalle."""
    venta = venta_service.registrar_venta_desde_productos(session, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.put(
    "/ventas/{venta_id}",
    response_model=VentaRead,
    summary="Actualizar venta",
    responses=COMMON_RESPONSES,
)
def actualizar_venta(venta_id: UUID, payload: VentaUpdate, session: Session = Depends(get_session)):
    """Actualiza una venta en estado editable respetando reglas de inmutabilidad al emitir."""
    venta = venta_service.actualizar_venta(session, venta_id, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.patch(
    "/ventas/{venta_id}",
    response_model=VentaRead,
    summary="Actualizar venta parcialmente",
    responses=COMMON_RESPONSES,
)
def actualizar_venta_parcial(venta_id: UUID, payload: VentaUpdate, session: Session = Depends(get_session)):
    """Actualiza parcialmente una venta siempre que no esté emitida o anulada."""
    venta = venta_service.actualizar_venta(session, venta_id, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.get(
    "/ventas/{venta_id}",
    response_model=VentaRead,
    summary="Obtener venta por ID",
    responses=COMMON_RESPONSES,
)
def obtener_venta(venta_id: UUID, session: Session = Depends(get_session)):
    """Recupera el documento de venta con sus detalles e impuestos snapshot."""
    return venta_service.obtener_venta_read(session, venta_id)


@router.post(
    "/ventas/{venta_id}/emitir",
    response_model=VentaRead,
    summary="Emitir venta",
    responses=COMMON_RESPONSES,
)
def emitir_venta(venta_id: UUID, payload: VentaEmitRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    """Emite la venta validando stock, generando CxC y encolando proceso SRI cuando aplica."""
    venta = venta_service.emitir_venta(
        session,
        venta_id,
        usuario_auditoria=payload.usuario_auditoria,
        background_tasks=background_tasks,
        encolar_sri=True,
    )
    return venta_service.obtener_venta_read(session, venta.id)


@router.post(
    "/ventas/{venta_id}/anular",
    response_model=VentaRead,
    summary="Anular venta",
    responses=COMMON_RESPONSES,
)
def anular_venta(venta_id: UUID, payload: VentaAnularRequest, session: Session = Depends(get_session)):
    """Anula la venta aplicando validaciones de cobros, reglas SRI y reversos transaccionales."""
    venta = venta_service.anular_venta(
        session,
        venta_id,
        usuario_auditoria=payload.usuario_auditoria,
        confirmado_portal_sri=payload.confirmado_portal_sri,
        motivo=payload.motivo,
    )
    return venta_service.obtener_venta_read(session, venta.id)


@router.post(
    "/v1/retenciones-recibidas",
    response_model=RetencionRecibidaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar retención recibida",
    responses=COMMON_RESPONSES,
)
def crear_retencion_recibida(payload: RetencionRecibidaCreate, session: Session = Depends(get_session)):
    """Registra una retención recibida validando formato SRI y reglas IVA/Renta contra la venta."""
    return retencion_recibida_service.crear_retencion_recibida(session, payload)


@router.post(
    "/v1/retenciones-recibidas/{retencion_id}/anular",
    response_model=RetencionRecibidaRead,
    summary="Anular retención recibida",
    responses=COMMON_RESPONSES,
)
def anular_retencion_recibida(retencion_id: UUID, payload: RetencionRecibidaAnularRequest, session: Session = Depends(get_session)):
    """Anula una retención aplicada y revierte su impacto sobre la cuenta por cobrar."""
    return retencion_recibida_service.anular_retencion_recibida(
        session,
        retencion_id,
        motivo=payload.motivo,
        usuario_auditoria=payload.usuario_auditoria,
    )


@router.post(
    "/v1/retenciones-recibidas/{retencion_id}/aplicar",
    response_model=RetencionRecibidaRead,
    summary="Aplicar retención recibida",
    responses=COMMON_RESPONSES,
)
def aplicar_retencion_recibida(retencion_id: UUID, session: Session = Depends(get_session)):
    """Aplica la retención recibida a la CxC con bloqueo pesimista para evitar carreras."""
    return retencion_recibida_service.aplicar_retencion_recibida(session, retencion_id)


@router.get(
    "/v1/cxc/{venta_id}",
    response_model=CuentaPorCobrarRead,
    summary="Obtener cuenta por cobrar de venta",
    responses=COMMON_RESPONSES,
)
def obtener_cxc_por_venta(venta_id: UUID, session: Session = Depends(get_session)):
    """Consulta el estado administrativo de cobro asociado a una venta."""
    return cxc_service.obtener_cxc_por_venta(session, venta_id)


@router.post(
    "/v1/cxc/{venta_id}/pagos",
    response_model=PagoCxCRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago de CxC",
    responses=COMMON_RESPONSES,
)
def registrar_pago_cxc(venta_id: UUID, payload: PagoCxCCreate, session: Session = Depends(get_session)):
    """Registra un pago en CxC validando sobrepago y recalculando saldo/estado en la misma transacción."""
    cxc = cxc_service.obtener_cxc_por_venta(session, venta_id)
    return cxc_service.registrar_pago_cxc(session, cxc.id, payload)


@router.get(
    "/ventas/{venta_id}/fe-payload",
    response_model=FEPayloadRead,
    summary="Obtener payload FE-EC de venta",
    responses=COMMON_RESPONSES,
)
def obtener_payload_fe_venta(venta_id: UUID, session: Session = Depends(get_session)):
    """Genera el payload FE-EC de la venta para firma y transmisión electrónica."""
    venta = venta_service.obtener_venta_read(session, venta_id)
    return fe_mapper_service.venta_to_fe_payload(venta)
