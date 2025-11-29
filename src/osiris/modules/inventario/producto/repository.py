from typing import Iterable
from uuid import UUID

from sqlmodel import Session, select
from osiris.domain.repository import BaseRepository
from .entity import (
    Producto,
    ProductoCategoria,
    ProductoProveedorPersona,
    ProductoProveedorSociedad,
)

class ProductoRepository(BaseRepository):
    model = Producto

    def set_categorias(self, session: Session, producto_id: UUID, categoria_ids: Iterable[UUID]) -> None:
        session.exec(select(ProductoCategoria).where(ProductoCategoria.producto_id == producto_id)).all()
        session.exec(
            select(ProductoCategoria).where(ProductoCategoria.producto_id == producto_id)
        ).all()
        # borrar existentes
        session.exec(
            select(ProductoCategoria).where(ProductoCategoria.producto_id == producto_id)
        )
        session.query(ProductoCategoria).filter(ProductoCategoria.producto_id == producto_id).delete()
        # insertar nuevas
        for cid in categoria_ids:
            session.add(ProductoCategoria(producto_id=producto_id, categoria_id=cid))
        session.commit()

    def set_proveedores_persona(self, session: Session, producto_id: UUID, prov_ids: Iterable[UUID]) -> None:
        session.query(ProductoProveedorPersona).filter(ProductoProveedorPersona.producto_id == producto_id).delete()
        for pid in prov_ids:
            session.add(ProductoProveedorPersona(producto_id=producto_id, proveedor_persona_id=pid))
        session.commit()

    def set_proveedores_sociedad(self, session: Session, producto_id: UUID, prov_ids: Iterable[UUID]) -> None:
        session.query(ProductoProveedorSociedad).filter(ProductoProveedorSociedad.producto_id == producto_id).delete()
        for sid in prov_ids:
            session.add(ProductoProveedorSociedad(producto_id=producto_id, proveedor_sociedad_id=sid))
        session.commit()
