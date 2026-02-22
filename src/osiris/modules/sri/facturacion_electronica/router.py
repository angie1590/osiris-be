from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from osiris.core.audit_context import get_current_user_id
from osiris.core.db import get_session
from osiris.modules.compras.services.retencion_service import RetencionService
from osiris.modules.sri.facturacion_electronica.services.documento_service import DocumentoElectronicoService
from osiris.modules.sri.facturacion_electronica.services.orquestador_fe_service import OrquestadorFEService
from osiris.modules.sri.facturacion_electronica.services.venta_sri_async_service import VentaSriAsyncService
from osiris.modules.sri.facturacion_electronica.services.sri_async_service import SriAsyncService


router = APIRouter()
documento_service = DocumentoElectronicoService()
orquestador_fe_service = OrquestadorFEService(
    venta_sri_service=VentaSriAsyncService(),
    retencion_sri_service=SriAsyncService(),
)
retencion_service = RetencionService()


@router.post("/v1/fe/procesar-cola", tags=["Facturacion"])
def procesar_cola_fe(session: Session = Depends(get_session)):
    procesados = orquestador_fe_service.procesar_cola(session)
    return {"procesados": procesados}


@router.get("/v1/documentos/{documento_id}/xml", tags=["Facturacion"])
def descargar_xml_documento(documento_id: UUID, session: Session = Depends(get_session)):
    xml = documento_service.obtener_xml_autorizado(session, documento_id=documento_id, user_id=get_current_user_id())
    return Response(content=xml, media_type="application/xml")


@router.get("/v1/documentos/{documento_id}/ride", tags=["Facturacion"])
def descargar_ride_documento(documento_id: UUID, session: Session = Depends(get_session)):
    html = documento_service.obtener_ride_html(session, documento_id=documento_id, user_id=get_current_user_id())
    return HTMLResponse(content=html)
