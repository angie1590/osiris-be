from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.osiris.models.cliente_model import ClienteCrear, ClienteActualizar
from src.osiris.db.entities.cliente_entity import Cliente
from src.osiris.db.repositories.cliente_repository import ClienteRepositorio

class ClienteServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: ClienteCrear) -> Cliente:
        existente = await ClienteRepositorio.obtener_por_persona_id(db, data.persona_id)
        if existente:
            raise ValueError("Esta persona ya está registrada como cliente.")
        return await ClienteRepositorio.crear(db, data)

    @staticmethod
    async def listar(db: AsyncSession) -> list[Cliente]:
        return await ClienteRepositorio.listar(db)

    @staticmethod
    async def actualizar(db: AsyncSession, cliente_id: UUID, data: ClienteActualizar) -> Cliente:
        actualizado = await ClienteRepositorio.actualizar(db, cliente_id, data)
        if not actualizado:
            raise ValueError("Cliente no encontrado o inactivo.")
        return actualizado

    @staticmethod
    async def eliminar(db: AsyncSession, cliente_id: UUID, usuario: str) -> None:
        eliminado = await ClienteRepositorio.eliminar_logico(db, cliente_id, usuario)
        if not eliminado:
            raise ValueError("Cliente no encontrado o inactivo.")
