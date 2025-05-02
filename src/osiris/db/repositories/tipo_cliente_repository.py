from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.tipo_cliente_entity import TipoCliente
from src.osiris.models.tipo_cliente_model import TipoClienteCrear, TipoClienteActualizar

class TipoClienteRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: TipoClienteCrear) -> TipoCliente:
        nuevo = TipoCliente(**data.model_dump())
        db.add(nuevo)
        await db.commit()
        await db.refresh(nuevo)
        return nuevo

    @staticmethod
    async def listar(db: AsyncSession) -> list[TipoCliente]:
        result = await db.execute(select(TipoCliente))
        return result.scalars().all()

    @staticmethod
    async def obtener_por_id(db: AsyncSession, tipo_id: UUID) -> TipoCliente | None:
        result = await db.execute(select(TipoCliente).where(TipoCliente.id == tipo_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def actualizar(db: AsyncSession, tipo_id: UUID, data: TipoClienteActualizar) -> TipoCliente | None:
        result = await db.execute(select(TipoCliente).where(TipoCliente.id == tipo_id))
        tipo = result.scalar_one_or_none()
        if not tipo:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(tipo, campo, valor)

        await db.commit()
        await db.refresh(tipo)
        return tipo
