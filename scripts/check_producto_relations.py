#!/usr/bin/env python3
"""Verifica relaciones de productos."""

from osiris.core.db import get_session
from osiris.modules.inventario.producto.entity import Producto, ProductoCategoria, ProductoImpuesto, ProductoBodega
from osiris.modules.inventario.categoria.entity import Categoria
from osiris.modules.sri.impuesto_catalogo.entity import ImpuestoCatalogo
from sqlmodel import select

def main():
    session = next(get_session())

    print("=" * 70)
    print("VERIFICACIÓN DE RELACIONES DE PRODUCTOS")
    print("=" * 70)

    # Tomar primer producto
    producto = session.exec(select(Producto).limit(1)).first()

    if not producto:
        print("❌ No hay productos en la BD")
        return

    print(f"\n📦 Producto: {producto.nombre}")
    print(f"   PVP: ${float(producto.pvp):.2f}")
    print(f"   Código barras: {producto.codigo_barras or 'Sin código'}")
    print(f"   Descripción: {producto.descripcion[:60] if producto.descripcion else 'Sin descripción'}...")

    # Categorías
    cat_rels = session.exec(
        select(ProductoCategoria).where(ProductoCategoria.producto_id == producto.id)
    ).all()

    print(f"\n📁 Categorías asignadas: {len(cat_rels)}")
    for rel in cat_rels:
        cat = session.get(Categoria, rel.categoria_id)
        if cat:
            print(f"   • {cat.nombre}")

    # Impuestos
    imp_rels = session.exec(
        select(ProductoImpuesto).where(ProductoImpuesto.producto_id == producto.id)
    ).all()

    print(f"\n💰 Impuestos aplicados: {len(imp_rels)}")
    for rel in imp_rels:
        imp = session.get(ImpuestoCatalogo, rel.impuesto_catalogo_id)
        if imp:
            tarifa = imp.porcentaje_iva or imp.tarifa_ad_valorem or "N/A"
            print(f"   • {imp.descripcion[:50]} ({imp.codigo_sri}) - Tarifa: {tarifa}%")

    # Bodegas
    bod_rels = session.exec(
        select(ProductoBodega).where(ProductoBodega.producto_id == producto.id)
    ).all()

    print(f"\n🏢 Stock en bodegas: {len(bod_rels)}")
    from osiris.modules.inventario.bodega.entity import Bodega
    for rel in bod_rels:
        bod = session.get(Bodega, rel.bodega_id)
        if bod:
            print(f"   • {bod.codigo_bodega:15s} - {bod.nombre_bodega:30s} | {rel.cantidad:3d} unidades")

    print("\n" + "=" * 70)
    print("✓ Verificación de relaciones completada")
    print("=" * 70)

if __name__ == "__main__":
    main()
