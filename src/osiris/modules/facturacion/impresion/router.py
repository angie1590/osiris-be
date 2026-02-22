from __future__ import annotations

from uuid import UUID

from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from osiris.core.db import get_session
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
