# Reporte de Auditoría: Osiris Backend - Épica 1 y Reglas RIMPE

## Resumen Ejecutivo

### ÉPICA 1: Parametrización SRI
**Estado Global: NO CUMPLE ❌**
Ninguna de las tarjetas auditadas de esta épica cumple con los requisitos críticos.

| Card | Estado | Fallo Principal |
| :--- | :--- | :--- |
| **E1-1 (Regímenes)** | **NO CUMPLE** | `Empresa` no tiene campos `regimen` ni `modo_emision`. No hay validación de compatibilidad. |
| **E1-2 (Secuenciales)** | **NO CUMPLE** | `PuntoEmisionService` carece de lógica de incremento atómico y bloqueo pesimista. |
| **E1-3 (Impuestos)** | **NO CUMPLE** | Módulo de Ventas/Facturas inexistente. Imposible verificar snapshot de impuestos. |

### CHECKLIST DE VALIDACIÓN RIMPE
**Estado Global: NO CUMPLE ❌**
La regla de negocio "Emisión Electrónica para RIMPE Negocio Popular" no está implementada.

| Validación | Estado | Detalle |
| :--- | :--- | :--- |
| **Bloqueo de IVA** | **NO CUMPLE** | No existen modelos de Venta para validar reglas de IVA (0% obligatorio). |
| **Actividad Excluida** | **NO CUMPLE** | No existe campo `es_actividad_excluida` para excepciones de IVA. |
| **Leyenda FE-EC** | **NO CUMPLE** | No se encontró servicio `fe_mapper` para inyectar leyenda en XML. |
| **Tests** | **NO CUMPLE** | No hay pruebas que cubran escenarios RIMPE vs IVA. |

---

## Detalles Técnicos y Correcciones Sugeridas

### Card E1-1: Regímenes SRI
*   **Archivo Revisado:** `src/osiris/modules/common/empresa/entity.py` (Línea 8-28)
*   **Problema:** Falta definición de campos y validadores.
*   **Corrección:**
    ```python
    # Entity
    regimen: str = Field(default="GENERAL", nullable=False)
    modo_emision: str = Field(default="ELECTRONICO", nullable=False)

    # Models Validator
    @model_validator(mode='after')
    def validar_regimen_modo(self):
        if self.modo_emision == "NOTA_VENTA_FISICA" and self.regimen != "RIMPE_NEGOCIO_POPULAR":
             raise ValueError("NOTA_VENTA_FISICA solo permitido para RIMPE_NEGOCIO_POPULAR")
        return self
    ```

### Card E1-2: Secuenciales
*   **Archivo Revisado:** `src/osiris/modules/common/punto_emision/service.py` (Línea 29-45)
*   **Problema:** Falta método transaccional seguro.
*   **Corrección:** Implementar `get_next_secuencial` usando `select(...).with_for_update()` y formateo `zfill(9)`.

### Card E1-3: Impuestos y FE-EC
*   **Archivo Revisado:** N/A (Módulos no existen)
*   **Problema:** Ausencia total del módulo de Ventas.
*   **Corrección:** Implementar `Venta` y `VentaDetalle`, asegurando que el detalle guarde un snapshot completo del impuesto (código, tarifa, porcentaje) y no solo una referencia.
