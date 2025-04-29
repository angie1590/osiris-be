# src/osiris/db/repositories/sucursal_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.sucursal_entity import Sucursal
from src.osiris.models.sucursal_model import SucursalCrear, SucursalActualizar


class SucursalRepositorio:
    @staticmethod
    async def crear(db: AsyncSession, datos: SucursalCrear):
        sucursal = Sucursal(**datos.model_dump())
        db.add(sucursal)
        await db.commit()
        await db.refresh(sucursal)
        return sucursal

    @staticmethod
    async def obtener_por_id(db: AsyncSession, id: UUID):
        result = await db.execute(select(Sucursal).where(Sucursal.id == id))
        return result.scalars().first()

    @staticmethod
    async def listar(db: AsyncSession, incluir_inactivos: bool = False):
        query = select(Sucursal)
        if not incluir_inactivos:
            query = query.where(Sucursal.activo == True)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def actualizar(db: AsyncSession, id: UUID, datos: SucursalActualizar):
        sucursal = await SucursalRepositorio.obtener_por_id(db, id)
        if not sucursal:
            return None
        for attr, value in datos.dict(exclude_unset=True).items():
            setattr(sucursal, attr, value)
        await db.commit()
        await db.refresh(sucursal)
        return sucursal

    @staticmethod
    async def eliminar_logico(db: AsyncSession, id: UUID):
        sucursal = await SucursalRepositorio.obtener_por_id(db, id)
        if sucursal:
            sucursal.activo = False
            await db.commit()
            await db.refresh(sucursal)
        return sucursal
