from __future__ import annotations

from fastapi import APIRouter

from osiris.modules.sri.facturacion_electronica.router import router as facturacion_electronica_router
from osiris.modules.sri.impuesto_catalogo.router import router as impuesto_catalogo_router


router = APIRouter(tags=["SRI"])

router.include_router(impuesto_catalogo_router, prefix="/impuestos", tags=["SRI"])
router.include_router(facturacion_electronica_router, tags=["SRI"])
