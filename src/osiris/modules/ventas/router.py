from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.sri.facturacion_electronica.services.fe_mapper_service import FEMapperService
from osiris.modules.ventas.schemas import (
    CuentaPorCobrarRead,
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


router = APIRouter()
venta_service = VentaService()
fe_mapper_service = FEMapperService()
retencion_recibida_service = RetencionRecibidaService()
cxc_service = CuentaPorCobrarService()


@router.post("/ventas", response_model=VentaRead, status_code=status.HTTP_201_CREATED, tags=["Facturacion"])
def crear_venta(payload: VentaCreate, session: Session = Depends(get_session)):
    venta = venta_service.registrar_venta(session, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.post("/ventas/desde-productos", response_model=VentaRead, status_code=status.HTTP_201_CREATED, tags=["Facturacion"])
def crear_venta_desde_productos(payload: VentaRegistroCreate, session: Session = Depends(get_session)):
    venta = venta_service.registrar_venta_desde_productos(session, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.put("/ventas/{venta_id}", response_model=VentaRead, tags=["Facturacion"])
def actualizar_venta(venta_id: UUID, payload: VentaUpdate, session: Session = Depends(get_session)):
    venta = venta_service.actualizar_venta(session, venta_id, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.patch("/ventas/{venta_id}", response_model=VentaRead, tags=["Facturacion"])
def actualizar_venta_parcial(venta_id: UUID, payload: VentaUpdate, session: Session = Depends(get_session)):
    venta = venta_service.actualizar_venta(session, venta_id, payload)
    return venta_service.obtener_venta_read(session, venta.id)


@router.get("/ventas/{venta_id}", response_model=VentaRead, tags=["Facturacion"])
def obtener_venta(venta_id: UUID, session: Session = Depends(get_session)):
    return venta_service.obtener_venta_read(session, venta_id)


@router.post("/ventas/{venta_id}/emitir", response_model=VentaRead, tags=["Facturacion"])
def emitir_venta(venta_id: UUID, payload: VentaEmitRequest, background_tasks: BackgroundTasks, session: Session = Depends(get_session)):
    venta = venta_service.emitir_venta(
        session,
        venta_id,
        usuario_auditoria=payload.usuario_auditoria,
        background_tasks=background_tasks,
        encolar_sri=True,
    )
    return venta_service.obtener_venta_read(session, venta.id)


@router.post("/ventas/{venta_id}/anular", response_model=VentaRead, tags=["Facturacion"])
def anular_venta(venta_id: UUID, payload: VentaAnularRequest, session: Session = Depends(get_session)):
    venta = venta_service.anular_venta(
        session,
        venta_id,
        usuario_auditoria=payload.usuario_auditoria,
        confirmado_portal_sri=payload.confirmado_portal_sri,
        motivo=payload.motivo,
    )
    return venta_service.obtener_venta_read(session, venta.id)


@router.post("/v1/retenciones-recibidas", response_model=RetencionRecibidaRead, status_code=status.HTTP_201_CREATED, tags=["Facturacion"])
def crear_retencion_recibida(payload: RetencionRecibidaCreate, session: Session = Depends(get_session)):
    return retencion_recibida_service.crear_retencion_recibida(session, payload)


@router.post("/v1/retenciones-recibidas/{retencion_id}/anular", response_model=RetencionRecibidaRead, tags=["Facturacion"])
def anular_retencion_recibida(retencion_id: UUID, payload: RetencionRecibidaAnularRequest, session: Session = Depends(get_session)):
    return retencion_recibida_service.anular_retencion_recibida(
        session,
        retencion_id,
        motivo=payload.motivo,
        usuario_auditoria=payload.usuario_auditoria,
    )


@router.post("/v1/retenciones-recibidas/{retencion_id}/aplicar", response_model=RetencionRecibidaRead, tags=["Facturacion"])
def aplicar_retencion_recibida(retencion_id: UUID, session: Session = Depends(get_session)):
    return retencion_recibida_service.aplicar_retencion_recibida(session, retencion_id)


@router.get("/v1/cxc/{venta_id}", response_model=CuentaPorCobrarRead, tags=["Facturacion"])
def obtener_cxc_por_venta(venta_id: UUID, session: Session = Depends(get_session)):
    return cxc_service.obtener_cxc_por_venta(session, venta_id)


@router.post("/v1/cxc/{venta_id}/pagos", response_model=PagoCxCRead, status_code=status.HTTP_201_CREATED, tags=["Facturacion"])
def registrar_pago_cxc(venta_id: UUID, payload: PagoCxCCreate, session: Session = Depends(get_session)):
    cxc = cxc_service.obtener_cxc_por_venta(session, venta_id)
    return cxc_service.registrar_pago_cxc(session, cxc.id, payload)


@router.get("/ventas/{venta_id}/fe-payload", tags=["Facturacion"])
def obtener_payload_fe_venta(venta_id: UUID, session: Session = Depends(get_session)):
    venta = venta_service.obtener_venta_read(session, venta_id)
    return fe_mapper_service.venta_to_fe_payload(venta)
