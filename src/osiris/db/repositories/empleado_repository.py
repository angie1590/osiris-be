from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.empleado_entity import Empleado
from src.osiris.models.empleado_model import EmpleadoCrear, EmpleadoActualizar

class EmpleadoRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: EmpleadoCrear) -> Empleado:
        nuevo = Empleado(**data.model_dump())
        db.add(nuevo)
        await db.commit()
        await db.refresh(nuevo)
        return nuevo

    @staticmethod
    async def obtener_por_persona_id(db: AsyncSession, persona_id: UUID) -> Empleado | None:
        result = await db.execute(select(Empleado).where(Empleado.id == persona_id, Empleado.activo == True))
        return result.scalar_one_or_none()

    @staticmethod
    async def listar(db: AsyncSession) -> list[Empleado]:
        result = await db.execute(select(Empleado).where(Empleado.activo == True))
        return result.scalars().all()

    @staticmethod
    async def actualizar(db: AsyncSession, empleado_id: UUID, data: EmpleadoActualizar) -> Empleado | None:
        result = await db.execute(select(Empleado).where(Empleado.id == empleado_id, Empleado.activo == True))
        empleado = result.scalar_one_or_none()
        if not empleado:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(empleado, campo, valor)

        await db.commit()
        await db.refresh(empleado)
        return empleado

    @staticmethod
    async def eliminar_logico(db: AsyncSession, empleado_id: UUID, usuario: str) -> bool:
        result = await db.execute(select(Empleado).where(Empleado.id == empleado_id, Empleado.activo == True))
        empleado = result.scalar_one_or_none()
        if not empleado:
            return False

        empleado.activo = False
        empleado.usuario_auditoria = usuario
        await db.commit()
        return True
