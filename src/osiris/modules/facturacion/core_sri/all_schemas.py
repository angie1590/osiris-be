from __future__ import annotations

from osiris.modules.facturacion.core_sri.schemas import (
    CENT,
    IVA_0_CODES,
    IVA_12_CODES,
    IVA_15_CODES,
    IVA_NO_OBJETO_CODES,
    ImpuestoAplicadoInput,
    VentaCompraDetalleCreate,
    VentaCompraDetalleRegistroCreate,
    q2,
)
from osiris.modules.facturacion.ventas.schemas import (
    CuentaPorCobrarRead,
    PagoCxCCreate,
    PagoCxCRead,
    RetencionRecibidaAnularRequest,
    RetencionRecibidaCreate,
    RetencionRecibidaDetalleCreate,
    RetencionRecibidaDetalleRead,
    RetencionRecibidaRead,
    VentaAnularRequest,
    VentaCreate,
    VentaDetalleImpuestoRead,
    VentaDetalleImpuestoSnapshotRead,
    VentaDetalleRead,
    VentaEmitRequest,
    VentaRead,
    VentaRegistroCreate,
    VentaUpdate,
)
from osiris.modules.facturacion.compras.schemas import (
    CompraAnularRequest,
    CompraCreate,
    CompraRead,
    CompraRegistroCreate,
    CompraUpdate,
    GuardarPlantillaRetencionRequest,
    PagoCxPCreate,
    PagoCxPRead,
    PlantillaRetencionDetalleInput,
    PlantillaRetencionDetalleRead,
    PlantillaRetencionRead,
    RetencionCreate,
    RetencionDetalleCreate,
    RetencionDetalleRead,
    RetencionEmitRequest,
    RetencionRead,
    RetencionSugeridaDetalleRead,
    RetencionSugeridaRead,
)
from osiris.modules.facturacion.reportes.schemas import ReporteTopProductoRead, ReporteVentasResumenRead

__all__ = [name for name in globals() if not name.startswith("_")]
