from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.facturacion.reportes.schemas import (
    AgrupacionTendencia,
    ReporteTopProductoRead,
    ReporteVentasPorVendedorRead,
    ReporteVentasResumenRead,
    ReporteVentasTendenciaRead,
)
from osiris.modules.facturacion.reportes.services.reportes_service import ReportesVentasService


router = APIRouter()
reportes_ventas_service = ReportesVentasService()


@router.get(
    "/v1/reportes/ventas/resumen",
    response_model=ReporteVentasResumenRead,
    tags=["Reportes"],
)
def obtener_reporte_ventas_resumen(
    fecha_inicio: date = Query(..., description="Fecha inicial del rango"),
    fecha_fin: date = Query(..., description="Fecha final del rango"),
    punto_emision_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return reportes_ventas_service.obtener_resumen_ventas(
        session,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        punto_emision_id=punto_emision_id,
    )


@router.get(
    "/v1/reportes/ventas/top-productos",
    response_model=list[ReporteTopProductoRead],
    tags=["Reportes"],
)
def obtener_reporte_top_productos_ventas(
    fecha_inicio: date | None = Query(default=None, description="Fecha inicial opcional"),
    fecha_fin: date | None = Query(default=None, description="Fecha final opcional"),
    punto_emision_id: UUID | None = Query(default=None),
    limite: int = Query(default=10, ge=1, le=100),
    session: Session = Depends(get_session),
):
    return reportes_ventas_service.obtener_top_productos(
        session,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        punto_emision_id=punto_emision_id,
        limite=limite,
    )


@router.get(
    "/v1/reportes/ventas/tendencias",
    response_model=list[ReporteVentasTendenciaRead],
    tags=["Reportes"],
)
def obtener_reporte_tendencias_ventas(
    fecha_inicio: date = Query(..., description="Fecha inicial del rango"),
    fecha_fin: date = Query(..., description="Fecha final del rango"),
    agrupacion: AgrupacionTendencia = Query(default=AgrupacionTendencia.DIARIA),
    session: Session = Depends(get_session),
):
    return reportes_ventas_service.obtener_tendencias_ventas(
        session,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        agrupacion=agrupacion,
    )


@router.get(
    "/v1/reportes/ventas/por-vendedor",
    response_model=list[ReporteVentasPorVendedorRead],
    tags=["Reportes"],
)
def obtener_reporte_ventas_por_vendedor(
    fecha_inicio: date | None = Query(default=None, description="Fecha inicial opcional"),
    fecha_fin: date | None = Query(default=None, description="Fecha final opcional"),
    session: Session = Depends(get_session),
):
    return reportes_ventas_service.obtener_ventas_por_vendedor(
        session,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
