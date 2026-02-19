# Reporte de Auditoría: Osiris Backend - Épica 2 (Auditoría y Bitácora)

## Resumen Ejecutivo

**Estado Global: CUMPLE PARCIALMENTE ⚠️**
La implementación base de auditoría y soft delete es sólida. Se detectaron fallos menores en la automatización del filtrado (`activo=True`) y la cobertura de pruebas específica para la inyección de usuario.

| Card | Estado | Detalle |
| :--- | :--- | :--- |
| **E2-1 (Auditoría Std)** | **NO CUMPLE** | Falta filtrado automático de `activo=True` en consultas base (requiere `WHERE` manual). |
| **E2-2 (Audit Log)** | **CUMPLE** | Listeners `after_update` implementados con snapshots JSON (Before/After). |
| **E2-3 (Historial SRI)** | **CUMPLE** | Tablas de historial existen y exigen `motivo_cambio` para anulaciones. |
| **E2-4 (Seguridad)** | **CUMPLE** | Middleware captura eventos 403 y registra IP/Usuario en `log_unauthorized_access`. |

---

## Detalles Técnicos y Hallazgos

### Card E2-1: Auditoría Estándar y Soft Delete
*   **Archivo:** `src/osiris/domain/base_models.py`
*   **Hallazgo (CUMPLE):** `AuditMixin` usa `contextvars` y `event.listens_for(..., "before_insert")` para inyectar `created_by`/`updated_by`.
*   **Hallazgo (NO CUMPLE):** Aunque `SoftDeleteMixin` agrega el campo `activo`, **no existe un mecanismo global** (como `FILTER` de SQLAlchemy o una clase `Session` personalizada) que filtre automáticamente `activo=True`.
*   **Corrección Necesaria:**
    ```python
    # Sugerencia: Implementar una clase Query personalizada o filtrar explícitamente en el repositorio base.
    # src/osiris/domain/repository.py
    def list(self, session, ...):
        stmt = select(self.model).where(self.model.activo == True)  # Filtrado manual requerido actualmente
    ```

### Card E2-2: Audit Log Before/After
*   **Archivo:** `src/osiris/modules/common/audit_log/entity.py` y `listeners.py`
*   **Hallazgo (CUMPLE):**
    *   Entidad `AuditLog` tiene `estado_anterior` y `estado_nuevo` (JSON).
    *   Listeners `after_update` en `Empresa`, `Producto` y `Venta` capturan los cambios automáticamente.

### Card E2-3: Historial de Estados y SRI
*   **Archivo:** `src/osiris/modules/facturacion/entity.py`
*   **Hallazgo (CUMPLE):**
    *   Tablas `VentaEstadoHistorial` y `DocumentoElectronicoHistorial` definidas.
    *   Campo `motivo_cambio` es `Text` y obligatorio (`nullable=False`).
    *   Servicio valida que `motivo_cambio` no sea vacío en anulaciones.

### Card E2-4: Auditoría de Seguridad
*   **Archivo:** `src/osiris/main.py`
*   **Hallazgo (CUMPLE):**
    *   Middleware `enforce_sensitive_access_control` intercepta peticiones.
    *   Si el usuario no tiene permiso o no está autenticado, llama a `log_unauthorized_access` y devuelve 403.
    *   Captura también si el endpoint interno devuelve 403.
