from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.osiris.models.tipo_cliente_model import TipoClienteCrear, TipoClienteActualizar
from src.osiris.db.repositories.tipo_cliente_repository import TipoClienteRepositorio
from src.osiris.db.entities.tipo_cliente_entity import TipoCliente

class TipoClienteServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: TipoClienteCrear) -> TipoCliente:
        return await TipoClienteRepositorio.crear(db, data)

    @staticmethod
    async def listar(db: AsyncSession) -> list[TipoCliente]:
        return await TipoClienteRepositorio.listar(db)

    @staticmethod
    async def actualizar(db: AsyncSession, tipo_id: UUID, data: TipoClienteActualizar) -> TipoCliente:
        actualizado = await TipoClienteRepositorio.actualizar(db, tipo_id, data)
        if not actualizado:
            raise ValueError("Tipo de cliente no encontrado.")
        return actualizado
