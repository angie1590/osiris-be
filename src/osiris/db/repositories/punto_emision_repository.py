# src/osiris/db/repositories/punto_emision_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.punto_emision_entity import PuntoEmision
from src.osiris.models.punto_emision_model import PuntoEmisionCrear, PuntoEmisionActualizar

class PuntoEmisionRepositorio:
    @staticmethod
    async def crear(db: AsyncSession, datos: PuntoEmisionCrear):
        punto = PuntoEmision(**datos.model_dump())
        db.add(punto)
        await db.commit()
        await db.refresh(punto)
        return punto

    @staticmethod
    async def obtener_por_id(db: AsyncSession, id: UUID) -> PuntoEmision:
        result = await db.execute(select(PuntoEmision).where(PuntoEmision.id == id))
        return result.scalars().first()

    @staticmethod
    async def listar(db: AsyncSession, incluir_inactivos: bool = False) -> list[PuntoEmision]:
        query = select(PuntoEmision)
        if not incluir_inactivos:
            query = query.where(PuntoEmision.activo == True)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def actualizar(db: AsyncSession, id: UUID, datos: PuntoEmision):
        punto = await PuntoEmisionRepositorio.obtener_por_id(db, id)
        if not punto:
            return None

        for attr, value in datos.dict(exclude_unset=True).items():
            setattr(punto, attr, value)

        await db.commit()
        await db.refresh(punto)
        return punto

    @staticmethod
    async def eliminar_logico(db: AsyncSession, id: UUID):
        punto = await PuntoEmisionRepositorio.obtener_por_id(db, id)
        if punto:
            punto.activo = False
            await db.commit()
            await db.refresh(punto)
        return punto