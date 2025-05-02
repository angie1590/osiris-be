from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from src.osiris.models.usuario_model import UsuarioCrear, UsuarioActualizar
from src.osiris.db.entities.usuario_entity import Usuario
from src.osiris.db.repositories.usuario_repository import UsuarioRepositorio
from src.osiris.db.repositories.empleado_repository import EmpleadoRepositorio
from src.osiris.db.repositories.cliente_repository import ClienteRepositorio
from passlib.hash import bcrypt

class UsuarioServicio:

    @staticmethod
    async def crear(db: AsyncSession, data: UsuarioCrear) -> Usuario:
        # Validar existencia en Empleado o Cliente
        empleado = await EmpleadoRepositorio.obtener_por_id(db, data.persona_id)
        cliente = await ClienteRepositorio.obtener_por_id(db, data.persona_id)

        if not empleado and not cliente:
            raise ValueError("Solo los empleados o clientes pueden tener acceso al sistema.")

        # Validar username único
        existente = await UsuarioRepositorio.obtener_por_username(db, data.username)
        if existente:
            raise ValueError("Ya existe un usuario con ese nombre.")

        password_hash = bcrypt.hash(data.password)
        return await UsuarioRepositorio.crear(db, data, password_hash)

    @staticmethod
    async def actualizar(db: AsyncSession, usuario_id: UUID, data: UsuarioActualizar) -> Usuario:
        password_hash = bcrypt.hash(data.password) if data.password else None
        usuario = await UsuarioRepositorio.actualizar(db, usuario_id, data, password_hash)
        if not usuario:
            raise ValueError("Usuario no encontrado o inactivo.")
        return usuario

    @staticmethod
    async def eliminar(db: AsyncSession, usuario_id: UUID, usuario: str) -> None:
        eliminado = await UsuarioRepositorio.eliminar_logico(db, usuario_id, usuario)
        if not eliminado:
            raise ValueError("Usuario no encontrado o inactivo.")
