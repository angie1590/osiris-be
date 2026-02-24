---
id: producto-atributos-impuestos-bodegas
title: "Producto: Atributos EAV, Impuestos y Bodegas"
sidebar_position: 1
---

import Tabs from "@theme/Tabs";
import TabItem from "@theme/TabItem";

# Producto: Atributos EAV, Impuestos y Bodegas

PUT /api/v1/productos/\{producto_id\}/atributos
Proposito: Upsert de valores EAV del producto. Valida que cada atributo sea aplicable a las categorias actuales del producto y que el valor sea compatible con su tipo de dato. Si existe un valor previo del atributo, lo reemplaza; si no existe, lo crea.

<Tabs>
<TabItem value="request" label="Request">

Path params:
- producto_id (UUID)

Body (JSON):
```json
[
  {
    "atributo_id": "UUID",
    "valor": "string | int | decimal | bool | date(YYYY-MM-DD)"
  }
]
```

</TabItem>
<TabItem value="response" label="Response 200">

Body (JSON):
```json
[
  {
    "id": "UUID",
    "producto_id": "UUID",
    "atributo_id": "UUID",
    "valor_string": "string | null",
    "valor_integer": 0,
    "valor_decimal": "0.00",
    "valor_boolean": true,
    "valor_date": "YYYY-MM-DD",
    "activo": true,
    "creado_en": "YYYY-MM-DDTHH:MM:SS",
    "actualizado_en": "YYYY-MM-DDTHH:MM:SS",
    "usuario_auditoria": "string | null"
  }
]
```

</TabItem>
</Tabs>

Diccionario de Datos
- producto_id: Identificador del producto a actualizar.
- atributo_id: Identificador del atributo EAV.
- valor: Valor crudo a tipar segun el tipo de dato del atributo (STRING, INTEGER, DECIMAL, BOOLEAN, DATE). No se acepta null.
- valor_string/valor_integer/valor_decimal/valor_boolean/valor_date: Columna tipada persistida; solo una debe venir con valor.
- activo: Indica si el registro de valor esta vigente.
- creado_en/actualizado_en: Timestamps de auditoria.
- usuario_auditoria: Usuario responsable del cambio, si se provee en el backend.

Nota critica EAV (errores 400):
- 400 por no aplicabilidad: `El atributo {nombre} ({atributo_id}) no aplica a las categorias actuales del producto.`
- 400 por tipo incompatible: `Valor incompatible para el atributo {nombre}. Se esperaba un tipo {tipo}.`
- Frontend debe interpretar 400 como error de validacion de atributos y NO asumir actualizacion parcial. Debe renderizar el mensaje exacto devuelto en `detail`, y asociarlo al atributo correspondiente: use el `atributo_id` embebido en el texto (o el nombre) para marcar el campo y mostrar el error inline. Si no logra mapearlo, muestre el mensaje como error global de formulario y mantenga los valores previos.

POST /api/v1/productos/\{producto_id\}/impuestos
Proposito: Asigna un impuesto de catalogo a un producto. Valida existencia/activo del producto e impuesto, vigencia del impuesto, compatibilidad por tipo de producto y evita duplicados. Si ya existe un impuesto del mismo tipo, se inactiva y se reemplaza por el nuevo.

<Tabs>
<TabItem value="request" label="Request">

Path params:
- producto_id (UUID)

Query params:
- impuesto_catalogo_id (UUID)
- usuario_auditoria (string)

Body: vacio.

</TabItem>
<TabItem value="response" label="Response 201">

Body (JSON):
```json
{
  "id": "UUID",
  "producto_id": "UUID",
  "impuesto_catalogo_id": "UUID",
  "codigo_impuesto_sri": "string",
  "codigo_porcentaje_sri": "string",
  "tarifa": "0.0000",
  "activo": true,
  "creado_en": "YYYY-MM-DDTHH:MM:SS",
  "actualizado_en": "YYYY-MM-DDTHH:MM:SS",
  "usuario_auditoria": "string | null",
  "impuesto": {
    "id": "UUID",
    "tipo_impuesto": "IVA | ICE | IRBPNR",
    "codigo_tipo_impuesto": "2 | 3 | 5",
    "codigo_sri": "string",
    "descripcion": "string",
    "vigente_desde": "YYYY-MM-DD",
    "vigente_hasta": "YYYY-MM-DD | null",
    "aplica_a": "BIEN | SERVICIO | AMBOS",
    "activo": true,
    "creado_en": "YYYY-MM-DDTHH:MM:SS",
    "actualizado_en": "YYYY-MM-DDTHH:MM:SS",
    "usuario_auditoria": "string | null",
    "porcentaje_iva": "0.00 | null",
    "clasificacion_iva": "string | null",
    "tarifa_ad_valorem": "0.00 | null",
    "tarifa_especifica": "0.00 | null",
    "modo_calculo_ice": "string | null",
    "unidad_base": "string | null"
  }
}
```

</TabItem>
</Tabs>

Diccionario de Datos
- producto_id: Producto al que se asigna el impuesto.
- impuesto_catalogo_id: Impuesto del catalogo a asignar.
- usuario_auditoria: Usuario responsable de la asignacion.
- codigo_impuesto_sri/codigo_porcentaje_sri: Codigos SRI que se copian del catalogo.
- tarifa: Tarifa principal resuelta segun tipo de impuesto (IVA usa porcentaje_iva, ICE usa tarifa_ad_valorem, otros 0).
- impuesto: Datos completos del catalogo si se encuentra disponible.

POST /api/v1/inventarios/movimientos
Proposito: Crea un movimiento de inventario en estado BORRADOR que define la asignacion de producto a bodega (via detalles). No afecta stock hasta confirmar.

<Tabs>
<TabItem value="request" label="Request">

Body (JSON):
```json
{
  "fecha": "YYYY-MM-DD",
  "bodega_id": "UUID",
  "tipo_movimiento": "INGRESO | EGRESO | TRANSFERENCIA | AJUSTE",
  "estado": "BORRADOR",
  "referencia_documento": "string | null",
  "motivo_ajuste": "string | null",
  "usuario_auditoria": "string | null",
  "detalles": [
    {
      "producto_id": "UUID",
      "cantidad": "0.0000 (> 0)",
      "costo_unitario": "0.0000 (>= 0)"
    }
  ]
}
```

</TabItem>
<TabItem value="response" label="Response 201">

Body (JSON):
```json
{
  "id": "UUID",
  "fecha": "YYYY-MM-DD",
  "bodega_id": "UUID",
  "tipo_movimiento": "INGRESO | EGRESO | TRANSFERENCIA | AJUSTE",
  "estado": "BORRADOR",
  "referencia_documento": "string | null",
  "motivo_ajuste": "string | null",
  "detalles": [
    {
      "id": "UUID",
      "movimiento_inventario_id": "UUID",
      "producto_id": "UUID",
      "cantidad": "0.0000",
      "costo_unitario": "0.0000"
    }
  ]
}
```

</TabItem>
</Tabs>

Diccionario de Datos
- bodega_id: Bodega a la que se asignaran los productos de los detalles.
- tipo_movimiento: Define si el movimiento es ingreso, egreso, transferencia o ajuste.
- estado: Siempre BORRADOR en la creacion; no afecta saldos.
- detalles[].producto_id: Producto a asignar a la bodega.
- detalles[].cantidad: Cantidad positiva del movimiento.
- detalles[].costo_unitario: Costo unitario usado para valoracion (>= 0).

POST /api/v1/inventarios/movimientos/\{movimiento_id\}/confirmar
Proposito: Confirma el movimiento creado, aplica locks y reglas anti-negativos y materializa el stock de producto-bodega. En AJUSTE, requiere motivo_ajuste.

<Tabs>
<TabItem value="request" label="Request">

Path params:
- movimiento_id (UUID)

Body (JSON):
```json
{
  "motivo_ajuste": "string | null",
  "usuario_auditoria": "string | null"
}
```

</TabItem>
<TabItem value="response" label="Response 200">

Body (JSON):
```json
{
  "id": "UUID",
  "fecha": "YYYY-MM-DD",
  "bodega_id": "UUID",
  "tipo_movimiento": "INGRESO | EGRESO | TRANSFERENCIA | AJUSTE",
  "estado": "CONFIRMADO",
  "referencia_documento": "string | null",
  "motivo_ajuste": "string | null",
  "detalles": [
    {
      "id": "UUID",
      "movimiento_inventario_id": "UUID",
      "producto_id": "UUID",
      "cantidad": "0.0000",
      "costo_unitario": "0.0000"
    }
  ]
}
```

</TabItem>
</Tabs>

Diccionario de Datos
- movimiento_id: Identificador del movimiento a confirmar.
- motivo_ajuste: Obligatorio cuando tipo_movimiento es AJUSTE.
- usuario_auditoria: Usuario autorizador; se registra en el movimiento.
- estado: Pasa de BORRADOR a CONFIRMADO.
- Reglas clave: solo confirma BORRADOR; no permite stock negativo en EGRESO/TRANSFERENCIA; en INGRESO crea stock si no existe.
