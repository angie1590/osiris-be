from __future__ import annotations

"""
Configuración global para smoke tests.
Los smoke tests se ejecutan contra el backend en localhost:8000.
"""

import pytest
import httpx
from sqlmodel import Session

from osiris.core.db import engine
from tests.smoke.utils import BASE, TIMEOUT, is_port_open, wait_for_service


@pytest.fixture(scope="session")
def client() -> httpx.Client:
    if not is_port_open("localhost", 8000):
        pytest.skip("Smoke tests requieren backend escuchando en localhost:8000")
    if not wait_for_service("/docs", timeout=20):
        pytest.skip("Smoke tests requieren backend listo en /docs")

    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as http_client:
        yield http_client


@pytest.fixture
def db_session() -> Session:
    with Session(engine) as session:
        yield session
