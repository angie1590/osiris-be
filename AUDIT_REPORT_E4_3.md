# Reporte de Auditoría: Osiris Backend - Card E4-3 (Plantillas de Retención)

## Resumen Ejecutivo

**Estado Global: CUMPLE ✅**
La implementación cumple con todos los requerimientos de la Card E4-3. El motor de sugerencias utiliza bases imponibles correctas, el modelado es relacional y existe funcionalidad de "guardado inverso".

| Requisito | Estado | Detalle |
| :--- | :--- | :--- |
| **Modelado de Datos** | **CUMPLE** | Entidades `PlantillaRetencion` y `PlantillaRetencionDetalle` definidas y vinculadas. |
| **Sugeridor** | **CUMPLE** | Lógica aplica `% IVA` sobre `monto_iva` y `% RENTA` sobre `subtotal_sin_impuestos`. |
| **Guardado Inverso** | **CUMPLE** | Endpoint permite crear/actualizar plantilla automáticamente desde una retención manual. |
| **Auditoría** | **CUMPLE** | Entidades heredan de `BaseTable` (AuditMixin) y el servicio registra usuario auditor. |
| **TDD (Tests)** | **CUMPLE** | `test_sugerir_retencion_aplica_bases_correctas` valida matemáticamente los cálculos. |

---

## Detalles Técnicos y Hallazgos

### Modelado de Datos
*   **Archivo:** `src/osiris/modules/facturacion/entity.py`
*   **Estructura:** Relación 1:N entre `PlantillaRetencion` y `PlantillaRetencionDetalle`.
*   **Campos:** `codigo_retencion_sri`, `tipo` (Enum RENTA/IVA) y `porcentaje` (Decimal 7,4) presentes.

### Endpoint Sugeridor de Retenciones
*   **Archivo:** `src/osiris/modules/facturacion/retencion_service.py`
*   **Validación Matemática:**
    ```python
    base = q2(compra.monto_iva) if detalle.tipo == TipoRetencionSRI.IVA else q2(compra.subtotal_sin_impuestos)
    valor = q2(base * q2(detalle.porcentaje) / Decimal("100"))
    ```
    Confirma que la base Renta incluye 0% y 12/15% (al usar el subtotal global).

### Guardado Inverso
*   **Archivo:** `src/osiris/modules/facturacion/retencion_service.py`
*   **Método:** `guardar_plantilla_desde_retencion_digitada` realiza *soft-delete* de la plantilla anterior y crea una nueva vigente, simplificando la UX.

### Cobertura de Pruebas (TDD)
*   **Archivo:** `tests/test_retencion_service.py`
*   **Caso:** `test_sugerir_retencion_aplica_bases_correctas`.
*   **Verificación:** Compra de $100 + $12 IVA. Plantilla 1% Renta + 30% IVA.
    *   Retención Renta: $100 * 1% = $1.00.
    *   Retención IVA: $12 * 30% = $3.60.
    *   Total: $4.60. Test pasa exitosamente.
