import socket
import time
import functools
import logging
from typing import Callable

import httpx

BASE = "http://localhost:8000/api"
TIMEOUT = 10.0


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def wait_for_service(path: str = "/docs", timeout: int = 30, interval: float = 0.5) -> bool:
    """Espera hasta que la ruta `http://localhost:8000{path}` responda 200 o hasta agotar `timeout`.
    Devuelve True si el servicio respondió 200 dentro del timeout, False en caso contrario.
    """
    url = f"http://localhost:8000{path}"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(url, timeout=2.0)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval)
    return False


def retry_on_exception(retries: int = 3, backoff: float = 0.5):
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    response = fn(*args, **kwargs)
                    # si devuelve Response, verificar código exitoso
                    if hasattr(response, "status_code"):
                        if response.status_code < 500:  # 2xx/3xx/4xx son "ok"
                            return response
                        raise Exception(f"HTTP {response.status_code}")
                    return response
                except Exception as exc:
                    last_exc = exc
                    if attempt < retries:  # no dormir en el último intento
                        time.sleep(backoff * attempt)
            # re-raise the last exception
            raise last_exc

        return wrapper

    return decorator


def get_client():
    return httpx.Client(timeout=TIMEOUT)
