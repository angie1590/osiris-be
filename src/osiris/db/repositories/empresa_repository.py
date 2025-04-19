"""
Repositorio para la entidad Empresa, ubicado en src/osiris/db/repositories/empresa_repository.py.
Encargado de interactuar con la base de datos para operaciones CRUD.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from src.osiris.db.entities.empresa_entity import Empresa
from uuid import UUID
from typing import List, Optional


class RepositorioEmpresa:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def obtener_todas(self) -> List[Empresa]:
        resultado = await self.session.execute(select(Empresa).where(Empresa.activo == True))
        return resultado.scalars().all()

    async def obtener_por_id(self, empresa_id: UUID) -> Optional[Empresa]:
        resultado = await self.session.execute(select(Empresa).where(Empresa.id == empresa_id, Empresa.activo == True))
        return resultado.scalar_one_or_none()

    async def obtener_por_ruc(self, ruc: str) -> Optional[Empresa]:
        resultado = await self.session.execute(select(Empresa).where(Empresa.ruc == ruc, Empresa.activo == True))
        return resultado.scalar_one_or_none()

    async def crear(self, empresa: Empresa) -> Empresa:
        self.session.add(empresa)
        await self.session.flush()
        await self.session.refresh(empresa)
        return empresa

    async def actualizar(self, empresa: Empresa) -> Empresa:
        await self.session.commit()
        await self.session.refresh(empresa)
        return empresa

    async def eliminar_logicamente(self, empresa: Empresa):
        empresa.activo = False
        await self.session.commit()