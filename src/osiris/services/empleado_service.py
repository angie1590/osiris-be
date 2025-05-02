from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.osiris.models.empleado_model import EmpleadoCrear, EmpleadoActualizar
from src.osiris.db.entities.empleado_entity import Empleado
from src.osiris.db.repositories.empleado_repository import EmpleadoRepositorio

class EmpleadoServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: EmpleadoCrear) -> Empleado:
        existente = await EmpleadoRepositorio.obtener_por_persona_id(db, data.persona_id)
        if existente:
            raise ValueError("Esta persona ya está registrada como empleado.")
        return await EmpleadoRepositorio.crear(db, data)

    @staticmethod
    async def listar(db: AsyncSession) -> list[Empleado]:
        return await EmpleadoRepositorio.listar(db)

    @staticmethod
    async def actualizar(db: AsyncSession, empleado_id: UUID, data: EmpleadoActualizar) -> Empleado:
        actualizado = await EmpleadoRepositorio.actualizar(db, empleado_id, data)
        if not actualizado:
            raise ValueError("Empleado no encontrado o inactivo.")
        return actualizado

    @staticmethod
    async def eliminar(db: AsyncSession, empleado_id: UUID, usuario: str) -> None:
        eliminado = await EmpleadoRepositorio.eliminar_logico(db, empleado_id, usuario)
        if not eliminado:
            raise ValueError("Empleado no encontrado o inactivo.")
