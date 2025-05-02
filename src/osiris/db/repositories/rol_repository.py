from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.rol_entity import Rol
from src.osiris.models.rol_model import RolCrear, RolActualizar

class RolRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: RolCrear) -> Rol:
        nuevo_rol = Rol(**data.model_dump())
        db.add(nuevo_rol)
        await db.commit()
        await db.refresh(nuevo_rol)
        return nuevo_rol

    @staticmethod
    async def listar_todos(db: AsyncSession) -> list[Rol]:
        result = await db.execute(select(Rol).where(Rol.activo == True))
        return result.scalars().all()

    @staticmethod
    async def obtener_por_nombre(db: AsyncSession, nombre: str) -> Rol | None:
        result = await db.execute(select(Rol).where(Rol.nombre == nombre))
        return result.scalar_one_or_none()

    @staticmethod
    async def actualizar(db: AsyncSession, rol_id: UUID, data: RolActualizar) -> Rol | None:
        result = await db.execute(select(Rol).where(Rol.id == rol_id, Rol.activo == True))
        rol = result.scalar_one_or_none()
        if not rol:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(rol, campo, valor)

        await db.commit()
        await db.refresh(rol)
        return rol

    @staticmethod
    async def eliminar_logico(db: AsyncSession, rol_id: UUID, usuario: str) -> bool:
        result = await db.execute(select(Rol).where(Rol.id == rol_id, Rol.activo == True))
        rol = result.scalar_one_or_none()
        if not rol:
            return False

        rol.activo = False
        rol.usuario_auditoria = usuario
        await db.commit()
        return True
