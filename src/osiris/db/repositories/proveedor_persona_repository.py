from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.osiris.db.entities.proveedor_persona_entity import ProveedorPersona
from src.osiris.models.proveedor_persona_model import ProveedorPersonaCrear, ProveedorPersonaActualizar

class ProveedorPersonaRepositorio:

    @staticmethod
    async def crear(db: AsyncSession, data: ProveedorPersonaCrear) -> ProveedorPersona:
        nuevo = ProveedorPersona(
            id=data.id,
            nombre_comercial=data.nombre_comercial,
            tipo_contribuyente_id=data.tipo_contribuyente_id,
            usuario_auditoria=data.usuario_auditoria
        )
        db.add(nuevo)
        await db.commit()
        await db.refresh(nuevo)
        return nuevo

    @staticmethod
    async def listar(db: AsyncSession) -> list[ProveedorPersona]:
        result = await db.execute(select(ProveedorPersona).where(ProveedorPersona.activo == True))
        return result.scalars().all()

    @staticmethod
    async def actualizar(db: AsyncSession, proveedor_id: str, data: ProveedorPersonaActualizar) -> ProveedorPersona | None:
        result = await db.execute(select(ProveedorPersona).where(ProveedorPersona.id == proveedor_id, ProveedorPersona.activo == True))
        proveedor = result.scalar_one_or_none()
        if not proveedor:
            return None

        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(proveedor, campo, valor)

        await db.commit()
        await db.refresh(proveedor)
        return proveedor

    @staticmethod
    async def eliminar_logico(db: AsyncSession, proveedor_id: str, usuario: str) -> bool:
        result = await db.execute(select(ProveedorPersona).where(ProveedorPersona.id == proveedor_id, ProveedorPersona.activo == True))
        proveedor = result.scalar_one_or_none()
        if not proveedor:
            return False

        proveedor.activo = False
        proveedor.usuario_auditoria = usuario
        await db.commit()
        return True
