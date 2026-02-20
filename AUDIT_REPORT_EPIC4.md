# Reporte de Auditoría: Osiris Backend - Épica 4 (Compras, CxP y Retenciones)

## Resumen Ejecutivo

**Estado Global: CUMPLE ✅**
La implementación demuestra un alto nivel de integridad transaccional y matemática. El flujo Compra → Inventario → CxP → Retención → Pago está completamente orquestado y cubierto por pruebas.

| Card | Estado | Detalle |
| :--- | :--- | :--- |
| **E4-1 (Compra->CxP)** | **CUMPLE** | Creación atómica de `CuentaPorPagar` y movimiento de inventario (`INGRESO`) en la misma transacción. |
| **E4-2 (Motor CxP)** | **CUMPLE** | Bloqueo pesimista (`with_for_update`) al pagar. Validación estricta `pago <= saldo`. Actualización correcta de estados. |
| **E4-4 (Retenciones)** | **CUMPLE** | Emisión actualiza `valor_retenido` en CxP y recalcula saldo. Restricción de duplicidad implementada. |
| **E4-5 (SRI Async)** | **CUMPLE** | Uso correcto de `BackgroundTasks` para envío no bloqueante al SRI con lógica de reintentos. |
| **TDD (Tests)** | **CUMPLE** | Test de integración `test_flujo_administrativo_compras_cxp_retencion` valida el ciclo completo. |

---

## Detalles Técnicos y Hallazgos

### Integración Compra -> CxP e Inventario (E4-1)
*   **Archivo:** `src/osiris/modules/facturacion/compra_service.py`
*   **Unit of Work:** Métodos `_crear_cxp_inicial` y `_orquestar_ingreso_inventario` se ejecutan antes del `session.commit()` final de `registrar_compra`.
*   **Resultado:** Garantía ACID. Si falla inventario o CxP, la compra no se guarda.

### Motor Matemático de CxP y Bloqueos (E4-2)
*   **Archivo:** `src/osiris/modules/facturacion/cxp_service.py`
*   **Bloqueo:** `session.query(CuentaPorPagar).with_for_update()...`
*   **Validación:** `if monto_pago > saldo_actual: raise HTTPException(400)`
*   **Estados:** Lógica condicional correcta para transitar entre `PENDIENTE`, `PARCIAL` y `PAGADA`.

### Impacto de la Retención en la Deuda (E4-4)
*   **Archivo:** `src/osiris/modules/facturacion/retencion_service.py`
*   **Impacto:** `cxp.valor_retenido` se incrementa con el total de la retención.
*   **Recálculo:** `_actualizar_estado_cxp` ajusta el saldo (`total - retenido - pagos`) y el estado.

### Orquestación Asíncrona SRI (E4-5)
*   **Archivo:** `src/osiris/modules/facturacion/sri_async_service.py`
*   **Mecanismo:** `encolar_retencion` delega a `background_tasks.add_task` para evitar latencia en la respuesta HTTP. Implementa reintentos exponenciales.

### Cobertura de Pruebas (TDD)
*   **Archivo:** `tests/test_retencion_cxp_flujo.py`
*   **Validación:** El test simula una compra de $100, retención de $10 y pago de $90, verificando que el saldo final sea $0.00 y el estado `PAGADA`.
