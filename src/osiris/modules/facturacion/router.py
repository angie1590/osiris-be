from __future__ import annotations

from fastapi import APIRouter

from osiris.modules.facturacion.compras.router import router as compras_router
from osiris.modules.facturacion.facturacion_electronica.router import router as fe_router
from osiris.modules.facturacion.impresion.router import router as impresion_router
from osiris.modules.facturacion.reportes.router import router as reportes_router
from osiris.modules.facturacion.ventas.router import router as ventas_router


router = APIRouter()
router.include_router(ventas_router)
router.include_router(compras_router)
router.include_router(fe_router)
router.include_router(impresion_router)
router.include_router(reportes_router)
