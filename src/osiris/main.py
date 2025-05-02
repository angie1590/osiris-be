from fastapi import FastAPI
from src.osiris.api.empresa_router import router as empresa_router
from src.osiris.api.punto_emision_router import router as punto_emision
from src.osiris.api.sucursal_router import router as sucursal
from src.osiris.api.persona_router import router as persona_router
from src.osiris.api.rol_router import router as rol_router
from src.osiris.api.usuario_router import router as usuario_router
from src.osiris.api.empleado_router import router as empleado_router
from src.osiris.api.tipo_cliente_router import router as tipo_cliente_router

app = FastAPI(
    title="Osiris API",
    description="API para la gestión tributaria y empresarial.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Incluir routers
app.include_router(empresa_router)
app.include_router(sucursal)
app.include_router(punto_emision)
app.include_router(persona_router)
app.include_router(rol_router)
app.include_router(usuario_router)
app.include_router(empleado_router)
app.include_router(tipo_cliente_router)
