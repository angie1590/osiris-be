from unittest.mock import AsyncMock, patch
import pytest
from httpx import ASGITransport, AsyncClient
from src.osiris.main import app

PUNTO_EMISION_MOCK_INPUT = {
  "codigo": "001",
  "descripcion": "PUNTO EMISION SUCURSAL 1",
  "secuencial_actual": 1,
  "empresa_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "sucursal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}

PUNTO_EMISION_MOCK_OUTPUT = {
  "codigo": "001",
  "descripcion": "PUNTO EMISION SUCURSAL 1",
  "secuencial_actual": 1,
  "empresa_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "sucursal_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "activo": True,
  "fecha_creacion": "2025-04-30T10:00:00",
  "fecha_modificacion": "2025-04-30T10:00:00",
  "usuario_auditoria": "admin"
}

@pytest.mark.asyncio
async def test_crear_punto_emision():
    with patch("src.osiris.services.punto_emision_service.PuntoEmisionServicio.crear", new=AsyncMock(return_value=PUNTO_EMISION_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/puntos-emision/", json=PUNTO_EMISION_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["codigo"] == PUNTO_EMISION_MOCK_INPUT["codigo"]

@pytest.mark.asyncio
async def test_listar_puntos_emision():
    with patch("src.osiris.services.punto_emision_service.PuntoEmisionServicio.listar", new=AsyncMock(return_value=[PUNTO_EMISION_MOCK_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/puntos-emision/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["codigo"] == PUNTO_EMISION_MOCK_INPUT["codigo"]

@pytest.mark.asyncio
async def test_actualizar_punto_emision():
    with patch("src.osiris.services.punto_emision_service.PuntoEmisionServicio.actualizar", new=AsyncMock(return_value=PUNTO_EMISION_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.patch(f"/puntos-emision/{PUNTO_EMISION_MOCK_OUTPUT['id']}", json={"descripcion": "PUNTO SUCURSAL 001"})

        assert response.status_code == 200
        assert response.json()["id"] == PUNTO_EMISION_MOCK_OUTPUT["id"]

@pytest.mark.asyncio
async def test_eliminar_punto_emision():
    with patch("src.osiris.services.punto_emision_service.PuntoEmisionServicio.eliminar_logico", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/puntos-emision/{PUNTO_EMISION_MOCK_OUTPUT['id']}")

        assert response.status_code == 204
