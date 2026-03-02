import asyncio
import logging
import time
from contextlib import asynccontextmanager, suppress

from fastapi.concurrency import run_in_threadpool
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlmodel import Session
from osiris.core.audit_context import (
    extract_auth_context_from_request_headers,
    extract_user_id_from_request_headers,
    reset_current_company_id,
    reset_current_user_id,
    set_current_company_id,
    set_current_user_id,
)
from osiris.core.db import engine
from osiris.core.settings import get_settings
from osiris.core.observability import (
    METRICS,
    configure_json_logging,
    initialize_metrics,
    new_request_id,
    observe_request_latency_seconds,
    record_fe_worker_error,
    record_fe_worker_run,
    record_http_in_flight,
    record_http_request,
    record_unauthorized_access,
    reset_current_request_id,
    set_current_request_id,
)
from osiris.core.errors import NotFoundError
from osiris.core.openapi_docs import build_gold_standard_openapi
from osiris.core.security_audit import (
    is_user_authorized_for_rule,
    log_unauthorized_access,
    match_sensitive_rule,
    parse_attempted_payload,
)
from osiris.modules.common.audit_log.router import router as audit_log_router
from osiris.modules.common.cliente.router import router as cliente_router
from osiris.modules.common.empleado.router import router as empleado_router
from osiris.modules.common.empresa.router import router as empresa_router
from osiris.modules.common.modulo.router import router as modulo_router
from osiris.modules.common.persona.router import router as persona_router
from osiris.modules.common.proveedor_persona.router import router as proveedor_persona_router
from osiris.modules.common.proveedor_sociedad.router import router as proveedor_sociedad_router
from osiris.modules.common.punto_emision.router import router as punto_emision_router
from osiris.modules.common.rol.router import router as rol_router
from osiris.modules.common.rol_modulo_permiso.router import router as rol_modulo_permiso_router
from osiris.modules.common.sucursal.router import router as sucursal_router
from osiris.modules.common.tipo_cliente.router import router as tipo_cliente_router
from osiris.modules.common.usuario.router import router as usuario_router
from osiris.modules.compras.router import router as compras_router
from osiris.modules.impresion.router import router as impresion_router
from osiris.modules.inventario.atributo.router import router as atributo_router
from osiris.modules.inventario.bodega.router import router as bodega_router
from osiris.modules.inventario.casa_comercial.router import router as casa_comercial_router
from osiris.modules.inventario.categoria.router import router as categoria_router
from osiris.modules.inventario.categoria_atributo.router import router as categoria_atributo_router
from osiris.modules.inventario.movimientos.router import router as movimientos_router
from osiris.modules.inventario.producto.router import router as producto_router
from osiris.modules.inventario.producto_bodega.router import router as producto_bodega_router
from osiris.modules.inventario.producto_impuesto.router import router as producto_impuesto_router
from osiris.modules.reportes.router import router as reportes_router
from osiris.modules.sri.facturacion_electronica.router import router as facturacion_electronica_router
from osiris.modules.sri.facturacion_electronica.services.orquestador_fe_service import OrquestadorFEService
from osiris.modules.sri.impuesto_catalogo.router import router as impuesto_catalogo_router
from osiris.modules.ventas.router import router as ventas_router

logger = logging.getLogger(__name__)
request_logger = logging.getLogger("osiris.request")


def _resolve_log_level(level_name: str) -> int:
    return getattr(logging, level_name.upper(), logging.INFO)


def _procesar_cola_fe_once() -> int:
    service = OrquestadorFEService()
    with Session(engine) as session:
        return service.procesar_cola(session)


async def _run_fe_queue_worker(poll_interval_seconds: int) -> None:
    while True:
        await asyncio.sleep(poll_interval_seconds)
        try:
            procesados = await run_in_threadpool(_procesar_cola_fe_once)
            record_fe_worker_run(processed=procesados)
            if procesados:
                logger.info("Worker FE procesó %s documentos de la cola.", procesados)
        except Exception as exc:  # pragma: no cover - protección operacional
            record_fe_worker_error()
            logger.exception("Error en worker FE al procesar cola: %s", exc)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Fuerza validacion de settings al arranque para fail-fast con mensaje claro.
    app_settings = get_settings()
    worker_task = None
    if app_settings.FE_QUEUE_AUTO_PROCESS_ENABLED:
        worker_task = asyncio.create_task(
            _run_fe_queue_worker(app_settings.FE_QUEUE_POLL_INTERVAL_SECONDS)
        )
        app_instance.state.fe_queue_worker_task = worker_task
    try:
        yield
    finally:
        if worker_task is not None:
            worker_task.cancel()
            with suppress(asyncio.CancelledError):
                await worker_task


app = FastAPI(
    title="Osiris ERP API",
    description="API para ERP Ecuatoriano (SRI)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.state.security_audit_engine = engine
app_settings = get_settings()
if app_settings.OBSERVABILITY_JSON_LOGS_ENABLED:
    configure_json_logging(level=_resolve_log_level(app_settings.LOG_LEVEL))
if app_settings.OBSERVABILITY_METRICS_ENABLED:
    initialize_metrics()


def custom_openapi():
    return build_gold_standard_openapi(app)


app.openapi = custom_openapi  # type: ignore[method-assign]


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


async def _safe_log_unauthorized_access(
    *,
    security_engine,
    request: Request,
    user_id: str | None,
    payload,
    reason: str,
    rule,
) -> None:
    try:
        await run_in_threadpool(
            _log_unauthorized_access_sync,
            security_engine=security_engine,
            request=request,
            user_id=user_id,
            payload=payload,
            reason=reason,
            rule=rule,
        )
    except Exception as exc:  # pragma: no cover - hardening defensivo
        logger.exception(
            "No se pudo registrar UNAUTHORIZED_ACCESS en auditoria (se preserva respuesta 403): %s",
            exc,
        )


@app.middleware("http")
async def observability_http_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or new_request_id()
    request_token = set_current_request_id(request_id)
    record_http_in_flight(+1)
    start = time.monotonic()
    status_code = 500
    route_path = request.url.path
    try:
        response = await call_next(request)
        status_code = response.status_code
        route = request.scope.get("route")
        if route is not None and getattr(route, "path", None):
            route_path = route.path
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        latency_seconds = observe_request_latency_seconds(start)
        record_http_request(
            method=request.method,
            path=route_path,
            status_code=status_code,
            latency_seconds=latency_seconds,
        )
        record_http_in_flight(-1)
        request_logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": route_path,
                "status_code": status_code,
                "latency_ms": round(latency_seconds * 1000, 3),
                "client_ip": request.client.host if request.client else None,
            },
        )
        reset_current_request_id(request_token)


@app.middleware("http")
async def inject_audit_user_context(request: Request, call_next):
    user_id, company_id = extract_auth_context_from_request_headers(
        authorization=request.headers.get("Authorization"),
        x_user_id=request.headers.get("X-User-Id"),
        x_company_id=request.headers.get("X-Empresa-Id"),
    )
    user_token = set_current_user_id(user_id)
    company_token = set_current_company_id(company_id)
    try:
        return await call_next(request)
    finally:
        reset_current_user_id(user_token)
        reset_current_company_id(company_token)


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
        record_unauthorized_access("missing_user")
        await _safe_log_unauthorized_access(
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
        record_unauthorized_access("insufficient_permissions")
        await _safe_log_unauthorized_access(
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
        record_unauthorized_access("endpoint_returned_403")
        await _safe_log_unauthorized_access(
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


@app.get("/metrics", include_in_schema=False)
async def metrics() -> PlainTextResponse:
    if not app_settings.OBSERVABILITY_METRICS_ENABLED:
        return PlainTextResponse(status_code=404, content="metrics disabled\n")
    content = METRICS.render_prometheus()
    return PlainTextResponse(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

# Incluir routers
app.include_router(empresa_router)
app.include_router(sucursal_router)
app.include_router(punto_emision_router)
app.include_router(rol_router)
app.include_router(usuario_router)
app.include_router(persona_router)
app.include_router(cliente_router)
app.include_router(empleado_router)
app.include_router(tipo_cliente_router)
app.include_router(modulo_router)
app.include_router(rol_modulo_permiso_router)
app.include_router(proveedor_persona_router)
app.include_router(proveedor_sociedad_router)
app.include_router(audit_log_router)

app.include_router(atributo_router)
app.include_router(categoria_router)
app.include_router(casa_comercial_router)
app.include_router(categoria_atributo_router)
app.include_router(bodega_router)
app.include_router(producto_router)
app.include_router(producto_bodega_router)
app.include_router(producto_impuesto_router)
app.include_router(movimientos_router)

app.include_router(impuesto_catalogo_router)
app.include_router(facturacion_electronica_router)

app.include_router(ventas_router)
app.include_router(compras_router)
app.include_router(reportes_router)
app.include_router(impresion_router)
