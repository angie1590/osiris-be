from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from src.osiris.db.entities.usuario_entity import Usuario
from src.osiris.models.usuario_model import UsuarioCrear, UsuarioActualizar

class UsuarioRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: UsuarioCrear, password_hash: str) -> Usuario:
        nuevo_usuario = Usuario(
            persona_id=data.persona_id,
            rol_id=data.rol_id,
            username=data.username,
            password_hash=password_hash,
            usuario_auditoria=data.usuario_auditoria
        )
        db.add(nuevo_usuario)
        await db.commit()
        await db.refresh(nuevo_usuario)
        return nuevo_usuario

    @staticmethod
    async def obtener_por_username(db: AsyncSession, username: str) -> Usuario | None:
        result = await db.execute(
            select(Usuario).where(Usuario.username == username, Usuario.activo == True)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def actualizar(db: AsyncSession, usuario_id: UUID, data: UsuarioActualizar, password_hash: str | None = None) -> Usuario | None:
        result = await db.execute(select(Usuario).where(Usuario.id == usuario_id, Usuario.activo == True))
        usuario = result.scalar_one_or_none()
        if not usuario:
            return None

        for campo, valor in data.model_dump(exclude_unset=True, exclude={"password"}).items():
            setattr(usuario, campo, valor)

        if password_hash:
            usuario.password_hash = password_hash

        await db.commit()
        await db.refresh(usuario)
        return usuario

    @staticmethod
    async def eliminar_logico(db: AsyncSession, usuario_id: UUID, usuario_auditor: str) -> bool:
        result = await db.execute(select(Usuario).where(Usuario.id == usuario_id, Usuario.activo == True))
        usuario = result.scalar_one_or_none()
        if not usuario:
            return False

        usuario.activo = False
        usuario.usuario_auditoria = usuario_auditor
        await db.commit()
        return True
