from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID

from osiris.core.db import get_session
from osiris.modules.inventario.producto_impuesto.models import (
    ProductoImpuestoRead,
)
from osiris.modules.inventario.producto_impuesto.service import ProductoImpuestoService
from osiris.modules.sri.impuesto_catalogo.models import ImpuestoCatalogoRead

router = APIRouter()
service = ProductoImpuestoService()


@router.get("/{producto_id}/impuestos", response_model=List[ImpuestoCatalogoRead], tags=["Productos"])
def listar_impuestos_producto(
    producto_id: UUID,
    session: Session = Depends(get_session),
):
    """Lista todos los impuestos asignados a un producto con su información completa del catálogo."""
    impuestos = service.get_impuestos_completos(session, producto_id)
    return [ImpuestoCatalogoRead.model_validate(imp) for imp in impuestos]


@router.post("/{producto_id}/impuestos", response_model=ProductoImpuestoRead, status_code=201, tags=["Productos"])
def asignar_impuesto_a_producto(
    producto_id: UUID,
    impuesto_catalogo_id: UUID,
    usuario_auditoria: str,
    session: Session = Depends(get_session),
):
    """
    Asigna un impuesto del catálogo a un producto.
    Aplica todas las validaciones: vigencia, compatibilidad tipo, máximo IVA/ICE, etc.
    """
    producto_impuesto = service.asignar_impuesto(
        session,
        producto_id,
        impuesto_catalogo_id,
        usuario_auditoria
    )

    # Cargar el impuesto completo para la respuesta
    impuesto = session.get(service.impuesto_repo.model, impuesto_catalogo_id)

    response = ProductoImpuestoRead.model_validate(producto_impuesto)
    if impuesto:
        response.impuesto = ImpuestoCatalogoRead.model_validate(impuesto)

    return response


@router.delete("/impuestos/{producto_impuesto_id}", status_code=204, tags=["Productos"])
def eliminar_impuesto_de_producto(
    producto_impuesto_id: UUID,
    session: Session = Depends(get_session),
):
    """Elimina (soft delete) la asignación de un impuesto a un producto."""
    service.eliminar_impuesto(session, producto_impuesto_id)
    return None
