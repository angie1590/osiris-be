from contextlib import asynccontextmanager

from fastapi.concurrency import run_in_threadpool
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session
from osiris.core.audit_context import (
    extract_user_id_from_request_headers,
    reset_current_user_id,
    set_current_user_id,
)
from osiris.core.db import engine
from osiris.core.settings import get_settings
from osiris.core.errors import NotFoundError
from osiris.core.security_audit import (
    is_user_authorized_for_rule,
    log_unauthorized_access,
    match_sensitive_rule,
    parse_attempted_payload,
)
from osiris.modules.common.router import router as common_router
from osiris.modules.inventario.router import router as inventario_router
from osiris.modules.sri.router import router as sri_router
from osiris.modules.ventas.router import router as ventas_router
from osiris.modules.compras.router import router as compras_router
from osiris.modules.impresion.router import router as impresion_router
from osiris.modules.reportes.router import router as reportes_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Fuerza validacion de settings al arranque para fail-fast con mensaje claro.
    get_settings()
    yield


app = FastAPI(
    title="Osiris ERP API",
    description="API para ERP Ecuatoriano (SRI)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.state.security_audit_engine = engine


def _log_unauthorized_access_sync(
    *,
    security_engine,
    request: Request,
    user_id: str | None,
    payload,
    reason: str,
    rule,
) -> None:
    with Session(security_engine) as security_session:
        log_unauthorized_access(
            security_session,
            request=request,
            user_id=user_id,
            payload=payload,
            reason=reason,
            rule=rule,
        )


def _is_user_authorized_for_rule_sync(
    *,
    security_engine,
    user_id: str,
    rule,
) -> bool:
    with Session(security_engine) as security_session:
        return is_user_authorized_for_rule(
            security_session,
            user_id=user_id,
            rule=rule,
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


@app.middleware("http")
async def enforce_sensitive_access_control(request: Request, call_next):
    rule = match_sensitive_rule(request.method, request.url.path)
    if not rule:
        return await call_next(request)

    raw_body = await request.body()
    payload = parse_attempted_payload(raw_body)

    async def receive() -> dict:
        return {"type": "http.request", "body": raw_body, "more_body": False}

    request._receive = receive  # type: ignore[attr-defined]

    user_id = extract_user_id_from_request_headers(
        authorization=request.headers.get("Authorization"),
        x_user_id=request.headers.get("X-User-Id"),
    )
    security_engine = getattr(request.app.state, "security_audit_engine", engine)

    if not user_id:
        await run_in_threadpool(
            _log_unauthorized_access_sync,
            security_engine=security_engine,
            request=request,
            user_id=None,
            payload=payload,
            reason="Usuario no autenticado para endpoint sensible.",
            rule=rule,
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "Acceso denegado a endpoint sensible."},
        )

    authorized = await run_in_threadpool(
        _is_user_authorized_for_rule_sync,
        security_engine=security_engine,
        user_id=user_id,
        rule=rule,
    )

    if not authorized:
        await run_in_threadpool(
            _log_unauthorized_access_sync,
            security_engine=security_engine,
            request=request,
            user_id=user_id,
            payload=payload,
            reason="Permisos insuficientes para endpoint sensible.",
            rule=rule,
        )
        return JSONResponse(
            status_code=403,
            content={"detail": "No tiene permisos para esta operación."},
        )

    response = await call_next(request)
    if response.status_code == 403:
        await run_in_threadpool(
            _log_unauthorized_access_sync,
            security_engine=security_engine,
            request=request,
            user_id=user_id,
            payload=payload,
            reason="El endpoint sensible devolvió 403.",
            rule=rule,
        )
    return response


@app.exception_handler(NotFoundError)
async def not_found_handler(_req: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

# Incluir routers
app.include_router(common_router, prefix="/api")
app.include_router(inventario_router, prefix="/api")
app.include_router(sri_router, prefix="/api")
app.include_router(ventas_router, prefix="/api")
app.include_router(compras_router, prefix="/api")
app.include_router(impresion_router, prefix="/api")
app.include_router(reportes_router, prefix="/api")
