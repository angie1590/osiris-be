from __future__ import annotations

from fastapi import APIRouter

from osiris.modules.inventario.atributo.router import router as atributo_router
from osiris.modules.inventario.bodega.router import router as bodega_router
from osiris.modules.inventario.casa_comercial.router import router as casa_comercial_router
from osiris.modules.inventario.categoria.router import router as categoria_router
from osiris.modules.inventario.categoria_atributo.router import router as categoria_atributo_router
from osiris.modules.inventario.movimientos.router import router as movimientos_router
from osiris.modules.inventario.producto.router import router as producto_router
from osiris.modules.inventario.producto_impuesto.router import router as producto_impuesto_router


router = APIRouter(tags=["Inventario"])

router.include_router(categoria_router, tags=["Inventario"])
router.include_router(casa_comercial_router, tags=["Inventario"])
router.include_router(atributo_router, tags=["Inventario"])
router.include_router(categoria_atributo_router, tags=["Inventario"])
router.include_router(bodega_router, tags=["Inventario"])
router.include_router(producto_router, tags=["Inventario"])
router.include_router(producto_impuesto_router, prefix="/productos", tags=["Inventario"])
router.include_router(movimientos_router, tags=["Inventario"])
