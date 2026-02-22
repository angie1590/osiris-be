#!/usr/bin/env python3
"""Script rápido para verificar datos del seed."""

from osiris.core.db import get_session
from osiris.modules.inventario.producto.entity import Producto
from osiris.modules.inventario.bodega.entity import Bodega
from osiris.modules.common.empresa.entity import Empresa
from osiris.modules.common.sucursal.entity import Sucursal
from sqlmodel import select, func

def main():
    session = next(get_session())

    print("=" * 60)
    print("VERIFICACIÓN DE DATOS SEED")
    print("=" * 60)

    # Contar registros
    empresas = session.exec(select(func.count(Empresa.id))).first()
    sucursales = session.exec(select(func.count(Sucursal.id))).first()
    bodegas = session.exec(select(func.count(Bodega.id))).first()
    productos = session.exec(select(func.count(Producto.id))).first()

    print("\n📊 Resumen de tablas:")
    print(f"  - Empresas: {empresas}")
    print(f"  - Sucursales: {sucursales}")
    print(f"  - Bodegas: {bodegas}")
    print(f"  - Productos: {productos}")

    # Mostrar 5 productos
    print("\n📦 Primeros 5 productos:")
    prods = session.exec(select(Producto).limit(5)).all()
    for p in prods:
        desc = p.descripcion[:40] if p.descripcion else "Sin descripción"
        barcode = p.codigo_barras or "Sin código"
        print(f"  • {barcode:15s} | {p.nombre[:30]:30s} | ${float(p.pvp):8.2f} | {desc}...")

    # Mostrar bodegas
    print("\n🏢 Bodegas:")
    bods = session.exec(select(Bodega)).all()
    for b in bods:
        print(f"  • {b.codigo_bodega} | {b.nombre_bodega}")

    print("\n" + "=" * 60)
    print("✓ Verificación completada")
    print("=" * 60)

if __name__ == "__main__":
    main()
