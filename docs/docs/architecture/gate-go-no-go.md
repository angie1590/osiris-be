---
sidebar_position: 4
---

# Gate Go/No-Go

## Objetivo

Definir un punto de control técnico y operativo antes de promover un release candidate, usando evidencia reproducible y sin decisiones subjetivas.

## Alcance

Este gate cubre:

- calidad técnica del código (`ruff`)
- regresión funcional (`pytest`)
- integridad de documentación (`docs build`)
- señales operativas (health/metrics) entregadas en Sprint 1-3

## Criterios obligatorios de GO

Todos son **bloqueantes**:

1. Lint técnico en verde.
2. Suite de pruebas en verde.
3. Build de documentación en verde.
4. Endpoints operativos disponibles:
   - `GET /health/live`
   - `GET /health/ready`
   - `GET /metrics`
5. Sin regresiones en hardening:
   - accesos sensibles mantienen `403` aunque falle auditoría de seguridad.
6. Métricas base presentes:
   - HTTP, seguridad, FE worker, DB por query/request, overload/readiness.

Si cualquiera falla: **NO-GO**.

## Comando oficial del gate

Desde la raíz del repo:

```bash
make gate-go-no-go
```

Este comando ejecuta:

1. `poetry run ruff check src tests`
2. `poetry run pytest -q`
3. `cd docs && npm run build --silent`

## Evidencia mínima para acta de gate

Guardar en el ticket/release:

1. Output completo de `make gate-go-no-go`.
2. Resultado del checklist QA de Sprint 1/2/3.
3. Commit hash candidate.
4. Fecha/hora y responsable de aprobación.

## Checklist QA de decisión

### 1) Observabilidad (Sprint 1)

- `X-Request-ID` se genera y propaga.
- `/metrics` responde correctamente.
- métricas de seguridad y FE worker disponibles.

### 2) Performance medible (Sprint 2)

- métricas DB por query y por request incrementan con tráfico.
- si `OBSERVABILITY_DB_METRICS_ENABLED=false`, no crecen métricas DB por request.
- headers de performance disponibles si `PERFORMANCE_RESPONSE_HEADERS_ENABLED=true`.

### 3) Resiliencia operativa (Sprint 3)

- `GET /health/live` => `200`.
- `GET /health/ready` => `200` con DB up / `503` con DB down.
- saturación controlada retorna `503`.
- `osiris_http_overload_rejections_total` y `osiris_health_readiness_checks_total` incrementan.

## Reglas de decisión

- **GO**: todos los criterios técnicos + QA bloqueante en verde.
- **GO CONDICIONAL**: permitido solo para hallazgos no bloqueantes y con plan/corte de corrección documentado.
- **NO-GO**: cualquier falla en criterio bloqueante o riesgo operativo sin mitigación.

## Plantilla de cierre (resumen rápido)

```text
Release candidate: <hash/tag>
Gate execution date: <YYYY-MM-DD HH:MM>
Owner: <nombre>

Lint: PASS/FAIL
Tests: PASS/FAIL
Docs build: PASS/FAIL
Health endpoints: PASS/FAIL
Metrics validation: PASS/FAIL
QA checklist: PASS/FAIL

Final decision: GO / NO-GO
Observaciones:
```
