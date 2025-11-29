from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from osiris.core.db import engine
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.categoria.entity import Categoria
from osiris.modules.common.persona.entity import Persona
from osiris.modules.common.proveedor_persona.entity import ProveedorPersona
from osiris.modules.common.proveedor_sociedad.entity import ProveedorSociedad
from osiris.modules.inventario.atributo.entity import Atributo
from osiris.modules.inventario.producto.entity import (
    Producto,
    ProductoCategoria,
    ProductoProveedorPersona,
    ProductoProveedorSociedad,
)
from osiris.modules.inventario.tipo_producto.entity import TipoProducto
from osiris.modules.aux.impuesto_catalogo.entity import (
    ImpuestoCatalogo,
    TipoImpuesto,
    AplicaA,
    ClasificacionIVA,
    ModoCalculoICE,
    UnidadBase,
)
from osiris.modules.aux.tipo_contribuyente.entity import TipoContribuyente
from osiris.modules.inventario.producto.service import ProductoService
from osiris.modules.inventario.producto.models import ProductoCreate

USUARIO = "seed"

# Datos de entrada (pueden personalizarse)
RUC_PERSONAS = [
    "0104815956001",
    "0103523908001",
]
RUC_PERSONAS_EXTRA = ["0102637063001", "0102522778001"]  # disponibles si se quieren más

RUC_SOCIEDADES = [
    "0990828237001",
    "0990005419001",
]
RUC_SOCIEDADES_EXTRA = ["1791148800001", "1792128218001"]


def get_or_create(session: Session, model, defaults: dict, **filters):
    obj = session.exec(select(model).filter_by(**filters)).first()
    if obj:
        return obj, False
    obj = model(**{**filters, **defaults})
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj, True


def seed():
    with Session(engine) as session:
        # Casa comercial
        casa, _ = get_or_create(session, CasaComercial, {"nombre": "Casa ACME", "usuario_auditoria": USUARIO}, nombre="Casa ACME")

        # Catálogo tipo contribuyente (01 Persona Natural, 02 Sociedad)
        get_or_create(session, TipoContribuyente, {"nombre": "Persona Natural", "descripcion": "Persona natural", "activo": True}, codigo="01")
        get_or_create(session, TipoContribuyente, {"nombre": "Sociedad", "descripcion": "Sociedad", "activo": True}, codigo="02")

        # Categorías (Tecnología > Computadoras > Laptop)
        tech, _ = get_or_create(session, Categoria, {"es_padre": True, "parent_id": None, "usuario_auditoria": USUARIO}, nombre="Tecnología")
        comp, _ = get_or_create(session, Categoria, {"es_padre": True, "parent_id": tech.id, "usuario_auditoria": USUARIO}, nombre="Computadoras")
        laptop, _ = get_or_create(session, Categoria, {"es_padre": False, "parent_id": comp.id, "usuario_auditoria": USUARIO}, nombre="Laptop")

        # Personas y proveedores persona
        proveedores_persona_ids = []
        persona_data = [
            (RUC_PERSONAS[0], "Juan", "Gómez", "Juan Gómez Importaciones"),
            (RUC_PERSONAS[1], "Pepe", "Pérez", "Tecnologías Pepe"),
        ]
        for identificacion, nombre, apellido, nombre_comercial in persona_data:
            persona, _ = get_or_create(
                session,
                Persona,
                {
                    "tipo_identificacion": "RUC",
                    "nombre": nombre,
                    "apellido": apellido,
                    "usuario_auditoria": USUARIO,
                },
                identificacion=identificacion,
            )
            proveedor, _ = get_or_create(
                session,
                ProveedorPersona,
                {
                    "tipo_contribuyente_id": "01",  # Persona natural
                    "persona_id": persona.id,
                    "nombre_comercial": nombre_comercial,
                    "usuario_auditoria": USUARIO,
                },
                persona_id=persona.id,
            )
            proveedores_persona_ids.append(proveedor.id)

        # Proveedores sociedad (usar la primera persona como contacto)
        contacto_persona = session.exec(select(Persona).filter(Persona.identificacion == RUC_PERSONAS[0])).first()
        proveedores_sociedad_ids = []
        sociedades_data = [
            (RUC_SOCIEDADES[0], "Tipti S.A.", "Tipti"),
            (RUC_SOCIEDADES[1], "ABC Comercial S.A.", "ABC Comercial"),
        ]
        for ruc, razon_social, nombre_comercial in sociedades_data:
            prov_soc, _ = get_or_create(
                session,
                ProveedorSociedad,
                {
                    "razon_social": razon_social,
                    "nombre_comercial": nombre_comercial,
                    "direccion": "Av. Principal 123",
                    "telefono": "0999999999",
                    "email": f"{nombre_comercial.lower().replace(' ', '_')}@example.com",
                    "tipo_contribuyente_id": "02",  # Sociedad
                    "persona_contacto_id": contacto_persona.id,
                    "usuario_auditoria": USUARIO,
                },
                ruc=ruc,
            )
            proveedores_sociedad_ids.append(prov_soc.id)

        # Atributos
        atributos_data = [
            ("color_principal", "string", "negro"),
            ("memoria_ram", "string", "32GB"),
            ("tamano_pantalla", "decimal", "15.6"),
        ]
        atributo_ids = []
        for nombre, tipo_dato, valor in atributos_data:
            atributo, _ = get_or_create(
                session,
                Atributo,
                {"tipo_dato": tipo_dato, "usuario_auditoria": USUARIO},
                nombre=nombre,
            )
            atributo_ids.append((atributo.id, valor))

        # Obtener impuestos del catálogo SRI ya insertados por migración
        # IVA 15% (codigo_sri="4")
        iva = session.exec(
            select(ImpuestoCatalogo).where(
                ImpuestoCatalogo.codigo_sri == "4",
                ImpuestoCatalogo.tipo_impuesto == TipoImpuesto.IVA
            )
        ).first()
        if not iva:
            raise RuntimeError("No se encontró IVA 15% (codigo_sri=4) en el catálogo. Ejecutar migraciones primero.")

        # ICE ejemplo: Cigarrillos Rubios (codigo_sri="3011")
        ice = session.exec(
            select(ImpuestoCatalogo).where(
                ImpuestoCatalogo.codigo_sri == "3011",
                ImpuestoCatalogo.tipo_impuesto == TipoImpuesto.ICE
            )
        ).first()
        if not ice:
            raise RuntimeError("No se encontró ICE (codigo_sri=3011) en el catálogo. Ejecutar migraciones primero.")

        session.commit()

        # Producto principal (verificar si existe o crearlo con servicio)
        producto = session.exec(select(Producto).where(Producto.nombre == "Laptop Gamer X Pro")).first()
        if not producto:
            prod_service = ProductoService()
            producto_data = ProductoCreate(
                nombre="Laptop Gamer X Pro",
                tipo="BIEN",
                pvp=Decimal("2999.00"),
                casa_comercial_id=casa.id,
                impuesto_catalogo_ids=[iva.id, ice.id],  # OBLIGATORIO: incluir impuestos
            )
            producto = prod_service.create(session, producto_data, USUARIO)
        created = producto is not None

        # Asociaciones categorías (solo laptop hoja)
        if not session.exec(
            select(ProductoCategoria).where(
                ProductoCategoria.producto_id == producto.id,
                ProductoCategoria.categoria_id == laptop.id,
            )
        ).first():
            session.add(ProductoCategoria(producto_id=producto.id, categoria_id=laptop.id))

        # Asociaciones proveedores persona
        for pid in proveedores_persona_ids:
            if not session.exec(
                select(ProductoProveedorPersona).where(
                    ProductoProveedorPersona.producto_id == producto.id,
                    ProductoProveedorPersona.proveedor_persona_id == pid,
                )
            ).first():
                session.add(ProductoProveedorPersona(producto_id=producto.id, proveedor_persona_id=pid))

        # Asociaciones proveedores sociedad
        for sid in proveedores_sociedad_ids:
            if not session.exec(
                select(ProductoProveedorSociedad).where(
                    ProductoProveedorSociedad.producto_id == producto.id,
                    ProductoProveedorSociedad.proveedor_sociedad_id == sid,
                )
            ).first():
                session.add(ProductoProveedorSociedad(producto_id=producto.id, proveedor_sociedad_id=sid))

        session.commit()

        # Asociar atributos (TipoProducto con valor)
        for atributo_id, valor in atributo_ids:
            tp = session.exec(
                select(TipoProducto).where(
                    TipoProducto.producto_id == producto.id,
                    TipoProducto.atributo_id == atributo_id,
                )
            ).first()
            if not tp:
                tp = TipoProducto(producto_id=producto.id, atributo_id=atributo_id, valor=valor, usuario_auditoria=USUARIO)
                session.add(tp)
            else:
                tp.valor = valor
        session.commit()

        # Construir salida usando el servicio principal
        if 'prod_service' not in locals():
            prod_service = ProductoService()
        resultado = prod_service.get_producto_completo(session, producto.id)

        print("=== Producto completo seed ===")
        from json import dumps
        # Serialización segura (UUIDs y Decimals) usando Pydantic v2
        try:
            payload = resultado.model_dump(mode="json")
        except Exception:
            # Fallback genérico convirtiendo cualquier objeto no serializable a str
            from fastapi.encoders import jsonable_encoder
            payload = jsonable_encoder(resultado)
        print(dumps(payload, indent=2, ensure_ascii=False))
        print("ID del producto:", producto.id)
        print("Ejemplo de uso: GET /api/productos/", producto.id)


if __name__ == "__main__":
    seed()
