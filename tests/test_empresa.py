import pytest
from uuid import uuid4
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from src.osiris.main import app
from src.osiris.models.empresa_model import EmpresaCrear

EMPRESA_ID = uuid4()
TIPO_CONTRIBUYENTE_ID = "01"

empresa_mock = {
    "id": str(EMPRESA_ID),
    "razon_social": "Mi Empresa SA",
    "nombre_comercial": "MiComercio",
    "ruc": "0104815956001",
    "direccion_matriz": "Av. Principal 123",
    "telefono": "0999999999",
    "codigo_establecimiento": "001",
    "obligado_contabilidad": True,
    "tipo_contribuyente_id": TIPO_CONTRIBUYENTE_ID,
    "activo": True
}


@pytest.mark.asyncio
async def test_crear_empresa():
    with patch("src.osiris.services.empresa_service.EmpresaServicio.crear_empresa", new=AsyncMock(return_value=empresa_mock)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/empresas/", json=empresa_mock)

        assert response.status_code == 201
        assert response.json()["ruc"] == empresa_mock["ruc"]


@pytest.mark.asyncio
async def test_listar_empresas():
    with patch("src.osiris.services.empresa_service.EmpresaServicio.listar_empresas", new=AsyncMock(return_value=[empresa_mock])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/empresas/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["id"] == str(EMPRESA_ID)


@pytest.mark.asyncio
async def test_actualizar_empresa():
    update_data = {**empresa_mock,"telefono": "0123456789"}

    empresa_actualizada = empresa_mock.copy()
    empresa_actualizada["telefono"] = update_data["telefono"]

    with patch(
        "src.osiris.services.empresa_service.EmpresaServicio.actualizar_empresa",
        new=AsyncMock(return_value=empresa_actualizada),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(f"/empresas/{EMPRESA_ID}", json=update_data)

        assert response.status_code == 200
        assert response.json()["telefono"] == update_data["telefono"]


@pytest.mark.asyncio
async def test_eliminar_empresa():
    with patch("src.osiris.services.empresa_service.EmpresaServicio.eliminar_empresa", new=AsyncMock(return_value=True)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/empresas/{EMPRESA_ID}")

        assert response.status_code == 204

@pytest.mark.asyncio
async def test_empresa_no_encontrada():
    empresa_id_fake = uuid4()

    with patch(
        "src.osiris.db.repositories.empresa_repository.RepositorioEmpresa.obtener_por_id",
        new=AsyncMock(return_value=None)  # fuerza que self.obtener_por_id() devuelva None
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(f"/empresas/{empresa_id_fake}", json=empresa_mock)

        assert response.status_code == 404
        assert response.json()["detail"] == "Empresa no encontrada"


def test_empresa_modelo_valido_con_ruc_correcto():
    empresa = EmpresaCrear(
        razon_social="Mi Empresa Legal",
        nombre_comercial="ComercialLegal",
        ruc="0104815956001",
        direccion_matriz="Av. República",
        telefono="0999999999",
        codigo_establecimiento="001",
        obligado_contabilidad=True,
        tipo_contribuyente_id="privado"
    )
    assert empresa.ruc == "0104815956001"


def test_empresa_modelo_falla_con_ruc_invalido():
    with pytest.raises(ValidationError) as exc_info:
        EmpresaCrear(
            razon_social="Empresa Falsa",
            nombre_comercial="ComercialX",
            ruc="1790012345002",  # inválido
            direccion_matriz="Av. Falsa",
            telefono="0999999999",
            codigo_establecimiento="001",
            obligado_contabilidad=True,
            tipo_contribuyente_id="privado"
        )
    errors = str(exc_info.value)
    assert "RUC o cédula no es válido" in errors


@pytest.mark.parametrize("campo, valor", [
    ("razon_social", "1234"),  # inválido por regex
    ("telefono", "abc1234567"),  # inválido por regex
    ("codigo_establecimiento", "00"),  # inválido por longitud mínima
])
def test_empresa_modelo_falla_con_regex_invalido(campo, valor):
    data = {
        "razon_social": "Mi Empresa",
        "nombre_comercial": "Mi Comercial",
        "ruc": "1790012345001",
        "direccion_matriz": "Av. Principal",
        "telefono": "0999999999",
        "codigo_establecimiento": "001",
        "obligado_contabilidad": False,
        "tipo_contribuyente_id": "publico"
    }
    data[campo] = valor
    with pytest.raises(ValidationError):
        EmpresaCrear(**data)