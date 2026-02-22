from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from osiris.core.audit_context import get_current_user_id
from osiris.core.db import get_session
from osiris.modules.sri.facturacion_electronica.schemas import FEProcesarColaRead
from osiris.modules.sri.facturacion_electronica.services.documento_service import DocumentoElectronicoService
from osiris.modules.sri.facturacion_electronica.services.orquestador_fe_service import OrquestadorFEService
from osiris.modules.sri.facturacion_electronica.services.sri_async_service import SriAsyncService
from osiris.modules.sri.facturacion_electronica.services.venta_sri_async_service import VentaSriAsyncService


COMMON_RESPONSES = {
    400: {"description": "Solicitud inválida para estado del documento."},
    403: {"description": "Usuario sin autorización para el documento solicitado."},
    404: {"description": "Documento o recurso relacionado no encontrado."},
}

router = APIRouter()
fe_router = APIRouter(prefix="/api/v1/fe", tags=["Facturación Electrónica"])
documentos_router = APIRouter(prefix="/api/v1/documentos", tags=["Documentos Electrónicos"])
documento_service = DocumentoElectronicoService()
orquestador_fe_service = OrquestadorFEService(
    venta_sri_service=VentaSriAsyncService(),
    retencion_sri_service=SriAsyncService(),
)


@fe_router.post("/procesar-cola", response_model=FEProcesarColaRead, summary="Procesar cola SRI", responses=COMMON_RESPONSES)
def procesar_cola_fe(session: Session = Depends(get_session)):
    """Procesa documentos electrónicos pendientes en cola aplicando reglas de reintentos y contingencia."""
    procesados = orquestador_fe_service.procesar_cola(session)
    return {"procesados": procesados}


@documentos_router.get("/{documento_id}/xml", summary="Descargar XML autorizado", responses=COMMON_RESPONSES, response_class=Response)
def descargar_xml_documento(documento_id: UUID, session: Session = Depends(get_session)):
    """Devuelve el XML autorizado de un documento electrónico si ya fue aceptado por el SRI."""
    xml = documento_service.obtener_xml_autorizado(session, documento_id=documento_id, user_id=get_current_user_id())
    return Response(content=xml, media_type="application/xml")


@documentos_router.get("/{documento_id}/ride", summary="Descargar RIDE", responses=COMMON_RESPONSES, response_class=HTMLResponse)
def descargar_ride_documento(documento_id: UUID, session: Session = Depends(get_session)):
    """Genera una representación HTML del RIDE para visualización y descarga controlada."""
    html = documento_service.obtener_ride_html(session, documento_id=documento_id, user_id=get_current_user_id())
    return HTMLResponse(content=html)


router.include_router(fe_router)
router.include_router(documentos_router)
