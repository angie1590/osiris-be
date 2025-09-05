from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.osiris.core.errors import NotFoundError
from src.osiris.modules.common.rol.router import router as rol_router
from src.osiris.modules.common.empresa.router import router as empresa_router
from src.osiris.modules.common.sucursal.router import router as sucursal_router
from src.osiris.modules.common.punto_emision.router import router as punto_emision_router
from src.osiris.modules.common.persona.router import router as persona_router
from src.osiris.modules.common.tipo_cliente.router import router as tipo_cliente_router
from src.osiris.modules.common.usuario.router import router as usuario_router
from src.osiris.modules.common.cliente.router import router as cliente_router

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
