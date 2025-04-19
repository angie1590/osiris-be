"""
Servicio de negocio para la entidad Empresa. Aplica la lógica de validaciones y transformaciones
necesarias antes de interactuar con la capa de persistencia. Cumple con el principio de
Responsabilidad Única (SRP) y el principio de Inversión de Dependencias (DIP).
"""
from src.osiris.models.empresa_model import EmpresaCrear, EmpresaActualizar
from src.osiris.db.entities.empresa_entity import Empresa
from src.osiris.db.repositories.empresa_repository import RepositorioEmpresa
from uuid import UUID
from typing import List


class EmpresaServicio:
    def __init__(self, repositorio: RepositorioEmpresa):
        self.repositorio = repositorio

    async def listar_empresas(self) -> List[Empresa]:
        return await self.repositorio.obtener_todas()

    async def obtener_por_id(self, empresa_id: UUID) -> Empresa:
        empresa = await self.repositorio.obtener_por_id(empresa_id)
        if not empresa:
            raise ValueError("Empresa no encontrada")
        return empresa

    async def crear_empresa(self, datos: EmpresaCrear) -> Empresa:
        existe = await self.repositorio.obtener_por_ruc(datos.ruc)
        if existe:
            raise ValueError("Ya existe una empresa registrada con este RUC")
        empresa = Empresa(**datos.dict())
        nueva_empresa = await self.repositorio.crear(empresa)
        return nueva_empresa  # este sí debe incluir el ID

    async def actualizar_empresa(self, empresa_id: UUID, datos: EmpresaActualizar) -> Empresa:
        empresa = await self.obtener_por_id(empresa_id)
        for campo, valor in datos.dict(exclude_unset=True).items():
            setattr(empresa, campo, valor)
        return await self.repositorio.actualizar(empresa)

    async def eliminar_empresa(self, empresa_id: UUID):
        empresa = await self.obtener_por_id(empresa_id)
        await self.repositorio.eliminar_logicamente(empresa)
