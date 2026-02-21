from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from osiris.core.audit_context import get_current_user_id
from osiris.core.db import get_session
from osiris.modules.facturacion.fe_mapper_service import FEMapperService
from osiris.modules.facturacion.compra_service import CompraService
from osiris.modules.facturacion.models import (
    CuentaPorCobrarRead,
    CompraAnularRequest,
    CompraCreate,
    CompraRead,
    CompraRegistroCreate,
    CompraUpdate,
    GuardarPlantillaRetencionRequest,
    PlantillaRetencionRead,
    PagoCxCCreate,
    PagoCxCRead,
    RetencionCreate,
    RetencionEmitRequest,
    RetencionRead,
    RetencionRecibidaAnularRequest,
    RetencionRecibidaCreate,
    RetencionRecibidaRead,
    RetencionSugeridaRead,
    VentaCreate,
    VentaAnularRequest,
    VentaEmitRequest,
    VentaRead,
    VentaRegistroCreate,
    VentaUpdate,
)
from osiris.modules.facturacion.cxc_service import CuentaPorCobrarService
from osiris.modules.facturacion.retencion_service import RetencionService
from osiris.modules.facturacion.retencion_recibida_service import RetencionRecibidaService
from osiris.modules.facturacion.venta_service import VentaService
from osiris.modules.facturacion.documento_service import DocumentoElectronicoService
from osiris.modules.facturacion.orquestador_fe_service import OrquestadorFEService

router = APIRouter()
venta_service = VentaService()
compra_service = CompraService()
fe_mapper_service = FEMapperService()
retencion_service = RetencionService()
retencion_recibida_service = RetencionRecibidaService()
cxc_service = CuentaPorCobrarService()
documento_service = DocumentoElectronicoService()
orquestador_fe_service = OrquestadorFEService(
    venta_sri_service=venta_service.venta_sri_async_service,
    retencion_sri_service=retencion_service.sri_async_service,
)


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


@router.get(
    "/ventas/{venta_id}",
    response_model=VentaRead,
    tags=["Facturacion"],
)
def obtener_venta(
    venta_id: UUID,
    session: Session = Depends(get_session),
):
    return venta_service.obtener_venta_read(session, venta_id)


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
    "/ventas/{venta_id}/emitir",
    response_model=VentaRead,
    tags=["Facturacion"],
)
def emitir_venta(
    venta_id: UUID,
    payload: VentaEmitRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
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
    tags=["Facturacion"],
)
def anular_venta(
    venta_id: UUID,
    payload: VentaAnularRequest,
    session: Session = Depends(get_session),
):
    venta = venta_service.anular_venta(
        session,
        venta_id,
        usuario_auditoria=payload.usuario_auditoria,
        confirmado_portal_sri=payload.confirmado_portal_sri,
        motivo=payload.motivo,
    )
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


@router.post(
    "/v1/retenciones-recibidas/{retencion_id}/aplicar",
    response_model=RetencionRecibidaRead,
    tags=["Facturacion"],
)
def aplicar_retencion_recibida(
    retencion_id: UUID,
    session: Session = Depends(get_session),
):
    return retencion_recibida_service.aplicar_retencion_recibida(session, retencion_id)


@router.get(
    "/v1/cxc/{venta_id}",
    response_model=CuentaPorCobrarRead,
    tags=["Facturacion"],
)
def obtener_cxc_por_venta(
    venta_id: UUID,
    session: Session = Depends(get_session),
):
    return cxc_service.obtener_cxc_por_venta(session, venta_id)


@router.post(
    "/v1/cxc/{venta_id}/pagos",
    response_model=PagoCxCRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Facturacion"],
)
def registrar_pago_cxc(
    venta_id: UUID,
    payload: PagoCxCCreate,
    session: Session = Depends(get_session),
):
    cxc = cxc_service.obtener_cxc_por_venta(session, venta_id)
    return cxc_service.registrar_pago_cxc(session, cxc.id, payload)


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


@router.post(
    "/v1/fe/procesar-cola",
    tags=["Facturacion"],
)
def procesar_cola_fe(
    session: Session = Depends(get_session),
):
    procesados = orquestador_fe_service.procesar_cola(session)
    return {"procesados": procesados}


@router.get(
    "/v1/documentos/{documento_id}/xml",
    tags=["Facturacion"],
)
def descargar_xml_documento(
    documento_id: UUID,
    session: Session = Depends(get_session),
):
    xml = documento_service.obtener_xml_autorizado(
        session,
        documento_id=documento_id,
        user_id=get_current_user_id(),
    )
    return Response(content=xml, media_type="application/xml")


@router.get(
    "/v1/documentos/{documento_id}/ride",
    tags=["Facturacion"],
)
def descargar_ride_documento(
    documento_id: UUID,
    session: Session = Depends(get_session),
):
    html = documento_service.obtener_ride_html(
        session,
        documento_id=documento_id,
        user_id=get_current_user_id(),
    )
    return HTMLResponse(content=html)
