from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.osiris.db.repositories.rol_repository import RolRepositorio
from src.osiris.models.rol_model import RolCrear, RolActualizar
from src.osiris.db.entities.rol_entity import Rol

class RolServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: RolCrear) -> Rol:
        existente = await RolRepositorio.obtener_por_nombre(db, data.nombre)
        if existente:
            raise ValueError("Ya existe un rol con ese nombre.")
        return await RolRepositorio.crear(db, data)

    @staticmethod
    async def listar(db: AsyncSession) -> list[Rol]:
        return await RolRepositorio.listar_todos(db)

    @staticmethod
    async def actualizar(db: AsyncSession, rol_id: UUID, data: RolActualizar) -> Rol:
        rol = await RolRepositorio.actualizar(db, rol_id, data)
        if not rol:
            raise ValueError("Rol no encontrado o inactivo.")
        return rol

    @staticmethod
    async def eliminar(db: AsyncSession, rol_id: UUID, usuario: str) -> None:
        eliminado = await RolRepositorio.eliminar_logico(db, rol_id, usuario)
        if not eliminado:
            raise ValueError("Rol no encontrado o inactivo.")
