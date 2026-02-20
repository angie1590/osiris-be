from __future__ import annotations

import pytest


pytestmark = pytest.mark.smoke


def test_smoke_audit_logs_listado(client):
    response = client.get("/v1/audit-logs", params={"limit": 10, "offset": 0})
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, list)
