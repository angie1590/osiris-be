import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

USUARIO_MOCK_INPUT = {
    "persona_id": "f1d58e22-e6d5-4a3f-a40c-01960d7e9e7e",
    "rol_id": "c3bb2ad7-60ef-4559-8e4d-0a498b9e1271",
    "username": "jdoe",
    "password": "Segura123",
    "usuario_auditoria": "admin"
}

USUARIO_MOCK_OUTPUT = {
    "id": "89d40991-3a42-45ce-9446-01234f07caaa",
    "persona_id": USUARIO_MOCK_INPUT["persona_id"],
    "rol_id": USUARIO_MOCK_INPUT["rol_id"],
    "username": USUARIO_MOCK_INPUT["username"],
    "requiere_cambio_password": True,
    "activo": True,
    "usuario_auditoria": USUARIO_MOCK_INPUT["usuario_auditoria"]
}


@pytest.mark.asyncio
async def test_crear_usuario():
    with patch("src.osiris.services.usuario_service.UsuarioServicio.crear", new=AsyncMock(return_value=USUARIO_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/usuarios/", json=USUARIO_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["username"] == USUARIO_MOCK_INPUT["username"]


@pytest.mark.asyncio
async def test_actualizar_usuario():
    with patch("src.osiris.services.usuario_service.UsuarioServicio.actualizar", new=AsyncMock(return_value=USUARIO_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(f"/usuarios/{USUARIO_MOCK_OUTPUT['id']}", json={
                "rol_id": USUARIO_MOCK_INPUT["rol_id"],
                "usuario_auditoria": "admin"
            })

        assert response.status_code == 200
        assert response.json()["id"] == USUARIO_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_usuario():
    with patch("src.osiris.services.usuario_service.UsuarioServicio.eliminar", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/usuarios/{USUARIO_MOCK_OUTPUT['id']}?usuario=admin")

        assert response.status_code == 200
        assert response.json()["mensaje"] == "Usuario eliminado correctamente."
