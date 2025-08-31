from fastapi import FastAPI
from src.osiris.modules.common.rol.router import router as roles_router

app = FastAPI(
    title="Osiris API",
    description="API para la gestión tributaria y empresarial.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Incluir routers
app.include_router(roles_router, prefix="/api")
