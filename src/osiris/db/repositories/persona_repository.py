from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from uuid import UUID

from src.osiris.db.entities.persona_entity import Persona
from osiris.models.persona_model import PersonaCrear, PersonaActualizar


class PersonaRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: PersonaCrear) -> Persona:
        nueva_persona = Persona(**data.model_dump())
        db.add(nueva_persona)
        await db.commit()
        await db.refresh(nueva_persona)
        return nueva_persona

    @staticmethod
    async def obtener_por_identificacion(db: AsyncSession, identificacion: str) -> Persona | None:
        result = await db.execute(
            select(Persona).where(Persona.identificacion == identificacion, Persona.activo == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def buscar_por_apellido(db: AsyncSession, apellido: str) -> list[Persona]:
        result = await db.execute(
            select(Persona).where(Persona.apellido.ilike(f"%{apellido}%"), Persona.activo == True)
        )
        return result.scalars().all()

    @staticmethod
    async def listar_todos(db: AsyncSession) -> list[Persona]:
        result = await db.execute(select(Persona).where(Persona.activo == True))
        return result.scalars().all()

    @staticmethod
    async def actualizar(db: AsyncSession, persona_id: UUID, data: PersonaActualizar) -> Persona | None:
        result = await db.execute(
            select(Persona).where(Persona.id == persona_id, Persona.activo == True)
        )
        persona = result.scalar_one_or_none()
        if not persona:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(persona, campo, valor)

        await db.commit()
        await db.refresh(persona)
        return persona

    @staticmethod
    async def eliminar_logico(db: AsyncSession, persona_id: UUID, usuario: str) -> bool:
        result = await db.execute(
            select(Persona).where(Persona.id == persona_id, Persona.activo == True)
        )
        persona = result.scalar_one_or_none()
        if not persona:
            return False

        persona.activo = False
        persona.usuario_auditoria = usuario
        await db.commit()
        return True
