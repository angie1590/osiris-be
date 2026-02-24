from __future__ import annotations

import base64
import json
import os
from contextvars import ContextVar, Token
from typing import Optional


_current_user_id: ContextVar[Optional[str]] = ContextVar("current_user_id", default=None)


def set_current_user_id(user_id: Optional[str]) -> Token:
    return _current_user_id.set(user_id)


def reset_current_user_id(token: Token) -> None:
    _current_user_id.reset(token)


def get_current_user_id() -> Optional[str]:
    return _current_user_id.get()


def _allows_x_user_id_header() -> bool:
    """
    X-User-Id se permite solo en entornos no productivos para pruebas
    técnicas/smoke. En producción se exige Authorization.
    """
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    return environment in {"development", "dev", "test", "testing", "local", "ci"}


def extract_user_id_from_request_headers(*, authorization: Optional[str], x_user_id: Optional[str]) -> Optional[str]:
    # Canal principal: Authorization.
    if authorization:
        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token.split(" ", 1)[1].strip()

        # Fallback simple: si el token no es JWT, lo tratamos como ID plano.
        if "." not in token:
            return token or None

        try:
            _header, payload_b64, _signature = token.split(".", 2)
            padding = "=" * ((4 - len(payload_b64) % 4) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
            payload = json.loads(payload_json)
            user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
            if user_id:
                return str(user_id)
        except Exception:
            # Si Authorization viene corrupto, no hacemos fallback a X-User-Id.
            return None

    # Canal auxiliar solo para dev/test/local/ci.
    if x_user_id and _allows_x_user_id_header():
        return x_user_id

    return None
