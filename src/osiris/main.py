from fastapi import FastAPI
from src.osiris.api.empresa_router import router as empresa_router

app = FastAPI(
    title="Osiris API",
    description="API para la gestión tributaria y empresarial.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Incluir routers
app.include_router(empresa_router)
