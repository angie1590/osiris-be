# Reporte de Auditoría: Osiris Backend

## Resumen Ejecutivo

### ÉPICA 0: Fundaciones Técnicas
**Estado Global: CUMPLE ✅**
Todas las tarjetas auditadas de esta épica cumplen con la Definition of Done.

| Card | Estado | Detalle |
| :--- | :--- | :--- |
| **E0-1 (Settings)** | **CUMPLE** | `src/osiris/core/settings.py` usa `BaseSettings` y falla si faltan vars críticas (`FEEC_P12_PATH`, etc). |
| **E0-2 (Imports)** | **CUMPLE** | `pyproject.toml` configura `packages` correctamente. Imports son absolutos (`osiris.*`). |
| **E0-3 (Drivers)** | **CUMPLE** | Dependencia `psycopg` (v3) confirmada en `pyproject.toml`. |

### ÉPICA 1: Parametrización SRI
**Estado Global: NO CUMPLE ❌**
Ninguna de las tarjetas auditadas de esta épica cumple con los requisitos críticos.

| Card | Estado | Fallo Principal |
| :--- | :--- | :--- |
| **E1-1 (Regímenes)** | **NO CUMPLE** | Faltan campos `regimen` y `modo_emision` en `Empresa`. Falta validación RIMPE/NOTA_VENTA. |
| **E1-2 (Secuenciales)** | **NO CUMPLE** | Falta lógica de incremento atómico (`SELECT FOR UPDATE`) y formateo `zfill(9)`. |
| **E1-3 (Impuestos)** | **NO CUMPLE** | Módulo de Ventas/Facturas inexistente. Imposible verificar snapshot de impuestos. |

---

## Detalles de Auditoría - Épica 1 (Fallos)

### Card E1-1: Regímenes SRI
*   **Archivo Revisado:** `src/osiris/modules/common/empresa/entity.py`
*   **Problema:** El modelo `Empresa` no define los campos requeridos.
*   **Corrección Necesaria:**
    ```python
    # src/osiris/modules/common/empresa/entity.py
    class Empresa(...):
        # ...
        regimen: str = Field(default="GENERAL", nullable=False)
        modo_emision: str = Field(default="ELECTRONICO", nullable=False)
    ```
    *(Y agregar validadores Pydantic correspondientes en `models.py`)*

### Card E1-2: Secuenciales
*   **Archivo Revisado:** `src/osiris/modules/common/punto_emision/service.py`
*   **Problema:** No existe método para generar el siguiente secuencial con bloqueo.
*   **Corrección Necesaria:**
    Implementar método con bloqueo pesimista:
    ```python
    stmt = select(PuntoEmision).where(...).with_for_update()
    punto = session.exec(stmt).one()
    secuencial = str(punto.secuencial_actual).zfill(9)
    punto.secuencial_actual += 1
    session.add(punto)
    ```

### Card E1-3: Impuestos y FE-EC
*   **Archivo Revisado:** N/A (No encontrado)
*   **Problema:** No existe código fuente para `Venta`, `Factura` o `VentaDetalle` en `src/osiris/modules/`.
*   **Corrección Necesaria:**
    Implementar módulo de ventas asegurando que `VentaDetalle` guarde una copia de los valores del impuesto (snapshot) y no solo la FK.
