from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from osiris.core.db import SOFT_DELETE_INCLUDE_INACTIVE_OPTION
from osiris.core.errors import NotFoundError
from osiris.domain.service import BaseService
from osiris.modules.inventario.categoria.entity import Categoria  # existente
from osiris.modules.inventario.casa_comercial.entity import CasaComercial
from osiris.modules.inventario.producto_impuesto.service import ProductoImpuestoService
from osiris.modules.sri.impuesto_catalogo.entity import ImpuestoCatalogo
from osiris.utils.pagination import build_pagination_meta
from fastapi import HTTPException
from .repository import ProductoRepository
from .entity import (
    Producto,
    ProductoCategoria,
    ProductoProveedorPersona,
    ProductoProveedorSociedad,
    ProductoBodega,
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
            from osiris.modules.sri.impuesto_catalogo.entity import TipoImpuesto
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
        try:
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

            prod = super().create(session, data, commit=False)
            pid = prod.id

            # asociaciones
            if categoria_ids:
                self.repo.set_categorias(session, pid, categoria_ids)
            usuario_auditoria = _val(data, "usuario_auditoria")

            # Asociar impuestos automáticamente
            if impuesto_ids:
                for imp_id in impuesto_ids:
                    impuesto = session.get(ImpuestoCatalogo, imp_id)
                    if not impuesto:
                        raise HTTPException(status_code=400, detail=f"Impuesto {imp_id} no existe.")

                    if impuesto.tipo_impuesto.value == "IVA":
                        tarifa = impuesto.porcentaje_iva or 0
                    elif impuesto.tipo_impuesto.value == "ICE":
                        tarifa = impuesto.tarifa_ad_valorem or 0
                    else:
                        tarifa = 0

                    producto_impuesto = ProductoImpuesto(
                        producto_id=pid,
                        impuesto_catalogo_id=imp_id,
                        codigo_impuesto_sri=impuesto.codigo_tipo_impuesto,
                        codigo_porcentaje_sri=impuesto.codigo_sri,
                        tarifa=tarifa,
                        usuario_auditoria=usuario_auditoria
                    )
                    session.add(producto_impuesto)

            session.commit()
            session.refresh(prod)
            return prod
        except Exception as exc:
            self._handle_transaction_error(session, exc)

    def update(self, session: Session, item_id: UUID, data):
        try:
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
            prod = super().update(session, item_id, data, commit=False)
            if prod is None:
                return None
            # asociaciones
            if categoria_ids is not None:
                self.repo.set_categorias(session, item_id, categoria_ids)
            _val(data, "usuario_auditoria")
            session.commit()
            session.refresh(prod)
            return prod
        except Exception as exc:
            self._handle_transaction_error(session, exc)

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
        from osiris.modules.inventario.categoria_atributo.entity import CategoriaAtributo
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

        # Atributos efectivos por categoría (herencia padre->hijo) + valores del producto (si existen)
        atributos = []
        # 1) Recolectar categorías del producto y sus ancestros
        categorias_ids = set(cat_ids)
        to_visit = list(cat_ids)
        while to_visit:
            current = to_visit.pop()
            cat = session.get(Categoria, current)
            if cat and cat.parent_id and cat.parent_id not in categorias_ids:
                categorias_ids.add(cat.parent_id)
                to_visit.append(cat.parent_id)

        # 2) Mapear atributos definidos en categorías (incluyendo ancestros)
        cat_attrs = session.exec(
            select(CategoriaAtributo, Atributo)
            .join(Atributo, Atributo.id == CategoriaAtributo.atributo_id)
            .where(CategoriaAtributo.categoria_id.in_(list(categorias_ids)))
        ).all()

        # 3) Valores por producto eliminados: ya no se consulta tbl_tipo_producto
        valor_por_atributo: dict = {}

        # 4) Unificar por atributo (evitar duplicados si viene de múltiples categorías)
        vistos = set()
        for ca, atributo in cat_attrs:
            if atributo.id in vistos:
                continue
            vistos.add(atributo.id)
            valor = valor_por_atributo.get(atributo.id)
            valor = str(valor) if valor is not None else None
            atributos.append({
                "atributo": {"nombre": atributo.nombre},
                "valor": valor,
            })

        # Impuestos (resiliente: si algo falla, lista vacía)
        impuestos = []
        try:
            impuesto_service = ProductoImpuestoService()
            impuestos_raw = impuesto_service.get_impuestos_completos(session, producto_id)
            for imp in impuestos_raw:
                porcentaje_val = Decimal("0.00")
                try:
                    # IVA usa porcentaje_iva, ICE usa tarifa_ad_valorem
                    raw_porcentaje = imp.porcentaje_iva or imp.tarifa_ad_valorem or Decimal("0.00")
                    porcentaje_val = (
                        raw_porcentaje
                        if isinstance(raw_porcentaje, Decimal)
                        else Decimal(str(raw_porcentaje))
                    )
                except Exception:
                    porcentaje_val = Decimal("0.00")
                impuestos.append({
                    "nombre": imp.descripcion,
                    "codigo": imp.codigo_sri,
                    "porcentaje": porcentaje_val,
                })
        except Exception:
            impuestos = []

        # Bodegas (relación producto-bodega)
        from osiris.modules.inventario.producto.entity import ProductoBodega
        from osiris.modules.inventario.bodega.entity import Bodega

        bodegas = []
        try:
            bodega_ids = session.exec(
                select(ProductoBodega.bodega_id)
                .where(ProductoBodega.producto_id == producto_id)
            ).all()
            for bodega_id in bodega_ids:
                bodega = session.get(Bodega, bodega_id)
                if bodega:
                    bodegas.append({
                        "codigo_bodega": bodega.codigo_bodega,
                        "nombre_bodega": bodega.nombre_bodega,
                    })
        except Exception:
            bodegas = []

        return {
            "id": producto.id,
            "nombre": producto.nombre,
            "tipo": producto.tipo,
            "pvp": producto.pvp,
            "cantidad": producto.cantidad,
            "casa_comercial": casa_comercial,
            "categorias": categorias,
            "proveedores_persona": proveedores_persona,
            "proveedores_sociedad": proveedores_sociedad,
            "atributos": atributos,
            "impuestos": impuestos,
            "bodegas": bodegas,
        }

    def list_paginated_completo(self, session: Session, only_active: bool = True, limit: int = 50, offset: int = 0):
        """Lista productos completos evitando N+1 con carga masiva."""
        from collections import defaultdict

        from osiris.modules.common.persona.entity import Persona
        from osiris.modules.common.proveedor_persona.entity import ProveedorPersona
        from osiris.modules.common.proveedor_sociedad.entity import ProveedorSociedad
        from osiris.modules.inventario.atributo.entity import Atributo
        from osiris.modules.inventario.bodega.entity import Bodega
        from osiris.modules.inventario.casa_comercial.entity import CasaComercial
        from osiris.modules.inventario.categoria.entity import Categoria
        from osiris.modules.inventario.categoria_atributo.entity import CategoriaAtributo

        stmt_base = select(Producto)
        if only_active is not None and hasattr(Producto, "activo"):
            stmt_base = stmt_base.where(Producto.activo == only_active)
        if hasattr(Producto, "activo") and only_active in {None, False}:
            stmt_base = stmt_base.execution_options(
                **{SOFT_DELETE_INCLUDE_INACTIVE_OPTION: True}
            )

        count_stmt = select(func.count()).select_from(stmt_base.subquery())
        if hasattr(Producto, "activo") and only_active in {None, False}:
            count_stmt = count_stmt.execution_options(
                **{SOFT_DELETE_INCLUDE_INACTIVE_OPTION: True}
            )
        total: int = int(session.exec(count_stmt).one())
        meta = build_pagination_meta(total=total, limit=limit, offset=offset)

        stmt_productos = (
            stmt_base
            .offset(offset)
            .limit(limit)
            .options(
                selectinload(Producto.producto_categorias).selectinload(ProductoCategoria.categoria),
                selectinload(Producto.producto_impuestos).selectinload(ProductoImpuesto.impuesto_catalogo),
            )
        )
        productos_cargados = list(session.exec(stmt_productos).all())
        if not productos_cargados:
            return [], meta

        producto_ids = [item.id for item in productos_cargados]
        producto_por_id = {producto.id: producto for producto in productos_cargados}

        casa_ids = {
            producto.casa_comercial_id
            for producto in productos_cargados
            if producto.casa_comercial_id is not None
        }
        casas_por_id: dict[UUID, CasaComercial] = {}
        if casa_ids:
            casas = session.exec(
                select(CasaComercial).where(CasaComercial.id.in_(casa_ids))
            ).all()
            casas_por_id = {casa.id: casa for casa in casas}

        proveedores_persona_por_producto: dict[UUID, list[dict]] = defaultdict(list)
        rows_prov_persona = session.exec(
            select(ProductoProveedorPersona.producto_id, ProveedorPersona, Persona)
            .join(
                ProveedorPersona,
                ProveedorPersona.id == ProductoProveedorPersona.proveedor_persona_id,
            )
            .join(Persona, Persona.id == ProveedorPersona.persona_id)
            .where(ProductoProveedorPersona.producto_id.in_(producto_ids))
        ).all()
        for producto_id, proveedor, persona in rows_prov_persona:
            proveedores_persona_por_producto[producto_id].append(
                {
                    "nombres": persona.nombre,
                    "apellidos": persona.apellido,
                    "nombre_comercial": getattr(proveedor, "nombre_comercial", None),
                }
            )

        proveedores_sociedad_por_producto: dict[UUID, list[dict]] = defaultdict(list)
        rows_prov_sociedad = session.exec(
            select(ProductoProveedorSociedad.producto_id, ProveedorSociedad)
            .join(
                ProveedorSociedad,
                ProveedorSociedad.id == ProductoProveedorSociedad.proveedor_sociedad_id,
            )
            .where(ProductoProveedorSociedad.producto_id.in_(producto_ids))
        ).all()
        for producto_id, proveedor in rows_prov_sociedad:
            proveedores_sociedad_por_producto[producto_id].append(
                {
                    "razon_social": proveedor.razon_social,
                    "nombre_comercial": getattr(proveedor, "nombre_comercial", None),
                }
            )

        bodegas_por_producto: dict[UUID, list[dict]] = defaultdict(list)
        rows_bodega = session.exec(
            select(ProductoBodega.producto_id, Bodega)
            .join(Bodega, Bodega.id == ProductoBodega.bodega_id)
            .where(ProductoBodega.producto_id.in_(producto_ids))
        ).all()
        for producto_id, bodega in rows_bodega:
            bodegas_por_producto[producto_id].append(
                {
                    "codigo_bodega": bodega.codigo_bodega,
                    "nombre_bodega": bodega.nombre_bodega,
                }
            )

        categorias_por_producto: dict[UUID, list[dict]] = defaultdict(list)
        categorias_directas_por_producto: dict[UUID, list[UUID]] = defaultdict(list)
        parent_por_categoria: dict[UUID, UUID | None] = {}
        categorias_relacionadas: set[UUID] = set()
        rows_categorias_producto = session.exec(
            select(
                ProductoCategoria.producto_id,
                Categoria.id,
                Categoria.nombre,
                Categoria.parent_id,
            )
            .join(Categoria, Categoria.id == ProductoCategoria.categoria_id)
            .where(ProductoCategoria.producto_id.in_(producto_ids))
        ).all()
        for producto_id, categoria_id, categoria_nombre, categoria_parent_id in rows_categorias_producto:
            categorias_por_producto[producto_id].append(
                {"id": categoria_id, "nombre": categoria_nombre}
            )
            categorias_directas_por_producto[producto_id].append(categoria_id)
            parent_por_categoria[categoria_id] = categoria_parent_id
            categorias_relacionadas.add(categoria_id)

        pendientes = {cid for cid in categorias_relacionadas if parent_por_categoria.get(cid)}
        while pendientes:
            rows_padres = session.exec(
                select(Categoria.id, Categoria.parent_id).where(Categoria.id.in_(pendientes))
            ).all()
            nuevos_pendientes: set[UUID] = set()
            for categoria_id, parent_id in rows_padres:
                parent_por_categoria[categoria_id] = parent_id
                if parent_id and parent_id not in parent_por_categoria:
                    nuevos_pendientes.add(parent_id)
            pendientes = nuevos_pendientes

        ancestros_cache: dict[UUID, set[UUID]] = {}

        def _expandir_ancestros(categoria_id: UUID) -> set[UUID]:
            if categoria_id in ancestros_cache:
                return ancestros_cache[categoria_id]

            resultado = {categoria_id}
            parent_id = parent_por_categoria.get(categoria_id)
            while parent_id:
                resultado.add(parent_id)
                parent_id = parent_por_categoria.get(parent_id)

            ancestros_cache[categoria_id] = resultado
            return resultado

        categorias_para_atributos: set[UUID] = set()
        for categoria_id in categorias_relacionadas:
            categorias_para_atributos.update(_expandir_ancestros(categoria_id))

        atributos_por_categoria: dict[UUID, list[tuple[UUID, str]]] = defaultdict(list)
        if categorias_para_atributos:
            rows_atributos = session.exec(
                select(CategoriaAtributo.categoria_id, Atributo.id, Atributo.nombre)
                .join(Atributo, Atributo.id == CategoriaAtributo.atributo_id)
                .where(CategoriaAtributo.categoria_id.in_(categorias_para_atributos))
            ).all()
            for categoria_id, atributo_id, nombre in rows_atributos:
                atributos_por_categoria[categoria_id].append((atributo_id, nombre))

        impuestos_por_producto: dict[UUID, list[dict]] = defaultdict(list)
        rows_impuestos = session.exec(
            select(ProductoImpuesto.producto_id, ImpuestoCatalogo)
            .join(ImpuestoCatalogo, ImpuestoCatalogo.id == ProductoImpuesto.impuesto_catalogo_id)
            .where(
                ProductoImpuesto.producto_id.in_(producto_ids),
                ProductoImpuesto.activo.is_(True),
            )
        ).all()
        for producto_id, impuesto_catalogo in rows_impuestos:
            if impuesto_catalogo is None or not impuesto_catalogo.activo:
                continue

            raw_porcentaje = (
                impuesto_catalogo.porcentaje_iva
                or impuesto_catalogo.tarifa_ad_valorem
                or Decimal("0.00")
            )
            porcentaje_val = (
                raw_porcentaje
                if isinstance(raw_porcentaje, Decimal)
                else Decimal(str(raw_porcentaje))
            )
            impuestos_por_producto[producto_id].append(
                {
                    "nombre": impuesto_catalogo.descripcion,
                    "codigo": impuesto_catalogo.codigo_sri,
                    "porcentaje": porcentaje_val,
                }
            )

        productos_completos: list[dict] = []
        for producto_id in producto_ids:
            producto = producto_por_id.get(producto_id)
            if producto is None:
                continue

            casa_comercial = None
            if producto.casa_comercial_id:
                casa = casas_por_id.get(producto.casa_comercial_id)
                if casa is not None:
                    casa_comercial = {"nombre": casa.nombre}

            categorias = categorias_por_producto.get(producto.id, [])

            atributos = []
            atributos_vistos: set[UUID] = set()
            categoria_ids_directas = categorias_directas_por_producto.get(producto.id, [])
            categorias_expandidas: set[UUID] = set()
            for categoria_id in categoria_ids_directas:
                categorias_expandidas.update(_expandir_ancestros(categoria_id))

            for categoria_id in categorias_expandidas:
                for atributo_id, nombre_atributo in atributos_por_categoria.get(categoria_id, []):
                    if atributo_id in atributos_vistos:
                        continue
                    atributos_vistos.add(atributo_id)
                    atributos.append(
                        {
                            "atributo": {"nombre": nombre_atributo},
                            "valor": None,
                        }
                    )

            productos_completos.append(
                {
                    "id": producto.id,
                    "nombre": producto.nombre,
                    "tipo": producto.tipo,
                    "pvp": producto.pvp,
                    "cantidad": producto.cantidad,
                    "casa_comercial": casa_comercial,
                    "categorias": categorias,
                    "proveedores_persona": proveedores_persona_por_producto.get(producto.id, []),
                    "proveedores_sociedad": proveedores_sociedad_por_producto.get(producto.id, []),
                    "atributos": atributos,
                    "impuestos": impuestos_por_producto.get(producto.id, []),
                    "bodegas": bodegas_por_producto.get(producto.id, []),
                }
            )

        return productos_completos, meta
