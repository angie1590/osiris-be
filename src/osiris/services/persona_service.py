from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.osiris.db.repositories.persona_repository import PersonaRepositorio
from src.osiris.models.persona_modelo import PersonaCrear, PersonaActualizar
from src.osiris.db.entities.persona_entity import Persona


class PersonaServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: PersonaCrear) -> Persona:
        existente = await PersonaRepositorio.obtener_por_identificacion(db, data.identificacion)
        if existente:
            raise ValueError("Ya existe una persona registrada con esa identificación.")
        return await PersonaRepositorio.crear(db, data)

    @staticmethod
    async def actualizar(db: AsyncSession, persona_id: UUID, data: PersonaActualizar) -> Persona:
        persona = await PersonaRepositorio.actualizar(db, persona_id, data)
        if not persona:
            raise ValueError("No se encontró una persona activa con ese ID.")
        return persona

    @staticmethod
    async def eliminar(db: AsyncSession, persona_id: UUID, usuario: str) -> None:
        eliminado = await PersonaRepositorio.eliminar_logico(db, persona_id, usuario)
        if not eliminado:
            raise ValueError("No se encontró una persona activa con ese ID.")

    @staticmethod
    async def buscar_por_identificacion(db: AsyncSession, identificacion: str) -> Persona | None:
        return await PersonaRepositorio.obtener_por_identificacion(db, identificacion)

    @staticmethod
    async def buscar_por_apellido(db: AsyncSession, apellido: str) -> list[Persona]:
        return await PersonaRepositorio.buscar_por_apellido(db, apellido)

    @staticmethod
    async def listar(db: AsyncSession) -> list[Persona]:
        return await PersonaRepositorio.listar_todos(db)
