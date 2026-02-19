# src/osiris/modules/inventario/producto_bodega/service.py
from __future__ import annotations

from uuid import UUID
from sqlmodel import Session, select
from fastapi import HTTPException

from osiris.domain.service import BaseService
from osiris.modules.inventario.producto.entity import Producto, ProductoBodega
from osiris.modules.inventario.bodega.entity import Bodega
from .repository import ProductoBodegaRepository


class ProductoBodegaService(BaseService):
    repo = ProductoBodegaRepository()

    # FKs a validar: producto y bodega deben existir y estar activos
    fk_models = {
        "producto_id": Producto,
        "bodega_id": Bodega,
    }

    @staticmethod
    def _is_service_product(producto: Producto | None) -> bool:
        if producto is None:
            return False

        tipo = getattr(producto, "tipo", None)
        if tipo is None:
            return False

        # Soporta enums (TipoProducto.SERVICIO) y strings ("SERVICIO")
        return getattr(tipo, "value", tipo) == "SERVICIO"

    def create(self, session: Session, data):
        """
        Crea una relación producto-bodega.
        Valida que no exista duplicado (constraint único en BD).
        """
        producto_id = data.get("producto_id")
        bodega_id = data.get("bodega_id")
        cantidad = data.get("cantidad", 0)

        # Validar si ya existe la relación
        existing = session.exec(
            select(ProductoBodega)
            .where(ProductoBodega.producto_id == producto_id)
            .where(ProductoBodega.bodega_id == bodega_id)
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"El producto ya está asignado a la bodega especificada."
            )

        # Regla de negocio: Productos de tipo SERVICIO no pueden tener stock (> 0) ni asignaciones a bodegas con cantidad positiva
        producto = session.get(Producto, producto_id)
        if self._is_service_product(producto) and cantidad > 0:
            raise HTTPException(
                status_code=400,
                detail="Los servicios no pueden tener stock en bodegas.",
            )

        # Alternativamente, si el producto existe y es SERVICIO, forzar cantidad = 0
        if self._is_service_product(producto):
            data["cantidad"] = 0

        return super().create(session, data)

    def update_cantidad(self, session: Session, producto_id: UUID, bodega_id: UUID, cantidad: int):
        """
        Actualiza la cantidad de un producto en una bodega específica.
        Si no existe la relación, la crea.
        """
        # Regla de negocio: Productos de tipo SERVICIO no pueden tener stock (> 0)
        producto = session.get(Producto, producto_id)
        if self._is_service_product(producto) and cantidad > 0:
            raise HTTPException(status_code=400, detail="Los servicios no pueden tener stock.")

        relacion = session.exec(
            select(ProductoBodega)
            .where(ProductoBodega.producto_id == producto_id)
            .where(ProductoBodega.bodega_id == bodega_id)
        ).first()

        if not relacion:
            # Crear nueva relación
            relacion = ProductoBodega(
                producto_id=producto_id,
                bodega_id=bodega_id,
                cantidad=cantidad
            )
            session.add(relacion)
        else:
            # Actualizar cantidad existente
            relacion.cantidad = cantidad
            session.add(relacion)

        session.commit()
        session.refresh(relacion)
        return relacion

    def get_bodegas_by_producto(self, session: Session, producto_id: UUID):
        """Obtiene todas las bodegas donde está un producto"""
        relaciones = session.exec(
            select(ProductoBodega, Bodega)
            .join(Bodega, Bodega.id == ProductoBodega.bodega_id)
            .where(ProductoBodega.producto_id == producto_id)
        ).all()

        return [
            {
                "id": rel.id,
                "bodega_id": bodega.id,
                "codigo_bodega": bodega.codigo_bodega,
                "nombre_bodega": bodega.nombre_bodega,
                "cantidad": rel.cantidad,
            }
            for rel, bodega in relaciones
        ]

    def get_productos_by_bodega(self, session: Session, bodega_id: UUID):
        """Obtiene todos los productos en una bodega"""
        relaciones = session.exec(
            select(ProductoBodega, Producto)
            .join(Producto, Producto.id == ProductoBodega.producto_id)
            .where(ProductoBodega.bodega_id == bodega_id)
        ).all()

        return [
            {
                "id": rel.id,
                "producto_id": producto.id,
                "nombre": producto.nombre,
                "cantidad": rel.cantidad,
            }
            for rel, producto in relaciones
        ]
