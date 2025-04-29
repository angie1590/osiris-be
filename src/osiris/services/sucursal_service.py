# src/osiris/services/sucursal_service.py

from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.osiris.db.repositories.sucursal_repository import SucursalRepositorio
from src.osiris.models.sucursal_model import SucursalCrear, SucursalActualizar


class SucursalServicio:
    @staticmethod
    async def crear(db: AsyncSession, datos: SucursalCrear):
        return await SucursalRepositorio.crear(db, datos)

    @staticmethod
    async def listar(db: AsyncSession, incluir_inactivos: bool = False):
        return await SucursalRepositorio.listar(db, incluir_inactivos)

    @staticmethod
    async def actualizar(db: AsyncSession, id: UUID, datos: SucursalActualizar):
        return await SucursalRepositorio.actualizar(db, id, datos)

    @staticmethod
    async def eliminar_logico(db: AsyncSession, id: UUID):
        sucursal = await SucursalRepositorio.obtener_por_id(db, id)
        if not sucursal:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada")
        sucursal.activo = False
        await db.commit()
