from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.compras.schemas import (
    CompraAnularRequest,
    CompraCreate,
    CompraRead,
    CompraRegistroCreate,
    CompraUpdate,
    GuardarPlantillaRetencionRequest,
    PlantillaRetencionRead,
    RetencionCreate,
    RetencionEmitRequest,
    RetencionFEPayloadRead,
    RetencionRead,
    RetencionSugeridaRead,
)
from osiris.modules.compras.services.compra_service import CompraService
from osiris.modules.compras.services.retencion_service import RetencionService


COMMON_RESPONSES = {
    400: {"description": "Solicitud inválida para la regla de negocio."},
    404: {"description": "Recurso no encontrado."},
}

router = APIRouter(tags=["Compras"])
compra_service = CompraService()
retencion_service = RetencionService()


@router.post(
    "/compras",
    response_model=CompraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar compra",
    responses=COMMON_RESPONSES,
)
def crear_compra(payload: CompraCreate, session: Session = Depends(get_session)):
    """Registra una factura de proveedor con cálculo tributario y estado inicial borrador/registrada."""
    return compra_service.registrar_compra(session, payload)


@router.post(
    "/compras/desde-productos",
    response_model=CompraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar compra desde catálogo",
    responses=COMMON_RESPONSES,
)
def crear_compra_desde_productos(payload: CompraRegistroCreate, session: Session = Depends(get_session)):
    """Registra una compra usando productos existentes y snapshot tributario de impuestos."""
    return compra_service.registrar_compra_desde_productos(session, payload)


@router.put(
    "/compras/{compra_id}",
    response_model=CompraRead,
    summary="Actualizar compra",
    responses=COMMON_RESPONSES,
)
def actualizar_compra(compra_id: UUID, payload: CompraUpdate, session: Session = Depends(get_session)):
    """Actualiza una compra siempre que su estado permita edición según política de inmutabilidad."""
    return compra_service.actualizar_compra(session, compra_id, payload)


@router.post(
    "/compras/{compra_id}/anular",
    response_model=CompraRead,
    summary="Anular compra",
    responses=COMMON_RESPONSES,
)
def anular_compra(compra_id: UUID, payload: CompraAnularRequest, session: Session = Depends(get_session)):
    """Anula la compra y conserva trazabilidad para auditoría tributaria y operativa."""
    return compra_service.anular_compra(session, compra_id, payload)


@router.get(
    "/v1/compras/{compra_id}/sugerir-retencion",
    response_model=RetencionSugeridaRead,
    summary="Sugerir retención",
    responses=COMMON_RESPONSES,
)
def sugerir_retencion_compra(compra_id: UUID, session: Session = Depends(get_session)):
    """Sugiere retenciones desde plantilla de proveedor cruzando bases imponibles de la compra."""
    return retencion_service.sugerir_retencion(session, compra_id)


@router.post(
    "/v1/compras/{compra_id}/guardar-plantilla-retencion",
    response_model=PlantillaRetencionRead,
    summary="Guardar plantilla de retención",
    responses=COMMON_RESPONSES,
)
def guardar_plantilla_retencion_desde_compra(
    compra_id: UUID,
    payload: GuardarPlantillaRetencionRequest,
    session: Session = Depends(get_session),
):
    """Guarda una plantilla reutilizable de retención a partir de una retención digitada."""
    return retencion_service.guardar_plantilla_desde_retencion_digitada(session, compra_id, payload)


@router.post(
    "/v1/compras/{compra_id}/retenciones",
    response_model=RetencionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar retención emitida",
    responses=COMMON_RESPONSES,
)
def crear_retencion_compra(
    compra_id: UUID,
    payload: RetencionCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Crea una retención emitida asociada a compra y la encola para proceso SRI."""
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
    summary="Emitir retención",
    responses=COMMON_RESPONSES,
)
def emitir_retencion(
    retencion_id: UUID,
    payload: RetencionEmitRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    """Emite o encola una retención y recalcula el saldo administrativo de la CxP."""
    return retencion_service.emitir_retencion(session, retencion_id, payload, background_tasks=background_tasks)


@router.get(
    "/v1/retenciones/{retencion_id}/fe-payload",
    response_model=RetencionFEPayloadRead,
    summary="Obtener payload FE-EC de retención",
    responses=COMMON_RESPONSES,
)
def obtener_payload_fe_retencion(retencion_id: UUID, session: Session = Depends(get_session)):
    """Genera el payload FE-EC de la retención emitida para firma y transmisión al SRI."""
    return retencion_service.obtener_payload_fe_retencion(session, retencion_id)
