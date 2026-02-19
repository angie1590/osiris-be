from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from osiris.core.audit_context import (
    extract_user_id_from_request_headers,
    reset_current_user_id,
    set_current_user_id,
)
from osiris.core.settings import get_settings
from osiris.core.errors import NotFoundError
from osiris.modules.common.rol.router import router as rol_router
from osiris.modules.common.empresa.router import router as empresa_router
from osiris.modules.common.sucursal.router import router as sucursal_router
from osiris.modules.common.punto_emision.router import router as punto_emision_router
from osiris.modules.common.audit_log.router import router as audit_log_router
from osiris.modules.common.persona.router import router as persona_router
from osiris.modules.common.tipo_cliente.router import router as tipo_cliente_router
from osiris.modules.common.usuario.router import router as usuario_router
from osiris.modules.common.cliente.router import router as cliente_router
from osiris.modules.common.empleado.router import router as empleado_router
from osiris.modules.common.proveedor_persona.router import router as proveedor_persona_router
from osiris.modules.common.proveedor_sociedad.router import router as proveedor_sociedad_router
from osiris.modules.common.modulo.router import router as modulo_router
from osiris.modules.common.rol_modulo_permiso.router import router as rol_modulo_permiso_router
from osiris.modules.inventario.categoria.router import router as categoria_router
from osiris.modules.inventario.casa_comercial.router import router as casa_comercial_router
from osiris.modules.inventario.atributo.router import router as atributo_router
from osiris.modules.inventario.categoria_atributo.router import router as categoria_atributo_router
from osiris.modules.inventario.bodega.router import router as bodega_router
from osiris.modules.inventario.producto.router import router as producto_router
from osiris.modules.inventario.producto_impuesto.router import router as producto_impuesto_router
from osiris.modules.sri.impuesto_catalogo.router import router as impuesto_catalogo_router
from osiris.modules.facturacion.router import router as facturacion_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fuerza validacion de settings al arranque para fail-fast con mensaje claro.
    get_settings()
    yield


app = FastAPI(
    title="Osiris API",
    description="API para la gestión tributaria y empresarial.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def inject_audit_user_context(request: Request, call_next):
    user_id = extract_user_id_from_request_headers(
        authorization=request.headers.get("Authorization"),
        x_user_id=request.headers.get("X-User-Id"),
    )
    token = set_current_user_id(user_id)
    try:
        return await call_next(request)
    finally:
        reset_current_user_id(token)


@app.exception_handler(NotFoundError)
async def not_found_handler(_req: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# Incluir routers
app.include_router(rol_router, prefix="/api")
app.include_router(empresa_router, prefix="/api")
app.include_router(sucursal_router, prefix="/api")
app.include_router(punto_emision_router, prefix="/api")
app.include_router(audit_log_router, prefix="/api/v1")
app.include_router(persona_router, prefix="/api")
app.include_router(tipo_cliente_router, prefix="/api")
app.include_router(usuario_router, prefix="/api")
app.include_router(cliente_router, prefix="/api")
app.include_router(empleado_router, prefix="/api")
app.include_router(proveedor_persona_router, prefix="/api")
app.include_router(proveedor_sociedad_router, prefix="/api")
app.include_router(modulo_router, prefix="/api")
app.include_router(rol_modulo_permiso_router, prefix="/api")
app.include_router(categoria_router, prefix="/api")
app.include_router(casa_comercial_router, prefix="/api")
app.include_router(atributo_router, prefix="/api")
app.include_router(categoria_atributo_router, prefix="/api")
app.include_router(bodega_router, prefix="/api")
app.include_router(producto_router, prefix="/api")
app.include_router(producto_impuesto_router, prefix="/api/productos")
app.include_router(impuesto_catalogo_router, prefix="/api/impuestos")
app.include_router(facturacion_router, prefix="/api")
