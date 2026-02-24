---
id: casa-comercial-bodega
title: "Casa Comercial y Bodega"
sidebar_position: 4
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Casa Comercial y Bodega

## Casa Comercial

### GET `/api/v1/casas-comerciales`

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
      "id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4",
      "nombre": "Casa ACME",
      "activo": true,
      "creado_en": "2026-02-24T10:00:00",
      "actualizado_en": "2026-02-24T10:00:00",
      "usuario_auditoria": "api"
    }
  ],
  "meta": {
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - GET `/api/v1/casas-comerciales`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `limit` | int | No | min 1, max 1000, default 50 |
| `offset` | int | No | min 0, default 0 |
| `only_active` | bool | No | default true |
| `items[].id` | UUID | Sí | PK |
| `items[].nombre` | string | Sí | unique, max 120 |
| `items[].activo` | bool | Sí | soft delete |
| `items[].creado_en` | datetime | Sí | auditoría |
| `items[].actualizado_en` | datetime | Sí | auditoría |
| `items[].usuario_auditoria` | string/null | No | auditoría |
| `meta.total` | int | Sí | total de registros |
| `meta.limit` | int | Sí | tamaño de página |
| `meta.offset` | int | Sí | desplazamiento |

### GET `/api/v1/casas-comerciales/{item_id}`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "item_id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4"
}
```

  </TabItem>
  <TabItem value="response200" label="Response 200">

```json
{
  "id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4",
  "nombre": "Casa ACME",
  "activo": true,
  "creado_en": "2026-02-24T10:00:00",
  "actualizado_en": "2026-02-24T10:00:00",
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Casa-comercial d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4 not found"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - GET `/api/v1/casas-comerciales/{item_id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `item_id` | UUID | Sí | path param |
| `id` | UUID | Sí | PK |
| `nombre` | string | Sí | unique, max 120 |
| `activo` | bool | Sí | soft delete |
| `creado_en` | datetime | Sí | auditoría |
| `actualizado_en` | datetime | Sí | auditoría |
| `usuario_auditoria` | string/null | No | auditoría |

### POST `/api/v1/casas-comerciales`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "nombre": "Casa ACME",
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response201" label="Response 201">

```json
{
  "id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4",
  "nombre": "Casa ACME",
  "activo": true,
  "creado_en": "2026-02-24T10:00:00",
  "actualizado_en": "2026-02-24T10:00:00",
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response409" label="Response 409">

```json
{
  "detail": "Registro duplicado: el valor de 'nombre' ya existe."
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - POST `/api/v1/casas-comerciales`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `nombre` | string | Sí | unique, max 120 |
| `usuario_auditoria` | string/null | No | auditoría |
| `id` | UUID | Sí | generado por sistema |
| `activo` | bool | Sí | default true |

### PUT `/api/v1/casas-comerciales/{item_id}`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "item_id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4",
  "body": {
    "nombre": "Casa ACME Actualizada",
    "usuario_auditoria": "api"
  }
}
```

  </TabItem>
  <TabItem value="response200" label="Response 200">

```json
{
  "id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4",
  "nombre": "Casa ACME Actualizada",
  "activo": true,
  "creado_en": "2026-02-24T10:00:00",
  "actualizado_en": "2026-02-24T10:10:00",
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Casa-comercial d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4 not found"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - PUT `/api/v1/casas-comerciales/{item_id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `item_id` | UUID | Sí | path param |
| `nombre` | string/null | No | unique, max 120 |
| `usuario_auditoria` | string/null | No | update parcial |
| `actualizado_en` | datetime | Sí | auditoría |

### DELETE `/api/v1/casas-comerciales/{item_id}`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "item_id": "d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4"
}
```

  </TabItem>
  <TabItem value="response204" label="Response 204">

```json
null
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Casa-comercial d0bdb05e-5f7a-40b5-b6db-9f10f9efe7a4 not found"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - DELETE `/api/v1/casas-comerciales/{item_id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `item_id` | UUID | Sí | path param |
| `status_code` | int | Sí | 204 sin cuerpo |
| `activo` | bool | Sí | pasa a false (soft delete) |

## Bodega

### GET `/api/v1/bodegas`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "skip": 0,
  "limit": 50,
  "empresa_id": "9f0de3b2-3b84-4f2f-9adf-c12b41f0a312",
  "sucursal_id": null
}
```

  </TabItem>
  <TabItem value="response" label="Response 200">

```json
[
  {
    "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6",
    "codigo_bodega": "BOD-MATRIZ",
    "nombre_bodega": "Bodega Matriz",
    "descripcion": "Bodega principal",
    "empresa_id": "9f0de3b2-3b84-4f2f-9adf-c12b41f0a312",
    "sucursal_id": null,
    "usuario_auditoria": "api",
    "activo": true,
    "creado_en": "2026-02-24T10:00:00",
    "actualizado_en": "2026-02-24T10:00:00"
  }
]
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - GET `/api/v1/bodegas`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `skip` | int | No | min 0, default 0 |
| `limit` | int | No | min 1, max 200, default 50 |
| `empresa_id` | UUID/null | No | filtro opcional |
| `sucursal_id` | UUID/null | No | filtro opcional |
| `[].id` | UUID | Sí | PK |
| `[].codigo_bodega` | string | Sí | max 20 |
| `[].nombre_bodega` | string | Sí | max 100 |
| `[].descripcion` | string/null | No | max 255 |
| `[].empresa_id` | UUID | Sí | FK tbl_empresa |
| `[].sucursal_id` | UUID/null | No | FK tbl_sucursal |
| `[].activo` | bool | Sí | listado retorna activos |
| `[].creado_en` | datetime | Sí | auditoría |
| `[].actualizado_en` | datetime | Sí | auditoría |
| `[].usuario_auditoria` | string/null | No | auditoría |

### GET `/api/v1/bodegas/{id}`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6"
}
```

  </TabItem>
  <TabItem value="response" label="Response 200">

```json
{
  "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6",
  "codigo_bodega": "BOD-MATRIZ",
  "nombre_bodega": "Bodega Matriz",
  "descripcion": "Bodega principal",
  "empresa_id": "9f0de3b2-3b84-4f2f-9adf-c12b41f0a312",
  "sucursal_id": null,
  "usuario_auditoria": "api",
  "activo": true,
  "creado_en": "2026-02-24T10:00:00",
  "actualizado_en": "2026-02-24T10:00:00"
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Bodega no encontrada"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - GET `/api/v1/bodegas/{id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `id` | UUID | Sí | path param |
| `codigo_bodega` | string | Sí | max 20 |
| `nombre_bodega` | string | Sí | max 100 |
| `descripcion` | string/null | No | max 255 |
| `empresa_id` | UUID | Sí | FK tbl_empresa |
| `sucursal_id` | UUID/null | No | FK tbl_sucursal |
| `activo` | bool | Sí | soft delete |
| `creado_en` | datetime | Sí | auditoría |
| `actualizado_en` | datetime | Sí | auditoría |
| `usuario_auditoria` | string/null | No | auditoría |

### POST `/api/v1/bodegas`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "codigo_bodega": "BOD-MATRIZ",
  "nombre_bodega": "Bodega Matriz",
  "descripcion": "Bodega principal",
  "empresa_id": "9f0de3b2-3b84-4f2f-9adf-c12b41f0a312",
  "sucursal_id": null,
  "usuario_auditoria": "api"
}
```

  </TabItem>
  <TabItem value="response201" label="Response 201">

```json
{
  "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6",
  "codigo_bodega": "BOD-MATRIZ",
  "nombre_bodega": "Bodega Matriz",
  "descripcion": "Bodega principal",
  "empresa_id": "9f0de3b2-3b84-4f2f-9adf-c12b41f0a312",
  "sucursal_id": null,
  "usuario_auditoria": "api",
  "activo": true,
  "creado_en": "2026-02-24T10:00:00",
  "actualizado_en": "2026-02-24T10:00:00"
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Empresa no encontrada"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - POST `/api/v1/bodegas`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `codigo_bodega` | string | Sí | max 20 |
| `nombre_bodega` | string | Sí | max 100 |
| `descripcion` | string/null | No | max 255 |
| `empresa_id` | UUID | Sí | FK obligatoria |
| `sucursal_id` | UUID/null | No | FK opcional |
| `usuario_auditoria` | string/null | No | el router usa "api" en servicio |
| `id` | UUID | Sí | generado por sistema |
| `activo` | bool | Sí | default true |

### PUT `/api/v1/bodegas/{id}`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6",
  "body": {
    "nombre_bodega": "Bodega Matriz Actualizada",
    "descripcion": "Bodega principal actualizada",
    "usuario_auditoria": "api"
  }
}
```

  </TabItem>
  <TabItem value="response200" label="Response 200">

```json
{
  "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6",
  "codigo_bodega": "BOD-MATRIZ",
  "nombre_bodega": "Bodega Matriz Actualizada",
  "descripcion": "Bodega principal actualizada",
  "empresa_id": "9f0de3b2-3b84-4f2f-9adf-c12b41f0a312",
  "sucursal_id": null,
  "usuario_auditoria": "api",
  "activo": true,
  "creado_en": "2026-02-24T10:00:00",
  "actualizado_en": "2026-02-24T10:10:00"
}
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Bodega no encontrada"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - PUT `/api/v1/bodegas/{id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `id` | UUID | Sí | path param |
| `codigo_bodega` | string/null | No | max 20 |
| `nombre_bodega` | string/null | No | max 100 |
| `descripcion` | string/null | No | max 255 |
| `sucursal_id` | UUID/null | No | FK opcional |
| `usuario_auditoria` | string/null | No | update parcial |
| `actualizado_en` | datetime | Sí | auditoría |

### DELETE `/api/v1/bodegas/{id}`

<Tabs>
  <TabItem value="request" label="Request" default>

```json
{
  "id": "cc723ad4-3f2f-4c25-8229-79a2755ab6f6"
}
```

  </TabItem>
  <TabItem value="response204" label="Response 204">

```json
null
```

  </TabItem>
  <TabItem value="response404" label="Response 404">

```json
{
  "detail": "Bodega no encontrada"
}
```

  </TabItem>
</Tabs>

#### Diccionario de Datos - DELETE `/api/v1/bodegas/{id}`

| Campo | Tipo | Requerido | Restricción |
|---|---|---|---|
| `id` | UUID | Sí | path param |
| `status_code` | int | Sí | 204 sin cuerpo |
| `activo` | bool | Sí | pasa a false (soft delete) |
