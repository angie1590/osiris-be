import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

TIPO_CLIENTE_MOCK_INPUT = {
    "nombre": "VIP",
    "descuento": 10.00
}

TIPO_CLIENTE_MOCK_OUTPUT = {
    "id": "11111111-1111-1111-1111-111111111111",
    "nombre": "VIP",
    "descuento": 10.00
}


@pytest.mark.asyncio
async def test_crear_tipo_cliente():
    with patch("src.osiris.services.tipo_cliente_service.TipoClienteServicio.crear", new=AsyncMock(return_value=TIPO_CLIENTE_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/tipos-cliente/", json=TIPO_CLIENTE_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["nombre"] == TIPO_CLIENTE_MOCK_INPUT["nombre"]


@pytest.mark.asyncio
async def test_actualizar_tipo_cliente():
    with patch("src.osiris.services.tipo_cliente_service.TipoClienteServicio.actualizar", new=AsyncMock(return_value=TIPO_CLIENTE_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(
                f"/tipos-cliente/{TIPO_CLIENTE_MOCK_OUTPUT['id']}",
                json={"descuento": 15.00}
            )

        assert response.status_code == 200
        assert response.json()["id"] == TIPO_CLIENTE_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_listar_tipos_cliente():
    with patch("src.osiris.services.tipo_cliente_service.TipoClienteServicio.listar", new=AsyncMock(return_value=[TIPO_CLIENTE_MOCK_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/tipos-cliente/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["nombre"] == TIPO_CLIENTE_MOCK_OUTPUT["nombre"]
