from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from osiris.core.errors import NotFoundError
from osiris.modules.common.rol.router import router as rol_router
from osiris.modules.common.empresa.router import router as empresa_router
from osiris.modules.common.sucursal.router import router as sucursal_router
from osiris.modules.common.punto_emision.router import router as punto_emision_router
from osiris.modules.common.persona.router import router as persona_router
from osiris.modules.common.tipo_cliente.router import router as tipo_cliente_router
from osiris.modules.common.usuario.router import router as usuario_router
from osiris.modules.common.cliente.router import router as cliente_router
from osiris.modules.common.empleado.router import router as empleado_router
from osiris.modules.common.proveedor_persona.router import router as proveedor_persona_router
from osiris.modules.common.proveedor_sociedad.router import router as proveedor_sociedad_router
from osiris.modules.inventario.categoria.router import router as categoria_router
from osiris.modules.inventario.casa_comercial.router import router as casa_comercial_router
from osiris.modules.inventario.atributo.router import router as atributo_router
from osiris.modules.inventario.tipo_producto.router import router as tipo_producto_router
from osiris.modules.inventario.producto.router import router as producto_router
from osiris.modules.inventario.producto_impuesto.router import router as producto_impuesto_router
from osiris.modules.aux.impuesto_catalogo.router import router as impuesto_catalogo_router

app = FastAPI(
    title="Osiris API",
    description="API para la gestión tributaria y empresarial.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.exception_handler(NotFoundError)
async def not_found_handler(_req: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# Incluir routers
app.include_router(rol_router, prefix="/api")
app.include_router(empresa_router, prefix="/api")
app.include_router(sucursal_router, prefix="/api")
app.include_router(punto_emision_router, prefix="/api")
app.include_router(persona_router, prefix="/api")
app.include_router(tipo_cliente_router, prefix="/api")
app.include_router(usuario_router, prefix="/api")
app.include_router(cliente_router, prefix="/api")
app.include_router(empleado_router, prefix="/api")
app.include_router(proveedor_persona_router, prefix="/api")
app.include_router(proveedor_sociedad_router, prefix="/api")
app.include_router(categoria_router, prefix="/api")
app.include_router(casa_comercial_router, prefix="/api")
app.include_router(atributo_router, prefix="/api")
app.include_router(tipo_producto_router, prefix="/api")
app.include_router(producto_router, prefix="/api")
app.include_router(producto_impuesto_router, prefix="/api/productos")
app.include_router(impuesto_catalogo_router, prefix="/api/impuestos")
