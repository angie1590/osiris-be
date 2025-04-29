import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from src.osiris.main import app

SUCURSAL_MOCK_INPUT = {
    "codigo": "002",
    "nombre": "SUCURSAL 1",
    "direccion": "CUENCA",
    "telefono": "0999888777",
    "empresa_id": "08fd3cc1-afe1-4606-af27-b5d78ab8027c",
}

# Resultado que devuelve el servicio mockeado
SUCURSAL_MOCK_OUTPUT = {
    "codigo": "002",
    "nombre": "SUCURSAL 1",
    "direccion": "CUENCA",
    "telefono": "0999888777",
    "empresa_id": "08fd3cc1-afe1-4606-af27-b5d78ab8027c",
    "id": "6b4de6b5-a105-4fe4-8905-671564b9a6d2",
    "activo": True
}

@pytest.mark.asyncio
async def test_crear_sucursal():
    with patch("src.osiris.services.sucursal_service.SucursalServicio.crear", new=AsyncMock(return_value=SUCURSAL_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/sucursales/", json=SUCURSAL_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["nombre"] == SUCURSAL_MOCK_INPUT["nombre"]


@pytest.mark.asyncio
async def test_actualizar_sucursal():
    with patch("src.osiris.services.sucursal_service.SucursalServicio.actualizar", new=AsyncMock(return_value=SUCURSAL_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.patch(f"/sucursales/{SUCURSAL_MOCK_OUTPUT['id']}", json={"telefono": "0988777666"})

        assert response.status_code == 200
        assert response.json()["id"] == SUCURSAL_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_sucursal():
    with patch("src.osiris.services.sucursal_service.SucursalServicio.eliminar_logico", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/sucursales/{SUCURSAL_MOCK_OUTPUT['id']}")

        assert response.status_code == 204
