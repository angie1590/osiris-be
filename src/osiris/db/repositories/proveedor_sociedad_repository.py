from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from src.osiris.db.entities.proveedor_sociedad_entity import ProveedorSociedad
from src.osiris.models.proveedor_sociedad_model import (
    ProveedorSociedadCrear,
    ProveedorSociedadActualizar,
)

class ProveedorSociedadRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: ProveedorSociedadCrear) -> ProveedorSociedad:
        print(data)
        nuevo = ProveedorSociedad(
            ruc=data["ruc"],
            razon_social=data["razon_social"],
            nombre_comercial=data["nombre_comercial"],
            direccion=data["direccion"],
            telefono=data["telefono"],
            email=data["email"],
            tipo_contribuyente_id=data["tipo_contribuyente_id"],
            persona_contacto_id=data["persona_contacto_id"],
            usuario_auditoria=data["usuario_auditoria"]
        )
        db.add(nuevo)
        await db.commit()
        await db.refresh(nuevo)
        return nuevo

    @staticmethod
    async def listar(db: AsyncSession) -> list[ProveedorSociedad]:
        result = await db.execute(
            select(ProveedorSociedad).where(ProveedorSociedad.activo == True)
        )
        return result.scalars().all()

    @staticmethod
    async def actualizar(
        db: AsyncSession,
        proveedor_id: UUID,
        data: ProveedorSociedadActualizar
    ) -> ProveedorSociedad | None:
        result = await db.execute(
            select(ProveedorSociedad).where(
                ProveedorSociedad.id == proveedor_id,
                ProveedorSociedad.activo == True
            )
        )
        proveedor = result.scalar_one_or_none()
        if not proveedor:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(proveedor, campo, valor)

        await db.commit()
        await db.refresh(proveedor)
        return proveedor

    @staticmethod
    async def eliminar_logico(db: AsyncSession, proveedor_id: UUID, usuario: str) -> bool:
        result = await db.execute(
            select(ProveedorSociedad).where(
                ProveedorSociedad.id == proveedor_id,
                ProveedorSociedad.activo == True
            )
        )
        proveedor = result.scalar_one_or_none()
        if not proveedor:
            return False

        proveedor.activo = False
        proveedor.usuario_auditoria = usuario
        await db.commit()
        return True
