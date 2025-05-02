import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

ROL_MOCK_INPUT = {
    "nombre": "ADMIN",
    "descripcion": "Rol administrador del sistema",
    "usuario_auditoria": "admin"
}

ROL_MOCK_OUTPUT = {
    **ROL_MOCK_INPUT,
    "id": "f5d1e69e-1b84-42d4-97f5-8a8e2e54d842",
    "activo": True,
    "fecha_creacion": "2025-04-30T10:00:00",
    "fecha_modificacion": "2025-04-30T10:00:00"
}


@pytest.mark.asyncio
async def test_crear_rol():
    with patch("src.osiris.services.rol_service.RolServicio.crear", new=AsyncMock(return_value=ROL_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/roles/", json=ROL_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["nombre"] == ROL_MOCK_INPUT["nombre"]


@pytest.mark.asyncio
async def test_actualizar_rol():
    with patch("src.osiris.services.rol_service.RolServicio.actualizar", new=AsyncMock(return_value=ROL_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(f"/roles/{ROL_MOCK_OUTPUT['id']}", json={
                "descripcion": "Rol administrativo",
                "usuario_auditoria": "admin"
            })

        assert response.status_code == 200
        assert response.json()["id"] == ROL_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_rol():
    with patch("src.osiris.services.rol_service.RolServicio.eliminar", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/roles/{ROL_MOCK_OUTPUT['id']}?usuario=admin")

        assert response.status_code == 200
        assert response.json()["mensaje"] == "Rol eliminado correctamente."


@pytest.mark.asyncio
async def test_listar_roles():
    with patch("src.osiris.services.rol_service.RolServicio.listar", new=AsyncMock(return_value=[ROL_MOCK_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/roles/")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["nombre"] == ROL_MOCK_INPUT["nombre"]
