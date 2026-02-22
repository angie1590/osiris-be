from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
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

