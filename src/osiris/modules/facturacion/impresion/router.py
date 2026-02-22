from __future__ import annotations

from uuid import UUID

from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from osiris.core.audit_context import get_current_user_id
from osiris.core.db import get_session
from osiris.modules.facturacion.impresion.schemas import ReimpresionRequest
from osiris.modules.facturacion.impresion.services.impresion_service import ImpresionService


router = APIRouter()
impresion_service = ImpresionService()


@router.get("/v1/impresion/documento/{documento_id}/a4", tags=["Facturacion"])
def generar_ride_a4(documento_id: UUID, session: Session = Depends(get_session)):
    pdf_bytes = impresion_service.generar_ride_a4(session, documento_id=documento_id)
    headers = {
        "Content-Disposition": f'inline; filename="ride-{documento_id}.pdf"',
    }
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/v1/impresion/documento/{documento_id}/ticket", tags=["Facturacion"])
def generar_ticket_termico(
    documento_id: UUID,
    ancho: Literal["58mm", "80mm"] = Query(default="80mm"),
    session: Session = Depends(get_session),
):
    html = impresion_service.generar_ticket_termico_html(
        session,
        documento_id=documento_id,
        ancho=ancho,
    )
    return HTMLResponse(content=html)


@router.post("/v1/impresion/documento/{documento_id}/reimprimir", tags=["Facturacion"])
def reimprimir_documento(
    documento_id: UUID,
    payload: ReimpresionRequest,
    session: Session = Depends(get_session),
):
    resultado = impresion_service.reimprimir_documento(
        session,
        documento_id=documento_id,
        motivo=payload.motivo,
        formato=payload.formato,
        user_id=get_current_user_id(),
    )
    headers = {"Content-Disposition": f'inline; filename="{resultado["filename"]}"'}
    if resultado["media_type"] == "application/pdf":
        return Response(content=resultado["content"], media_type="application/pdf", headers=headers)
    return HTMLResponse(content=resultado["content"], headers=headers)
