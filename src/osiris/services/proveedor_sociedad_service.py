from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.osiris.models.proveedor_sociedad_model import (
    ProveedorSociedadCrear,
    ProveedorSociedadActualizar,
)
from src.osiris.db.entities.proveedor_sociedad_entity import ProveedorSociedad
from src.osiris.db.repositories.proveedor_sociedad_repository import ProveedorSociedadRepositorio
from src.osiris.db.repositories.persona_repository import PersonaRepositorio


class ProveedorSociedadServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: ProveedorSociedadCrear) -> ProveedorSociedad:
        persona = await PersonaRepositorio.obtener_por_id(db, data.persona_contacto_id)
        if not persona or not persona.activo:
            raise ValueError("La persona de contacto no existe o está inactiva.")

        return await ProveedorSociedadRepositorio.crear(db, data)

    @staticmethod
    async def listar(db: AsyncSession) -> list[ProveedorSociedad]:
        return await ProveedorSociedadRepositorio.listar(db)

    @staticmethod
    async def actualizar(
        db: AsyncSession,
        proveedor_id: UUID,
        data: ProveedorSociedadActualizar
    ) -> ProveedorSociedad:
        actualizado = await ProveedorSociedadRepositorio.actualizar(db, proveedor_id, data)
        if not actualizado:
            raise ValueError("Proveedor no encontrado o inactivo.")
        return actualizado

    @staticmethod
    async def eliminar(db: AsyncSession, proveedor_id: UUID, usuario: str) -> None:
        eliminado = await ProveedorSociedadRepositorio.eliminar_logico(db, proveedor_id, usuario)
        if not eliminado:
            raise ValueError("Proveedor no encontrado o inactivo.")
