---
sidebar_position: 2
---

# Catálogo Dinámico (EAV)

## Visión general

En Osiris, los atributos de producto se modelan con un patrón **EAV fuertemente tipado**:

- Maestro de atributos: define `nombre` y `tipo_dato`.
- Relación categoría-atributo: define aplicabilidad por jerarquía, obligatoriedad, orden y defaults.
- Valores por producto: se persisten en `tbl_producto_atributo_valor` usando columnas tipadas:
  - `valor_string`
  - `valor_integer`
  - `valor_decimal`
  - `valor_boolean`
  - `valor_date`

Este modelo evita esquemas rígidos y permite extender catálogos sin alterar `tbl_producto`.

## Regla B3 (evolución de taxonomía)

Cuando una categoría hoja que ya tiene productos pasa a ser padre:

1. Se crea o reutiliza una subcategoría hija llamada `General`.
2. Se migran los productos de la categoría original a `General` en una transacción atómica.
3. El nodo original queda como padre sin romper la integridad del catálogo.

## Reglas de negocio

### Tipado fuerte y casting

En el upsert de atributos, cada `valor` se valida contra el `tipo_dato` del atributo maestro.

Mapeo de tipos:

- `STRING` -> `valor_string`
- `INTEGER` -> `valor_integer`
- `DECIMAL` -> `valor_decimal`
- `BOOLEAN` -> `valor_boolean`
- `DATE` -> `valor_date`

Si el valor no se puede convertir al tipo esperado, la API responde `HTTP 400`.

### Defaults seguros y backfill masivo

Si un atributo se vuelve obligatorio sin `valor_default`, se inyecta un default seguro:

- `STRING`: `"N/A"`
- `INTEGER`: `"0"`
- `DECIMAL`: `"0.00"`
- `BOOLEAN`: `"false"`
- `DATE`: fecha actual en formato `YYYY-MM-DD`

Luego se ejecuta backfill masivo SQL idempotente (sin loops en Python y sin pisar valores existentes).

### Ocultamiento lógico ante cambio de categorías

Si un producto cambia de familia de categoría:

- Los valores históricos previos **no se borran físicamente** de `tbl_producto_atributo_valor`.
- El endpoint de detalle reconstruye atributos aplicables con la nueva jerarquía y los no aplicables quedan ocultos.

## Guía de integración Frontend

### 1) Leer atributos aplicables de un producto

Endpoint:

```http
GET /api/v1/productos/{producto_id}
```

Respuesta de ejemplo (fragmento):

```json
{
  "id": "1c7fd8a8-8700-4ea2-8f8d-2b5f299275ca",
  "nombre": "Televisor 55",
  "tipo": "BIEN",
  "pvp": "999.00",
  "cantidad": 0,
  "categorias": [
    {
      "id": "87ca4b6c-cd85-4f29-a95b-8d093f7b2de2",
      "nombre": "Televisores"
    }
  ],
  "atributos": [
    {
      "atributo": {
        "id": "9bc11585-8add-4a13-bfa6-cd9491e7d2cf",
        "nombre": "Garantia",
        "tipo_dato": "string"
      },
      "valor": "24 meses",
      "obligatorio": true,
      "orden": 1
    },
    {
      "atributo": {
        "id": "5517f99c-8ff9-4064-a530-f83f0cb8f8f7",
        "nombre": "Resolucion",
        "tipo_dato": "string"
      },
      "valor": null,
      "obligatorio": false,
      "orden": 2
    }
  ]
}
```

Regla UI:

- Renderizar inputs desde `atributos`.
- Respetar `obligatorio` y `orden`.
- Si `valor` es `null`, mostrar campo vacío.

### 2) Guardar atributos EAV

Endpoint:

```http
PUT /api/v1/productos/{producto_id}/atributos
Content-Type: application/json
```

Payload esperado:

```json
[
  {
    "atributo_id": "9bc11585-8add-4a13-bfa6-cd9491e7d2cf",
    "valor": "24 meses"
  },
  {
    "atributo_id": "5517f99c-8ff9-4064-a530-f83f0cb8f8f7",
    "valor": "4K"
  }
]
```

Respuesta `200` (fragmento):

```json
[
  {
    "id": "4310e977-3b8a-4f8f-925b-d7cf64daf036",
    "producto_id": "1c7fd8a8-8700-4ea2-8f8d-2b5f299275ca",
    "atributo_id": "9bc11585-8add-4a13-bfa6-cd9491e7d2cf",
    "valor_string": "24 meses",
    "valor_integer": null,
    "valor_decimal": null,
    "valor_boolean": null,
    "valor_date": null,
    "activo": true
  }
]
```

## Manejo de errores UX/UI (HTTP 400)

### Error 1: atributo no aplicable

```json
{
  "detail": "El atributo Cilindrada (4f96d2d2-ec3e-4f4f-b6b3-9559f1774a0d) no aplica a las categorias actuales del producto."
}
```

### Error 2: tipo de dato incompatible

```json
{
  "detail": "Valor incompatible para el atributo Pulgadas. Se esperaba un tipo integer."
}
```

Recomendación Frontend:

- Parsear `detail`.
- Identificar atributo por nombre/id.
- Marcar input en rojo con mensaje contextual.
