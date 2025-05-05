import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

PROVEEDOR_PERSONA_INPUT = {
    "id": "4528a702-fc57-4a80-a1c5-4f8704f179d3",
    "tipo_contribuyente_id": "02",
    "nombre_comercial": "Negocio Don José",
    "usuario_auditoria": "admin"
}

PROVEEDOR_PERSONA_OUTPUT = {
    "id": PROVEEDOR_PERSONA_INPUT["id"],
    "tipo_contribuyente_id": PROVEEDOR_PERSONA_INPUT["tipo_contribuyente_id"],
    "nombre_comercial": PROVEEDOR_PERSONA_INPUT["nombre_comercial"],
    "activo": True,
    "fecha_creacion": "2025-05-02T10:00:00",
    "fecha_modificacion": "2025-05-02T10:00:00",
    "usuario_auditoria": "admin"
}


@pytest.mark.asyncio
async def test_crear_proveedor_persona():
    with patch("src.osiris.services.proveedor_persona_service.ProveedorPersonaServicio.crear", new=AsyncMock(return_value=PROVEEDOR_PERSONA_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/proveedores-persona/", json=PROVEEDOR_PERSONA_INPUT)

        assert response.status_code == 201
        assert response.json()["nombre_comercial"] == PROVEEDOR_PERSONA_INPUT["nombre_comercial"]


@pytest.mark.asyncio
async def test_actualizar_proveedor_persona():
    with patch("src.osiris.services.proveedor_persona_service.ProveedorPersonaServicio.actualizar", new=AsyncMock(return_value=PROVEEDOR_PERSONA_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(
                f"/proveedores-persona/{PROVEEDOR_PERSONA_OUTPUT['id']}",
                json={"nombre_comercial": "Negocio Don Pedro", "usuario_auditoria": "admin"}
            )

        assert response.status_code == 200
        assert response.json()["id"] == PROVEEDOR_PERSONA_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_proveedor_persona():
    with patch("src.osiris.services.proveedor_persona_service.ProveedorPersonaServicio.eliminar", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/proveedores-persona/{PROVEEDOR_PERSONA_OUTPUT['id']}?usuario=admin")

        assert response.status_code == 200
        assert response.json()["mensaje"] == "Proveedor eliminado correctamente."


@pytest.mark.asyncio
async def test_listar_proveedores_persona():
    with patch("src.osiris.services.proveedor_persona_service.ProveedorPersonaServicio.listar", new=AsyncMock(return_value=[PROVEEDOR_PERSONA_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/proveedores-persona/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["tipo_contribuyente_id"] == PROVEEDOR_PERSONA_INPUT["tipo_contribuyente_id"]
