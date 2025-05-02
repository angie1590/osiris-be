import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

CLIENTE_MOCK_INPUT = {
    "id": "f6ff8d8b-73a6-49f4-9438-113c5d9f7a4e",
    "tipo_cliente_id": "1a2b3c4d-5e6f-7a8b-9c0d-abcdef123456",
    "usuario_auditoria": "admin"
}

CLIENTE_MOCK_OUTPUT = {
    "id": "4b9f9261-390a-4fa3-b9d0-1fa2e8e8b22d",
    "id": CLIENTE_MOCK_INPUT["id"],
    "tipo_cliente_id": CLIENTE_MOCK_INPUT["tipo_cliente_id"],
    "activo": True,
    "fecha_creacion": "2025-04-30T10:00:00",
    "fecha_modificacion": "2025-04-30T10:00:00",
    "usuario_auditoria": CLIENTE_MOCK_INPUT["usuario_auditoria"]
}


@pytest.mark.asyncio
async def test_crear_cliente():
    with patch("src.osiris.services.cliente_service.ClienteServicio.crear", new=AsyncMock(return_value=CLIENTE_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/clientes/", json=CLIENTE_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["id"] == CLIENTE_MOCK_INPUT["" \
        "id"]


@pytest.mark.asyncio
async def test_actualizar_cliente():
    with patch("src.osiris.services.cliente_service.ClienteServicio.actualizar", new=AsyncMock(return_value=CLIENTE_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(
                f"/clientes/{CLIENTE_MOCK_OUTPUT['id']}",
                json={"tipo_cliente_id": CLIENTE_MOCK_INPUT["tipo_cliente_id"], "usuario_auditoria": "admin"}
            )

        assert response.status_code == 200
        assert response.json()["id"] == CLIENTE_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_cliente():
    with patch("src.osiris.services.cliente_service.ClienteServicio.eliminar", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/clientes/{CLIENTE_MOCK_OUTPUT['id']}?usuario=admin")

        assert response.status_code == 200
        assert response.json()["mensaje"] == "Cliente eliminado correctamente."


@pytest.mark.asyncio
async def test_listar_clientes():
    with patch("src.osiris.services.cliente_service.ClienteServicio.listar", new=AsyncMock(return_value=[CLIENTE_MOCK_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/clientes/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["tipo_cliente_id"] == CLIENTE_MOCK_INPUT["tipo_cliente_id"]
