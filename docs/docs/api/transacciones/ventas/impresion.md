---
id: impresion
title: "Ventas: Impresión, Nota Preimpresa y Reimpresión Segura"
sidebar_position: 4
---

import Tabs from "@theme/Tabs";
import TabItem from "@theme/TabItem";

# Ventas: Impresión, Nota Preimpresa y Reimpresión Segura

## Endpoints

| Endpoint | Proposito |
|---|---|
| `GET /api/v1/impresion/documento/{documento_id}/a4` | Generar RIDE A4 (PDF) |
| `GET /api/v1/impresion/documento/{documento_id}/ticket` | Generar ticket térmico (HTML) |
| `GET /api/v1/impresion/documento/{documento_id}/preimpresa` | Generar formato para nota de venta física preimpresa |
| `POST /api/v1/impresion/documento/{documento_id}/reimprimir` | Reimpresión controlada con auditoría |

## Reglas generales

- Solo se imprime/reimprime documento en estado SRI `AUTORIZADO`.
- Reimpresión requiere usuario autenticado con rol:
  - `CAJERO`, `ADMIN`, `ADMINISTRADOR`.
- Toda reimpresión incrementa contador en documento/venta y deja `AuditLog`.

---

`GET /api/v1/impresion/documento/{documento_id}/a4`
Proposito: devuelve PDF A4 para RIDE.

Response esperada:

- `200` con `Content-Type: application/pdf`.
- `404` documento inexistente.
- `400` documento no autorizado.

---

`GET /api/v1/impresion/documento/{documento_id}/ticket`
Proposito: genera ticket térmico HTML para impresión del frontend.

Query params:

| Param | Valores |
|---|---|
| `ancho` | `58mm` \| `80mm` (default `80mm`) |

Incluye:

- totales,
- total pagado,
- efectivo y cambio,
- clave de acceso.

---

`GET /api/v1/impresion/documento/{documento_id}/preimpresa`
Proposito: genera formato de nota de venta física preimpresa (sin encabezado tributario completo).

Query params:

| Param | Valores |
|---|---|
| `formato` | `HTML` \| `PDF` (default `HTML`) |

Usa configuración por punto de emisión (`config_impresion`):

- `margen_superior_cm`
- `max_items_por_pagina`

Si se excede el máximo de ítems por página, retorna warning en header:

- `X-Impresion-Warning`

---

`POST /api/v1/impresion/documento/{documento_id}/reimprimir`
Proposito: reimprime con traza de auditoría.

<Tabs>
<TabItem value="request" label="Request">

```json
{
  "motivo": "Se atascó el papel",
  "formato": "A4"
}
```

`formato` admite:

- `A4`
- `TICKET_80MM`
- `TICKET_58MM`

</TabItem>
</Tabs>

Reglas:

1. valida rol autorizado.
2. incrementa `cantidad_impresiones` en `DocumentoElectronico` y `Venta`.
3. inserta evento `REIMPRESION_DOCUMENTO` en `AuditLog`.

## Integración frontend recomendada

1. En vista de documento autorizado:
   - botón `Imprimir A4`,
   - botón `Imprimir Ticket`.
2. Para nota física:
   - usar endpoint `preimpresa`,
   - mostrar warning de paginación si llega `X-Impresion-Warning`.
3. Para reimpresión:
   - pedir motivo obligatorio en modal.
   - mostrar historial de reimpresiones (cuando exista endpoint de consulta de auditoría en UI).

## Dependencias de renderizado (runtime)

- Jinja2 (plantillas HTML).
- WeasyPrint (PDF real). Si falta, el backend aplica fallback PDF mínimo.
- python-barcode (código de barras para clave acceso). Si falta, usa fallback SVG textual.

## Preguntas para cierre de front (si aplica)

1. ¿La impresión térmica será manejada por navegador (`window.print`) o spooler local?
2. ¿Necesitan endpoint para listar historial de reimpresiones por documento?
