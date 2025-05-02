import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
from src.osiris.main import app

EMPLEADO_MOCK_INPUT = {
    "persona_id": "4e90ff1e-ccf7-4f6e-81b3-d353e2c82f6c",
    "salario": 1500.00,
    "cargo": "Analista",
    "fecha_ingreso": "2023-01-10",
    "fecha_nacimiento": "1990-05-20",
    "usuario_auditoria": "admin"
}

EMPLEADO_MOCK_OUTPUT = {
    **EMPLEADO_MOCK_INPUT,
    "id": "ba72dc7b-29a3-4c53-a116-5f818d4d3f89",
    "fecha_salida": None,
    "activo": True
}


@pytest.mark.asyncio
async def test_crear_empleado():
    with patch("src.osiris.services.empleado_service.EmpleadoServicio.crear", new=AsyncMock(return_value=EMPLEADO_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/empleados/", json=EMPLEADO_MOCK_INPUT)

        assert response.status_code == 201
        assert response.json()["persona_id"] == EMPLEADO_MOCK_INPUT["persona_id"]


@pytest.mark.asyncio
async def test_actualizar_empleado():
    with patch("src.osiris.services.empleado_service.EmpleadoServicio.actualizar", new=AsyncMock(return_value=EMPLEADO_MOCK_OUTPUT)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.put(
                f"/empleados/{EMPLEADO_MOCK_OUTPUT['id']}",
                json={"cargo": "Senior Analyst", "usuario_auditoria": "admin"}
            )

        assert response.status_code == 200
        assert response.json()["id"] == EMPLEADO_MOCK_OUTPUT["id"]


@pytest.mark.asyncio
async def test_eliminar_empleado():
    with patch("src.osiris.services.empleado_service.EmpleadoServicio.eliminar", new=AsyncMock(return_value=None)):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.delete(f"/empleados/{EMPLEADO_MOCK_OUTPUT['id']}?usuario=admin")

        assert response.status_code == 200
        assert response.json()["mensaje"] == "Empleado eliminado correctamente."


@pytest.mark.asyncio
async def test_listar_empleados():
    with patch("src.osiris.services.empleado_service.EmpleadoServicio.listar", new=AsyncMock(return_value=[EMPLEADO_MOCK_OUTPUT])):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/empleados/")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["cargo"] == EMPLEADO_MOCK_INPUT["cargo"]
