from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.cliente_entity import Cliente
from src.osiris.models.cliente_model import ClienteCrear, ClienteActualizar

class ClienteRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: ClienteCrear) -> Cliente:
        nuevo = Cliente(**data.model_dump())
        db.add(nuevo)
        await db.commit()
        await db.refresh(nuevo)
        return nuevo

    @staticmethod
    async def obtener_por_id(db: AsyncSession, cliente_id: UUID) -> Cliente | None:
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id, Cliente.activo == True))
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(db: AsyncSession) -> list[Cliente]:
        result = await db.execute(select(Cliente).where(Cliente.activo == True))
        return result.scalars().all()

    @staticmethod
    async def actualizar(db: AsyncSession, cliente_id: UUID, data: ClienteActualizar) -> Cliente | None:
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id, Cliente.activo == True))
        cliente = result.scalar_one_or_none()
        if not cliente:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(cliente, campo, valor)

        await db.commit()
        await db.refresh(cliente)
        return cliente

    @staticmethod
    async def eliminar_logico(db: AsyncSession, cliente_id: UUID, usuario: str) -> bool:
        result = await db.execute(select(Cliente).where(Cliente.id == cliente_id, Cliente.activo == True))
        cliente = result.scalar_one_or_none()
        if not cliente:
            return False

        cliente.activo = False
        cliente.usuario_auditoria = usuario
        await db.commit()
        return True
