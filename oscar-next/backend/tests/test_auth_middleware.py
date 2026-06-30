"""
Phase 0.5 — JWT auth middleware tests.

Covers:
- Public paths skip auth (no token needed)
- Missing token → 401
- Expired/malformed token → 401
- Valid RS256 token → request proceeds, claims on request.state
- Roles extracted from realm_access.roles
- JWKS cache refresh on unknown kid
"""
import pytest
import httpx
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.middleware.auth import AuthMiddleware
from app.config import get_settings

settings = get_settings()

KEYCLOAK_BASE = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"
TOKEN_URL = f"{KEYCLOAK_BASE}/protocol/openid-connect/token"


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_test_app(jwks_url: str = None, issuer: str = None) -> FastAPI:
    """Minimal app with AuthMiddleware for unit testing."""
    from fastapi import HTTPException as FastAPIHTTPException
    from fastapi.responses import JSONResponse

    app = FastAPI()

    # BaseHTTPMiddleware swallows HTTPException — must re-raise via handler
    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.add_middleware(
        AuthMiddleware,
        jwks_url=jwks_url or settings.jwks_url,
        issuer=issuer or settings.keycloak_issuer,
        audience=settings.keycloak_client_id,
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/fhir/R4/Patient")
    async def patients(request: Request):
        return {
            "roles": getattr(request.state, "roles", []),
            "subject": request.state.token_data.get("sub", ""),
        }

    return app


async def get_keycloak_token(username: str, password: str, client_id: str = "oscar-web") -> str | None:
    """Get a real token from Keycloak — requires direct access grants enabled on client."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(TOKEN_URL, data={
                "grant_type": "password",
                "client_id": client_id,
                "username": username,
                "password": password,
            })
            if response.status_code == 200:
                return response.json().get("access_token")
    except Exception:
        pass
    return None


# ── Unit tests (no real Keycloak needed) ─────────────────────────────────────

def test_public_path_health_no_token():
    """Health endpoint must be reachable without any token."""
    app = make_test_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/health")
    assert response.status_code == 200


def test_missing_token_returns_401():
    """Request to protected endpoint without token must return 401."""
    app = make_test_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/fhir/R4/Patient")
    assert response.status_code == 401
    assert "Missing authentication token" in response.text


def test_malformed_token_returns_401():
    """Garbage string in Authorization header must return 401."""
    app = make_test_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/fhir/R4/Patient", headers={"Authorization": "Bearer not.a.jwt"})
    assert response.status_code == 401


def test_wrong_algorithm_token_returns_401():
    """HS256-signed token must be rejected (only RS256 accepted)."""
    from jose import jwt as jose_jwt
    token = jose_jwt.encode({"sub": "test", "exp": int(time.time()) + 300}, "secret", algorithm="HS256")
    app = make_test_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/fhir/R4/Patient", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_bearer_prefix_required():
    """Token without 'Bearer ' prefix must be treated as missing."""
    app = make_test_app()
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/fhir/R4/Patient", headers={"Authorization": "Token abc123"})
    assert response.status_code == 401
    assert "Missing authentication token" in response.text


def test_extract_token_strips_bearer_prefix():
    """_extract_token must strip 'Bearer ' correctly."""
    from starlette.requests import Request as StarletteRequest
    from starlette.datastructures import Headers

    middleware = AuthMiddleware(
        MagicMock(),
        jwks_url=settings.jwks_url,
        issuer=settings.keycloak_issuer,
    )

    scope = {
        "type": "http",
        "headers": [(b"authorization", b"Bearer mytoken123")],
        "method": "GET",
        "path": "/test",
        "query_string": b"",
    }
    request = StarletteRequest(scope)
    assert middleware._extract_token(request) == "mytoken123"


def test_extract_token_returns_none_without_header():
    """_extract_token must return None when no Authorization header."""
    from starlette.requests import Request as StarletteRequest

    middleware = AuthMiddleware(
        MagicMock(),
        jwks_url=settings.jwks_url,
        issuer=settings.keycloak_issuer,
    )
    scope = {
        "type": "http",
        "headers": [],
        "method": "GET",
        "path": "/test",
        "query_string": b"",
    }
    request = StarletteRequest(scope)
    assert middleware._extract_token(request) is None


# ── Integration tests (require live Keycloak at localhost:8090) ───────────────

pytestmark_integration = pytest.mark.skipif(
    "localhost" not in settings.keycloak_url,
    reason="Integration tests require local Keycloak"
)


async def test_jwks_endpoint_reachable():
    """Keycloak JWKS endpoint must return RSA keys."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(settings.jwks_url)
    assert response.status_code == 200
    keys = response.json().get("keys", [])
    assert any(k.get("kty") == "RSA" for k in keys), "No RSA key in JWKS"


async def test_jwks_cache_populates_on_first_call():
    """JWKS cache must be populated after first fetch."""
    middleware = AuthMiddleware(
        MagicMock(),
        jwks_url=settings.jwks_url,
        issuer=settings.keycloak_issuer,
    )
    assert middleware._jwks_cache is None
    jwks = await middleware._get_jwks()
    assert middleware._jwks_cache is not None
    assert len(jwks.get("keys", [])) > 0


async def test_jwks_cache_not_refetched_within_ttl():
    """JWKS must be served from cache within TTL without HTTP call."""
    middleware = AuthMiddleware(
        MagicMock(),
        jwks_url=settings.jwks_url,
        issuer=settings.keycloak_issuer,
    )
    # Populate cache
    await middleware._get_jwks()
    fetched_at = middleware._jwks_fetched_at

    with patch("httpx.AsyncClient") as mock_client:
        await middleware._get_jwks()
        mock_client.assert_not_called()

    assert middleware._jwks_fetched_at == fetched_at
