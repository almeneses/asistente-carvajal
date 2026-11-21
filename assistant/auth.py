"""Autenticación multiusuario ligera: PBKDF2 y sesión firmada."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from urllib.parse import quote

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse

from assistant.config import Settings

COOKIE_NAME = "asistente_session"
_PBKDF2_ITERATIONS = 200_000
PUBLIC_PATHS = {"/login", "/logout", "/healthz", "/readyz", "/metrics"}


@dataclass(frozen=True)
class User:
    username: str
    role: str = "user"


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """Genera `pbkdf2_sha256$iteraciones$sal$hash`."""
    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, _PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt_bytes.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_session(user: User, secret: str, ttl_seconds: int) -> str:
    payload = _b64(
        json.dumps(
            {"u": user.username, "r": user.role, "exp": int(time.time()) + ttl_seconds},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signature = _b64(
        hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
    )
    return f"{payload}.{signature}"


def parse_session(token: str, secret: str) -> User | None:
    try:
        payload, signature = token.split(".", 1)
        expected = _b64(
            hmac.new(secret.encode("utf-8"), payload.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(_unb64(payload))
        if int(data.get("exp", 0)) < int(time.time()):
            return None
        username = str(data.get("u", ""))
        if not username:
            return None
        return User(username=username, role=str(data.get("r", "user")))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def current_user(request: Request, settings: Settings) -> User | None:
    if not settings.auth_enabled:
        return User("local", "user")
    if not settings.auth_secret:
        return None
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    user = parse_session(token, settings.auth_secret)
    if user is None:
        return None
    role = "admin" if user.username in settings.auth_admins else "user"
    return User(user.username, role)


def is_public(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/static/")


def build_auth_middleware(settings: Settings):
    """Middleware que adjunta el usuario o bloquea la ruta."""

    async def middleware(request: Request, call_next):
        if not settings.auth_enabled:
            request.state.user = User("local", "user")
            return await call_next(request)
        user = current_user(request, settings)
        if is_public(request.url.path):
            request.state.user = user
            return await call_next(request)
        if user is None:
            accepts_html = "text/html" in request.headers.get("accept", "")
            if request.method == "GET" and accepts_html:
                return RedirectResponse(f"/login?next={quote(request.url.path)}", status_code=303)
            return JSONResponse({"detail": "No autenticado."}, status_code=401)
        request.state.user = user
        return await call_next(request)

    return middleware
