# Reporte de Auditoría: Osiris Backend - Smoke Tests (E0-E5)

## Resumen Ejecutivo

**Estado Global: NO CUMPLE ❌**
Aunque existe una estructura modular, la implementación viola principios críticos de reutilización de fixtures y faltan pruebas clave solicitadas en el checklist.

| Punto de Control | Estado | Detalle |
| :--- | :--- | :--- |
| **Modularidad** | **CUMPLE** | Archivos divididos por dominio (`test_crud_smoke.py`, etc.). |
| **Fixtures (CRÍTICO)** | **NO CUMPLE** | `conftest.py` está vacío. `test_crud_smoke.py` instancia `httpx.Client` manualmente. |
| **Aserciones Core** | **NO CUMPLE** | No hay verificación de Kardex (stock) en los tests de humo API. (Solo existen en integración). |
| **Lógica Tributaria** | **NO CUMPLE** | Falta `test_retencion_smoke.py` en la suite de humo. |
| **AuditLog** | **NO CUMPLE** | No existe prueba de humo para verificar la bitácora. |

---

## Detalles Técnicos y Correcciones Necesarias

### 1. Reutilización de Fixtures (CRÍTICO)
*   **Archivo:** `tests/smoke/conftest.py` está vacío.
*   **Problema:** `tests/smoke/test_crud_smoke.py` usa `with httpx.Client(...)` repetidamente.
*   **Corrección:** Definir `client` en `conftest.py` y usarlo.

```python
# tests/smoke/conftest.py
import pytest
import httpx

@pytest.fixture(scope="session")
def client():
    with httpx.Client(base_url="http://localhost:8000/api", timeout=5.0) as c:
        yield c
```

### 2. Aserciones de Integración (Kardex)
*   **Fallo:** Los tests de humo actuales solo verifican códigos HTTP 200/201. No llaman a `/api/v1/inventario/kardex` para confirmar el movimiento de stock real tras una venta/compra.

### 3. Falta de Cobertura Específica
*   **Retenciones:** No existe archivo de humo para retenciones recibidas.
*   **AuditLog:** No existe archivo de humo para consultar `/api/v1/audit-log`.
