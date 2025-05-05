from sqlalchemy.ext.asyncio import AsyncSession
from src.osiris.db.entities.proveedor_persona_entity import ProveedorPersona
from src.osiris.db.repositories.proveedor_persona_repository import ProveedorPersonaRepositorio
from src.osiris.models.proveedor_persona_model import ProveedorPersonaCrear, ProveedorPersonaActualizar

class ProveedorPersonaServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: ProveedorPersonaCrear) -> ProveedorPersona:
        return await ProveedorPersonaRepositorio.crear(db, data)

    @staticmethod
    async def listar(db: AsyncSession) -> list[ProveedorPersona]:
        return await ProveedorPersonaRepositorio.listar(db)

    @staticmethod
    async def actualizar(db: AsyncSession, proveedor_id: str, data: ProveedorPersonaActualizar) -> ProveedorPersona:
        actualizado = await ProveedorPersonaRepositorio.actualizar(db, proveedor_id, data)
        if not actualizado:
            raise ValueError("Proveedor no encontrado o inactivo.")
        return actualizado

    @staticmethod
    async def eliminar(db: AsyncSession, proveedor_id: str, usuario: str) -> None:
        eliminado = await ProveedorPersonaRepositorio.eliminar_logico(db, proveedor_id, usuario)
        if not eliminado:
            raise ValueError("Proveedor no encontrado o inactivo.")
