import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

PERSONA_MOCK_INPUT = {
    "identificacion": "0104815956",
    "tipo_identificacion": "CEDULA",
    "nombre": "Juan",
    "apellido": "Pérez",
    "direccion": "Av. Loja",
    "telefono": "0999999999",
    "ciudad": "Cuenca",
    "email": "juan.perez@example.com",
    "usuario_auditoria": "admin"
}

PERSONA_MOCK_OUTPUT = {
    **PERSONA_MOCK_INPUT,
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "activo": True,
    "fecha_creacion": "2025-04-30T10:00:00",
    "fecha_modificacion": "2025-04-30T10:00:00"
}


@pytest.mark.asyncio
async def test_crear_persona():
    with patch("src.osiris.services.persona_service.PersonaServicio.crear", new=AsyncMock(return_value=PERSONA_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/personas/", json=PERSONA_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["identificacion"] == PERSONA_MOCK_INPUT["identificacion"]


@pytest.mark.asyncio
async def test_actualizar_persona():
    with patch("src.osiris.services.persona_service.PersonaServicio.actualizar", new=AsyncMock(return_value=PERSONA_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(f"/personas/{PERSONA_MOCK_OUTPUT['id']}", json={
                "telefono": "0888888888",
                "usuario_auditoria": "admin"
            })

        assert response.status_code == 200
        assert response.json()["id"] == PERSONA_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_persona():
    with patch("src.osiris.services.persona_service.PersonaServicio.eliminar", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/personas/{PERSONA_MOCK_OUTPUT['id']}?usuario=admin")

        assert response.status_code == 200
        assert response.json()["mensaje"] == "Persona eliminada correctamente."


@pytest.mark.asyncio
async def test_buscar_por_identificacion():
    with patch("src.osiris.services.persona_service.PersonaServicio.buscar_por_identificacion", new=AsyncMock(return_value=PERSONA_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(f"/personas/buscar?identificacion={PERSONA_MOCK_INPUT['identificacion']}")

        assert response.status_code == 200
        assert response.json()[0]["identificacion"] == PERSONA_MOCK_INPUT["identificacion"]


@pytest.mark.asyncio
async def test_buscar_por_apellido():
    with patch("src.osiris.services.persona_service.PersonaServicio.buscar_por_apellido", new=AsyncMock(return_value=[PERSONA_MOCK_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get(f"/personas/buscar?apellido=Pérez")

        assert response.status_code == 200
        assert response.json()[0]["apellido"] == PERSONA_MOCK_INPUT["apellido"]
