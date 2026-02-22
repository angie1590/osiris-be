# Auditoría Técnica de Código - Osiris Backend

**Fecha:** 24 de Octubre de 2024
**Autor:** Jules (AI Staff Engineer)
**Repositorio:** https://github.com/angie1590/osiris-be.git

Este reporte detalla los hallazgos de la auditoría técnica profunda realizada sobre el código base de `osiris-be`. Se han clasificado los problemas por nivel de severidad y se proponen soluciones concretas para cada uno.

---

## 1. Fugas de Conexiones y Transacciones (Severidad CRÍTICA)

### A. Middleware Asíncrono Bloqueante en `main.py`
**Archivo:** `src/osiris/main.py`
**Líneas:** ~76-143 (`enforce_sensitive_access_control`)

**Problema:**
El middleware `enforce_sensitive_access_control` está definido como `async def`, pero realiza operaciones de base de datos síncronas bloqueantes (`log_unauthorized_access`, `is_user_authorized_for_rule`) dentro del bucle de eventos principal.
Esto **congela** todo el servidor FastAPI mientras espera la respuesta de la base de datos, anulando la concurrencia y degradando severamente el rendimiento bajo carga.

**Solución Propuesta:**
Ejecutar las operaciones de base de datos en un hilo separado usando `run_in_threadpool` o refactorizar las funciones de auditoría para que sean verdaderamente asíncronas (`async/await`) si la librería de base de datos lo soporta (SQLAlchemy con `AsyncSession`). Dado que se usa `Session` síncrona, `run_in_threadpool` es la solución inmediata.

```python
from fastapi.concurrency import run_in_threadpool

# ... dentro del middleware ...
await run_in_threadpool(log_unauthorized_access, security_session, ...)
```

### B. Falta de Atomicidad en Servicios CRUD Base
**Archivos:** `src/osiris/domain/repository.py`, `src/osiris/domain/service.py`, `src/osiris/modules/common/empresa/service.py`

**Problema:**
El método `BaseRepository.create` realiza un `session.commit()` inmediatamente después de `session.add(obj)`.
El método `BaseService.create` llama a `repo.create` y *luego* ejecuta el hook `on_created`.
En el caso de `EmpresaService.on_created`, se intenta crear una `Sucursal` por defecto. Si esta segunda operación falla, la `Empresa` ya ha sido persistida en la base de datos, dejando el sistema en un estado inconsistente (Empresa sin Sucursal Matriz).

**Solución Propuesta:**
Eliminar el `commit()` automático en `BaseRepository`. El control de la transacción debe residir en la capa de Servicio (`Service Layer`), utilizando el patrón "Unit of Work". El servicio debe orquestar todas las operaciones y realizar un único `commit()` al final.

```python
# En BaseRepository
def create(self, session: Session, obj: Any, commit: bool = True) -> Any:
    session.add(obj)
    if commit:
        session.commit()
    # ...
```

---

## 2. Tipos de Datos y Precisión Financiera (Severidad CRÍTICA)

### A. Uso de `float` en Campos Monetarios y de Impuestos
**Archivos:**
1.  `src/osiris/modules/common/empleado/entity.py`: `salario: float` (Línea ~22)
2.  `src/osiris/modules/common/tipo_cliente/entity.py`: `descuento: float` (Línea ~18)
3.  `src/osiris/modules/inventario/producto/models.py`: `porcentaje: float`
4.  `src/osiris/modules/inventario/producto/service.py`: `float(...)` explícito en cálculo de impuestos.

**Problema:**
El uso del tipo `float` de Python introduce errores de precisión de punto flotante (IEEE 754), inaceptables en sistemas financieros. Aunque la base de datos use `Numeric` o `Integer`, la manipulación en Python como `float` puede corromper los datos antes de guardarlos o al leerlos.
Adicionalmente, en `TipoCliente`, el campo `descuento` se define como `float` en Pydantic pero se mapea a una columna `Integer` en la base de datos, lo que causará truncamiento silencioso de decimales (ej. 10.5% -> 10%).

**Solución Propuesta:**
*   Cambiar todos los tipos `float` a `Decimal` de la librería estándar `decimal`.
*   Alinear el tipo de columna en base de datos para `TipoCliente.descuento` a `Numeric(5, 2)` si se requieren decimales, o mantener `Integer` pero tipar en Python como `int`.

```python
# Ejemplo Corrección Empleado
from decimal import Decimal
salario: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
```

---

## 3. SQLAlchemy 2.0 Estricto y Consultas N+1 (Severidad ALTA)

### A. Problema N+1 en Listado de Productos
**Archivo:** `src/osiris/modules/inventario/producto/service.py`
**Líneas:** `list_paginated_completo` (Línea ~238)

**Problema:**
El método `list_paginated_completo` itera sobre cada producto obtenido de la base de datos y llama a `self.get_producto_completo(session, producto.id)`.
A su vez, `get_producto_completo` realiza múltiples consultas separadas para obtener categorías, proveedores, atributos e impuestos.
Esto resulta en un patrón **N * M consultas**, donde listar 50 productos podría disparar cientos de consultas a la base de datos, degradando el rendimiento.

**Solución Propuesta:**
Utilizar "Eager Loading" de SQLAlchemy (`selectinload` o `joinedload`) en la consulta inicial para traer todas las relaciones necesarias en una sola ida a la base de datos (o pocas consultas optimizadas).

```python
stmt = select(Producto).options(
    selectinload(Producto.producto_categorias).selectinload(ProductoCategoria.categoria),
    selectinload(Producto.producto_impuestos),
    # ... otras relaciones
)
```

---

## 4. Bloqueo del Event Loop (Severidad CRÍTICA)

### A. Operaciones Bloqueantes en Middleware Async
**Referencia:** Ver punto 1.A.
Esta es una violación directa de la arquitectura asíncrona de FastAPI. El uso de `Session` síncrona dentro de funciones `async def` sin `run_in_threadpool` es un antipatrón grave que afecta la escalabilidad.

---

## 5. Pydantic V2 Deprecations (Severidad MEDIA)

**Estado:** Aprobado (con vigilancia).
El escaneo no detectó uso explícito de métodos deprecados de V1 (`.dict()`, `.json()`, `parse_obj()`). El código utiliza correctamente `model_dump()`, `model_validate()`, `ConfigDict` y `computed_field`.

**Recomendación:** Mantener el uso estricto de Pydantic V2 y evitar reintroducir patrones de V1.

---

## 6. Código Muerto y Limpieza (Severidad BAJA/MEDIA)

### A. Archivos y Bloques "Zombie"
1.  **Archivo:** `backup_before_refactor.sql` (Raíz del proyecto)
    *   **Problema:** Archivo de respaldo masivo en el repositorio. Aumenta el tamaño del repo y puede contener datos sensibles.
    *   **Solución:** Eliminar inmediatamente.
2.  **Archivo:** `src/osiris/domain/router.py`
    *   **Problema:** Método `patch_item` comentado.
    *   **Solución:** Borrar el código comentado.
3.  **Archivo:** `src/osiris/modules/common/persona/service.py`
    *   **Problema:** Método `update` comentado.
    *   **Solución:** Borrar el código comentado.

### B. Imports y Variables No Usadas
Herramientas de linting (`ruff`) detectaron **207 problemas**, mayormente imports no usados.
Ejemplos destacados:
*   `tests/test_empleado.py`: Importa `Empresa` y `Persona` sin usarlos.
*   `tests/test_movimiento_inventario.py`: Comparaciones booleanas redundantes (`== True`).
*   `tests/test_producto.py`: Variables asignadas no usadas (`out = ...`).

**Solución:** Ejecutar `ruff check . --fix` para limpiar automáticamente la mayoría de estos problemas.
