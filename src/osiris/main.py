from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.osiris.core.errors import NotFoundError
from src.osiris.modules.common.rol.router import router as rol_router

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
