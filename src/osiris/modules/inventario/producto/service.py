from __future__ import annotations

from typing import Iterable, Optional
from uuid import UUID

from sqlmodel import Session, select

from osiris.core.errors import NotFoundError
from osiris.domain.service import BaseService
from osiris.modules.inventario.categoria.entity import Categoria  # existente
from osiris.modules.inventario.tipo_producto.entity import TipoProducto
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.producto_impuesto.service import ProductoImpuestoService
from osiris.modules.aux.impuesto_catalogo.entity import ImpuestoCatalogo
from fastapi import HTTPException
from .repository import ProductoRepository
from .entity import (
    Producto,
    ProductoCategoria,
    ProductoProveedorPersona,
    ProductoProveedorSociedad,
    ProductoImpuesto,
)

class ProductoService(BaseService):
    repo = ProductoRepository()

    # Validación de FKs estándar (existencia/activo) para casa comercial
    fk_models = {
        "casa_comercial_id": CasaComercial,
    }

    def _validate_leaf_categories(self, session: Session, categoria_ids: Iterable[UUID]) -> None:
        if not categoria_ids:
            return
        for cid in categoria_ids:
            # una categoría es hoja si no tiene hijos
            has_children = session.exec(select(Categoria).where(Categoria.parent_id == cid)).first() is not None
            if has_children:
                raise HTTPException(status_code=400, detail="Solo se permiten categorías hoja (sin hijos) para el producto.")

    def _validate_impuestos(self, session: Session, impuesto_ids: Iterable[UUID], tipo_producto) -> None:
        """
        Valida que:
        1. Solo haya un impuesto de cada tipo (IVA, ICE, IRBPNR)
        2. Al menos un IVA esté presente (obligatorio según SRI)
        3. Los impuestos existan y estén activos
        4. Sean compatibles con el tipo de producto
        """
        if not impuesto_ids:
            raise HTTPException(status_code=400, detail="Debe incluir al menos un impuesto IVA.")

        tipos_vistos = set()
        tiene_iva = False

        for imp_id in impuesto_ids:
            # Verificar que el impuesto existe y está activo
            impuesto = session.get(ImpuestoCatalogo, imp_id)
            if not impuesto or not impuesto.activo:
                raise HTTPException(status_code=400, detail=f"El impuesto {imp_id} no existe o está inactivo.")

            # Validar que no se repita el tipo de impuesto
            tipo_impuesto = impuesto.tipo_impuesto
            if tipo_impuesto in tipos_vistos:
                raise HTTPException(
                    status_code=400,
                    detail=f"Solo se permite un impuesto de tipo {tipo_impuesto.value} por producto."
                )
            tipos_vistos.add(tipo_impuesto)

            # Verificar que hay al menos un IVA (comparar con el enum directamente)
            from osiris.modules.aux.impuesto_catalogo.entity import TipoImpuesto
            if tipo_impuesto == TipoImpuesto.IVA:
                tiene_iva = True

            # Validar compatibilidad con tipo de producto
            ProductoImpuestoService()._validar_compatibilidad_tipo(tipo_producto, impuesto.aplica_a)

        if not tiene_iva:
            raise HTTPException(
                status_code=400,
                detail="Debe incluir exactamente un impuesto de tipo IVA. Los productos siempre deben tener IVA."
            )

    def create(self, session: Session, data):
        def _val(obj, key):
            if obj is None:
                return None
            if hasattr(obj, "get"):
                try:
                    return obj.get(key)
                except Exception:
                    pass
            return getattr(obj, key, None)

        categoria_ids: Optional[Iterable[UUID]] = _val(data, "categoria_ids")
        self._validate_leaf_categories(session, categoria_ids or [])

        # Validar impuestos antes de crear el producto
        impuesto_ids: Optional[Iterable[UUID]] = _val(data, "impuesto_catalogo_ids")
        tipo_producto = _val(data, "tipo")
        if impuesto_ids:
            self._validate_impuestos(session, impuesto_ids, tipo_producto)

        prod = super().create(session, data)
        pid = prod.id

        # asociaciones
        if categoria_ids:
            self.repo.set_categorias(session, pid, categoria_ids)
        provp_ids = _val(data, "proveedor_persona_ids")
        if provp_ids:
            self.repo.set_proveedores_persona(session, pid, provp_ids)
        provs_ids = _val(data, "proveedor_sociedad_ids")
        if provs_ids:
            self.repo.set_proveedores_sociedad(session, pid, provs_ids)
        attr_ids = _val(data, "atributo_ids")
        usuario_auditoria = _val(data, "usuario_auditoria")
        if attr_ids:
            # reset tipo_producto para producto
            session.query(TipoProducto).filter(TipoProducto.producto_id == pid).delete()
            for aid in attr_ids:
                session.add(TipoProducto(producto_id=pid, atributo_id=aid, usuario_auditoria=usuario_auditoria))
            session.commit()

        # Asociar impuestos automáticamente
        if impuesto_ids:
            for imp_id in impuesto_ids:
                producto_impuesto = ProductoImpuesto(
                    producto_id=pid,
                    impuesto_catalogo_id=imp_id,
                    usuario_auditoria=usuario_auditoria
                )
                session.add(producto_impuesto)
            session.commit()

        return prod

    def update(self, session: Session, item_id: UUID, data):
        # validar categorías si vienen
        def _val(obj, key):
            if obj is None:
                return None
            if hasattr(obj, "get"):
                try:
                    return obj.get(key)
                except Exception:
                    pass
            return getattr(obj, key, None)

        categoria_ids = _val(data, "categoria_ids")
        if categoria_ids is not None:
            self._validate_leaf_categories(session, categoria_ids)
        prod = super().update(session, item_id, data)
        if prod is None:
            return None
        # asociaciones
        if categoria_ids is not None:
            self.repo.set_categorias(session, item_id, categoria_ids)
        provp_ids = _val(data, "proveedor_persona_ids")
        if provp_ids is not None:
            self.repo.set_proveedores_persona(session, item_id, provp_ids)
        provs_ids = _val(data, "proveedor_sociedad_ids")
        if provs_ids is not None:
            self.repo.set_proveedores_sociedad(session, item_id, provs_ids)
        attr_ids = _val(data, "atributo_ids")
        usuario_auditoria = _val(data, "usuario_auditoria")
        if attr_ids is not None:
            session.query(TipoProducto).filter(TipoProducto.producto_id == item_id).delete()
            for aid in attr_ids:
                session.add(TipoProducto(producto_id=item_id, atributo_id=aid, usuario_auditoria=usuario_auditoria))
            session.commit()
        return prod

    def get(self, session: Session, item_id: UUID):
        prod = super().get(session, item_id)
        if prod is None:
            raise NotFoundError("Producto no encontrado")
        return prod

    def get_with_impuestos(self, session: Session, item_id: UUID):
        """
        Obtiene un producto con su lista completa de impuestos incluida.
        Retorna tupla (producto, lista_impuestos).
        """
        prod = self.get(session, item_id)

        # Obtener impuestos del producto
        producto_impuesto_service = ProductoImpuestoService()
        impuestos = producto_impuesto_service.get_impuestos_completos(session, item_id)

        # Retornar tupla para que el router construya el response
        return prod, impuestos

    def _build_categoria_ruta(self, session: Session, categoria_id: UUID) -> str:
        """Construye la ruta completa de una categoría (ej: Tecnología > Computadoras > Laptop)"""
        from osiris.modules.inventario.categoria.entity import Categoria

        ruta_parts = []
        current_id = categoria_id

        while current_id:
            categoria = session.get(Categoria, current_id)
            if not categoria:
                break
            ruta_parts.insert(0, categoria.nombre)
            current_id = categoria.parent_id

        return " > ".join(ruta_parts)

    def get_producto_completo(self, session: Session, producto_id: UUID) -> dict:
        """Obtiene un producto con todas sus relaciones completas según contrato"""
        from osiris.modules.inventario.casa_comercial.entity import CasaComercial
        from osiris.modules.inventario.categoria.entity import Categoria
        from osiris.modules.common.proveedor_persona.entity import ProveedorPersona
        from osiris.modules.common.proveedor_sociedad.entity import ProveedorSociedad
        from osiris.modules.common.persona.entity import Persona
        from osiris.modules.inventario.atributo.entity import Atributo
        from osiris.modules.inventario.producto_impuesto.service import ProductoImpuestoService

        producto = self.get(session, producto_id)

        # Casa comercial
        casa_comercial = None
        if producto.casa_comercial_id:
            casa = session.get(CasaComercial, producto.casa_comercial_id)
            if casa:
                casa_comercial = {"nombre": casa.nombre}

        # Categorías con ruta
        categorias = []
        cat_ids = session.exec(
            select(ProductoCategoria.categoria_id)
            .where(ProductoCategoria.producto_id == producto_id)
        ).all()
        for cat_id in cat_ids:
            cat = session.get(Categoria, cat_id)
            if cat:
                categorias.append({
                    "id": cat.id,
                    "nombre": cat.nombre,
                })

        # Proveedores persona
        proveedores_persona = []
        prov_pers_ids = session.exec(
            select(ProductoProveedorPersona.proveedor_persona_id)
            .where(ProductoProveedorPersona.producto_id == producto_id)
        ).all()
        for prov_id in prov_pers_ids:
            prov = session.get(ProveedorPersona, prov_id)
            if prov:
                persona = session.get(Persona, prov.persona_id)
                if persona:
                    proveedores_persona.append({
                        "nombres": persona.nombre,
                        "apellidos": persona.apellido,
                        "nombre_comercial": getattr(prov, "nombre_comercial", None)
                    })

        # Proveedores sociedad
        proveedores_sociedad = []
        prov_soc_ids = session.exec(
            select(ProductoProveedorSociedad.proveedor_sociedad_id)
            .where(ProductoProveedorSociedad.producto_id == producto_id)
        ).all()
        for prov_id in prov_soc_ids:
            prov = session.get(ProveedorSociedad, prov_id)
            if prov:
                proveedores_sociedad.append({
                    "razon_social": prov.razon_social,
                    "nombre_comercial": getattr(prov, "nombre_comercial", None)
                })

        # Atributos con valores
        atributos = []
        tipo_prods = session.exec(
            select(TipoProducto, Atributo)
            .join(Atributo, Atributo.id == TipoProducto.atributo_id)
            .where(TipoProducto.producto_id == producto_id)
        ).all()
        for tipo_prod, atributo in tipo_prods:
            # Stringificar el valor según tipo_dato (ya almacenado como string/decimal)
            valor = tipo_prod.valor
            if valor is not None:
                valor = str(valor)
            atributos.append({
                "atributo": {
                    "nombre": atributo.nombre,
                },
                "valor": valor,
            })

        # Impuestos (resiliente: si algo falla, lista vacía)
        impuestos = []
        try:
            impuesto_service = ProductoImpuestoService()
            impuestos_raw = impuesto_service.get_impuestos_completos(session, producto_id)
            for imp in impuestos_raw:
                porcentaje_val = 0.0
                try:
                    # IVA usa porcentaje_iva, ICE usa tarifa_ad_valorem
                    porcentaje_val = float(imp.porcentaje_iva or imp.tarifa_ad_valorem or 0)
                except Exception:
                    porcentaje_val = 0.0
                impuestos.append({
                    "nombre": imp.descripcion,
                    "codigo": imp.codigo_sri,
                    "porcentaje": porcentaje_val,
                })
        except Exception:
            impuestos = []

        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "tipo": producto.tipo,
            "pvp": producto.pvp,
            "casa_comercial": casa_comercial,
            "categorias": categorias,
            "proveedores_persona": proveedores_persona,
            "proveedores_sociedad": proveedores_sociedad,
            "atributos": atributos,
            "impuestos": impuestos,
        }

    def list_paginated_completo(self, session: Session, only_active: bool = True, limit: int = 50, offset: int = 0):
        """Lista productos con toda su información completa"""
        items, meta = self.list_paginated(session, only_active=only_active, limit=limit, offset=offset)

        # Convertir cada producto a formato completo
        productos_completos = []
        for producto in items:
            try:
                producto_completo = self.get_producto_completo(session, producto.id)
                productos_completos.append(producto_completo)
            except Exception:
                # Si falla, incluir el producto básico con campos mínimos del contrato
                productos_completos.append({
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "casa_comercial": None,
                    "categorias": [],
                    "proveedores_persona": [],
                    "proveedores_sociedad": [],
                    "atributos": [],
                    "impuestos": [],
                })

        return productos_completos, meta
