from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from osiris.core.db import get_session
from osiris.modules.facturacion.reportes.schemas import (
    AgrupacionTendencia,
    ReporteCajaCierreDiarioRead,
    ReporteCarteraCobrarItemRead,
    ReporteCarteraPagarItemRead,
    ReporteComprasPorProveedorRead,
    ReporteInventarioKardexRead,
    ReporteInventarioValoracionRead,
    ReporteImpuestosMensualRead,
    ReporteTopProductoRead,
    ReporteVentasPorVendedorRead,
    ReporteVentasResumenRead,
    ReporteVentasTendenciaRead,
)
from osiris.modules.facturacion.reportes.services.reporte_cartera_service import (
    ReporteCarteraService,
)
from osiris.modules.facturacion.reportes.services.reporte_caja_service import (
    ReporteCajaService,
)
from osiris.modules.facturacion.reportes.services.reporte_compras_service import (
    ReporteComprasService,
)
from osiris.modules.facturacion.reportes.services.reporte_inventario_service import (
    ReporteInventarioService,
)
from osiris.modules.facturacion.reportes.services.reporte_tributario_service import (
    ReporteTributarioService,
)
from osiris.modules.facturacion.reportes.services.reportes_service import ReportesVentasService


router = APIRouter()
reportes_ventas_service = ReportesVentasService()
reporte_tributario_service = ReporteTributarioService()
reporte_inventario_service = ReporteInventarioService()
reporte_cartera_service = ReporteCarteraService()
reporte_caja_service = ReporteCajaService()
reporte_compras_service = ReporteComprasService()


@router.get(
    "/v1/reportes/ventas/resumen",
    response_model=ReporteVentasResumenRead,
    tags=["Reportes"],
)
def obtener_reporte_ventas_resumen(
    fecha_inicio: date = Query(..., description="Fecha inicial del rango"),
    fecha_fin: date = Query(..., description="Fecha final del rango"),
    punto_emision_id: UUID | None = Query(default=None),
    sucursal_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return reportes_ventas_service.obtener_resumen_ventas(
        session,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        punto_emision_id=punto_emision_id,
        sucursal_id=sucursal_id,
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


@router.get(
    "/v1/reportes/compras/por-proveedor",
    response_model=list[ReporteComprasPorProveedorRead],
    tags=["Reportes"],
)
def obtener_reporte_compras_por_proveedor(
    fecha_inicio: date = Query(..., description="Fecha inicial del rango"),
    fecha_fin: date = Query(..., description="Fecha final del rango"),
    sucursal_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return reporte_compras_service.obtener_compras_por_proveedor(
        session,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        sucursal_id=sucursal_id,
    )


@router.get(
    "/v1/reportes/impuestos/mensual",
    response_model=ReporteImpuestosMensualRead,
    tags=["Reportes"],
)
def obtener_reporte_impuestos_mensual(
    mes: int = Query(..., ge=1, le=12, description="Mes fiscal (1-12)"),
    anio: int = Query(..., ge=2000, le=2100, description="Anio fiscal"),
    sucursal_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return reporte_tributario_service.obtener_reporte_mensual_impuestos(
        session,
        mes=mes,
        anio=anio,
        sucursal_id=sucursal_id,
    )


@router.get(
    "/v1/reportes/inventario/valoracion",
    response_model=ReporteInventarioValoracionRead,
    tags=["Reportes"],
)
def obtener_reporte_valoracion_inventario(
    session: Session = Depends(get_session),
):
    return reporte_inventario_service.obtener_valoracion_inventario(session)


@router.get(
    "/v1/reportes/inventario/kardex/{producto_id}",
    response_model=ReporteInventarioKardexRead,
    tags=["Reportes"],
)
def obtener_reporte_kardex_inventario(
    producto_id: UUID,
    fecha_inicio: date | None = Query(default=None, description="Fecha inicial opcional"),
    fecha_fin: date | None = Query(default=None, description="Fecha final opcional"),
    sucursal_id: UUID | None = Query(default=None, description="Filtro opcional por sucursal"),
    session: Session = Depends(get_session),
):
    return reporte_inventario_service.obtener_kardex_historico(
        session,
        producto_id=producto_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        sucursal_id=sucursal_id,
    )


@router.get(
    "/v1/reportes/cartera/cobrar",
    response_model=list[ReporteCarteraCobrarItemRead],
    tags=["Reportes"],
)
def obtener_reporte_cartera_cobrar(
    session: Session = Depends(get_session),
):
    return reporte_cartera_service.obtener_cartera_cobrar(session)


@router.get(
    "/v1/reportes/cartera/pagar",
    response_model=list[ReporteCarteraPagarItemRead],
    tags=["Reportes"],
)
def obtener_reporte_cartera_pagar(
    session: Session = Depends(get_session),
):
    return reporte_cartera_service.obtener_cartera_pagar(session)


@router.get(
    "/v1/reportes/caja/cierre-diario",
    response_model=ReporteCajaCierreDiarioRead,
    tags=["Reportes"],
)
def obtener_reporte_cierre_caja_diario(
    fecha: date = Query(default_factory=date.today, description="Fecha del arqueo"),
    usuario_id: UUID | None = Query(default=None, description="Filtro opcional por usuario"),
    sucursal_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    return reporte_caja_service.obtener_cierre_diario(
        session,
        fecha=fecha,
        usuario_id=usuario_id,
        sucursal_id=sucursal_id,
    )
