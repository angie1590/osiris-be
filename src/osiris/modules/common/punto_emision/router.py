from uuid import UUID

from fastapi import APIRouter, Body, Depends, Path
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.domain.router import register_crud_routes
from .entity import TipoDocumentoSRI
from .models import (
    AjusteManualSecuencialRequest,
    PuntoEmisionCreate,
    PuntoEmisionRead,
    PuntoEmisionSecuencialRead,
    PuntoEmisionUpdate,
)
from .service import PuntoEmisionService

router = APIRouter()
service = PuntoEmisionService()

register_crud_routes(
    router=router,
    prefix="puntos-emision",
    tags=["Puntos de Emisión"],
    model_read=PuntoEmisionRead,
    model_create=PuntoEmisionCreate,
    model_update=PuntoEmisionUpdate,
    service=service,
)


@router.post(
    "/puntos-emision/{punto_emision_id}/secuenciales/{tipo_documento}/ajuste-manual",
    response_model=PuntoEmisionSecuencialRead,
    tags=["Puntos de Emisión"],
)
def ajustar_secuencial_manual(
    punto_emision_id: UUID = Path(..., description="ID del punto de emisión"),
    tipo_documento: TipoDocumentoSRI = Path(..., description="Tipo de documento SRI"),
    payload: AjusteManualSecuencialRequest = Body(...),
    session: Session = Depends(get_session),
):
    return service.ajustar_secuencial_manual(
        session,
        punto_emision_id=punto_emision_id,
        tipo_documento=tipo_documento,
        nuevo_secuencial=payload.nuevo_secuencial,
        usuario_id=payload.usuario_id,
        justificacion=payload.justificacion,
    )
