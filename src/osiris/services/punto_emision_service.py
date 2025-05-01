# src/osiris/services/punto_emision_service.py

from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.osiris.models.punto_emision_model import PuntoEmisionCrear, PuntoEmisionActualizar
from src.osiris.db.repositories.punto_emision_repository import PuntoEmisionRepositorio


class PuntoEmisionServicio:
    @staticmethod
    async def crear(db: AsyncSession, datos: PuntoEmisionCrear):
        return await PuntoEmisionRepositorio.crear(db, datos)

    @staticmethod
    async def obtener(db: AsyncSession, id: UUID):
        return await PuntoEmisionRepositorio.obtener_por_id(db, id)

    @staticmethod
    async def listar(db: AsyncSession, incluir_inactivos: bool = False):
        return await PuntoEmisionRepositorio.listar(db, incluir_inactivos)

    @staticmethod
    async def actualizar(db: AsyncSession, id: UUID, datos: PuntoEmisionActualizar):
        return await PuntoEmisionRepositorio.actualizar(db, id, datos)

    @staticmethod
    async def eliminar_logico(db: AsyncSession, id: UUID):
        punto_emision = await PuntoEmisionRepositorio.eliminar_logico(db, id)
        if not punto_emision:
             raise HTTPException(status_code=404, detail="Punto de emisión no encontrado")
        punto_emision.activo = False
        await db.commit()
