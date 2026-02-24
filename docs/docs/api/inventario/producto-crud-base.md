---
id: producto-crud-base
title: "Producto: CRUD Base"
sidebar_position: 5
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Producto: CRUD Base

Este documento cubre únicamente el CRUD base de `producto`:
- `GET /api/v1/productos`
- `GET /api/v1/productos/{id}`
- `POST /api/v1/productos`
- `PUT /api/v1/productos/{id}`
- `DELETE /api/v1/productos/{id}`

---

## GET `/api/v1/productos`

Listado **liviano** para grillas y búsquedas rápidas. Devuelve metadata base y paginación, sin resolver el detalle completo de relaciones.

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "limit": 50,
  "offset": 0,
  "only_active": true
}
```

  </TabItem>
  <TabItem value="response200" label="Response 200">

```json
{
  "items": [
    {
      "id": "9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa",
      "nombre": "Laptop Gamer X",
      "tipo": "BIEN",
      "pvp": "2999.00",
      "cantidad": 0
    }
  ],
  "meta": {
    "total": 1,
    "limit": 50,
    "offset": 0,
    "page": 1,
    "page_count": 1
  }
}
```

  </TabItem>
</Tabs>

### Diccionario de Datos - GET `/api/v1/productos`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `limit` | int | No | min 1, max 1000, default 50 |
| `offset` | int | No | min 0, default 0 |
| `only_active` | bool | No | default true |
| `items[].id` | UUID | Sí | PK |
| `items[].nombre` | string | Sí | max 255, unique |
| `items[].tipo` | enum | Sí | `BIEN` \| `SERVICIO` |
| `items[].pvp` | decimal | Sí | escala monetaria |
| `items[].cantidad` | int | Sí | default 0 |
| `meta.total` | int | Sí | total registros |
| `meta.limit` | int | Sí | tamaño página |
| `meta.offset` | int | Sí | desplazamiento |
| `meta.page` | int | Sí | página calculada |
| `meta.page_count` | int | Sí | total páginas |

---

## GET `/api/v1/productos/{id}`

Obtiene el detalle completo del producto. Este endpoint sí trae composición completa (casa comercial, categorías, proveedores, impuestos, bodegas) y estructura de atributos con herencia por categorías.

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "id": "9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa"
}
```

  </TabItem>
  <TabItem value="response200" label="Response 200">

```json
{
  "id": "9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa",
  "nombre": "Laptop Gamer X",
  "tipo": "BIEN",
  "pvp": "2999.00",
  "cantidad": 0,
  "casa_comercial": {
    "nombre": "Casa ACME"
  },
  "categorias": [
    {
      "id": "3d3a9558-ec2f-4a11-95ce-ccf00f9ce2a9",
      "nombre": "Laptops"
    }
  ],
  "proveedores_persona": [],
  "proveedores_sociedad": [],
  "atributos": [
    {
      "atributo": {
        "id": "2a2bf5b8-e95e-4f6b-850d-c3ec4ce7c38f",
        "nombre": "Color",
        "tipo_dato": "string"
      },
      "valor": "Negro",
      "obligatorio": true,
      "orden": 1
    }
  ],
  "impuestos": [
    {
      "nombre": "IVA 15%",
      "codigo": "2",
      "porcentaje": "15.00"
    }
  ],
  "bodegas": [
    {
      "codigo_bodega": "BOD-MATRIZ",
      "nombre_bodega": "Bodega Matriz"
    }
  ]
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Producto no encontrado"
}
```

  </TabItem>
</Tabs>

### Diccionario de Datos - GET `/api/v1/productos/{id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `id` | UUID | Sí | path param |
| `nombre` | string | Sí | max 255, unique |
| `tipo` | enum | Sí | `BIEN` \| `SERVICIO` |
| `pvp` | decimal | Sí | escala monetaria |
| `cantidad` | int | Sí | default 0 |
| `casa_comercial` | object/null | No | objeto anidado |
| `categorias` | list | Sí | categorías del producto |
| `proveedores_persona` | list | Sí | proveedores persona |
| `proveedores_sociedad` | list | Sí | proveedores sociedad |
| `atributos` | list | Sí | detalle con herencia por categoría |
| `impuestos` | list | Sí | impuestos aplicados |
| `bodegas` | list | Sí | disponibilidad por bodega |

---

## POST `/api/v1/productos`

Crea un producto nuevo y retorna el contrato completo.

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "nombre": "Laptop Gamer X",
  "descripcion": "Portátil de alto rendimiento",
  "codigo_barras": "1234567890123",
  "tipo": "BIEN",
  "pvp": "2999.00",
  "casa_comercial_id": "6fc4e4d7-bf58-4eb3-a1db-1977e09e0f8e",
  "categoria_ids": [
    "3d3a9558-ec2f-4a11-95ce-ccf00f9ce2a9"
  ],
  "impuesto_catalogo_ids": [
    "bb8ad8d6-ecf3-4f3d-9f0d-b5a6d4d3f2c1"
  ],
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response201" label="Response 201">

```json
{
  "id": "9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa",
  "nombre": "Laptop Gamer X",
  "tipo": "BIEN",
  "pvp": "2999.00",
  "cantidad": 0,
  "casa_comercial": {
    "nombre": "Casa ACME"
  },
  "categorias": [],
  "proveedores_persona": [],
  "proveedores_sociedad": [],
  "atributos": [],
  "impuestos": [],
  "bodegas": []
}
```

  </TabItem>
  <TabItem value="response400" label="Response 400">

```json
{
  "detail": "El PVP debe ser mayor que cero"
}
```

```json
{
  "detail": "Solo se permiten categorías hoja (sin hijos) para el producto."
}
```

```json
{
  "detail": "Debe incluir exactamente un impuesto de tipo IVA. Los productos siempre deben tener IVA."
}
```

  </TabItem>
</Tabs>

### Diccionario de Datos - POST `/api/v1/productos`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `nombre` | string | Sí | max 255, unique |
| `descripcion` | string/null | No | max 1000 |
| `codigo_barras` | string/null | No | max 100 |
| `tipo` | enum | No | default `BIEN`; `BIEN` \| `SERVICIO` |
| `pvp` | decimal | Sí | **debe ser > 0**, redondeado a 2 decimales |
| `casa_comercial_id` | UUID/null | No | FK válida y activa |
| `categoria_ids` | UUID[]/null | No | si se envía, categorías hoja |
| `impuesto_catalogo_ids` | UUID[] | Sí | obligatorio; impuestos activos; IVA obligatorio; sin duplicar tipo de impuesto |
| `usuario_auditoria` | string/null | No | auditoría |

### Validaciones de negocio (POST)

- `tipo`: solo valores del enum `TipoProducto`.
- `pvp`: validación positiva y normalización a 2 decimales.
- `casa_comercial_id`: validación FK por servicio base.
- `categoria_ids`: solo categorías hoja (sin hijos).
- `impuesto_catalogo_ids`: al menos un IVA, impuestos existentes/activos, y sin repetir tipo de impuesto.

---

## PUT `/api/v1/productos/{id}`

Actualiza parcialmente un producto y retorna el contrato completo.

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "nombre": "Laptop Gamer X Pro",
  "tipo": "BIEN",
  "pvp": "3199.90",
  "casa_comercial_id": "6fc4e4d7-bf58-4eb3-a1db-1977e09e0f8e",
  "categoria_ids": [
    "3d3a9558-ec2f-4a11-95ce-ccf00f9ce2a9"
  ],
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response200" label="Response 200">

```json
{
  "id": "9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa",
  "nombre": "Laptop Gamer X Pro",
  "tipo": "BIEN",
  "pvp": "3199.90",
  "cantidad": 0,
  "casa_comercial": {
    "nombre": "Casa ACME"
  },
  "categorias": [],
  "proveedores_persona": [],
  "proveedores_sociedad": [],
  "atributos": [],
  "impuestos": [],
  "bodegas": []
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Producto 9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa no encontrado"
}
```

  </TabItem>
</Tabs>

### Diccionario de Datos - PUT `/api/v1/productos/{id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `id` | UUID | Sí | path param |
| `nombre` | string/null | No | max 255, unique |
| `descripcion` | string/null | No | max 1000 |
| `codigo_barras` | string/null | No | max 100 |
| `tipo` | enum/null | No | `BIEN` \| `SERVICIO` |
| `pvp` | decimal/null | No | si se envía, **debe ser > 0**, redondeo 2 decimales |
| `casa_comercial_id` | UUID/null | No | FK válida y activa |
| `categoria_ids` | UUID[]/null | No | si se envía, categorías hoja |
| `usuario_auditoria` | string/null | No | auditoría |

### Validaciones de negocio (PUT)

- `tipo`: enum `TipoProducto`.
- `pvp`: si se envía, debe ser mayor que cero.
- `casa_comercial_id`: validación FK por servicio base.
- `categoria_ids`: si se envían, deben ser categorías hoja.

---

## DELETE `/api/v1/productos/{id}`

Eliminación lógica del producto (`activo=false`).

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "id": "9c4a9ec6-4e3f-4f7a-8f1a-bf6f7ad0f1aa"
}
```

  </TabItem>
  <TabItem value="response204" label="Response 204">

```json
null
```

  </TabItem>
</Tabs>

### Diccionario de Datos - DELETE `/api/v1/productos/{id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `id` | UUID | Sí | path param |
| `status_code` | int | Sí | 204 sin cuerpo |
| `activo` | bool | Sí | soft delete |
