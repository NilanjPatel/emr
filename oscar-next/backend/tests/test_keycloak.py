"""
Phase 0.4 — Keycloak connectivity tests.
Requires Keycloak running at KEYCLOAK_URL (localhost:8090 in dev).
Run after: docker compose -f oscar-next/docker/docker-compose.yml up -d keycloak
"""
import pytest
import httpx
from app.config import get_settings

settings = get_settings()
KEYCLOAK_BASE = f"{settings.keycloak_url}/realms/{settings.keycloak_realm}"

pytestmark = pytest.mark.skipif(
    "localhost" not in settings.keycloak_url and "keycloak" not in settings.keycloak_url,
    reason="Keycloak URL not configured"
)


async def test_keycloak_realm_reachable():
    """Keycloak oscar realm must be accessible."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{KEYCLOAK_BASE}/.well-known/openid-configuration")
    assert response.status_code == 200, (
        f"Keycloak not reachable at {KEYCLOAK_BASE} — "
        f"run: docker compose -f oscar-next/docker/docker-compose.yml up -d keycloak"
    )


async def test_keycloak_jwks_endpoint():
    """JWKS endpoint must return at least one RS256 key."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{KEYCLOAK_BASE}/protocol/openid-connect/certs")
    assert response.status_code == 200
    keys = response.json().get("keys", [])
    assert len(keys) > 0, "No signing keys found in JWKS endpoint"
    rs256_keys = [k for k in keys if k.get("alg") == "RS256" or k.get("kty") == "RSA"]
    assert len(rs256_keys) > 0, "No RS256 keys found — JWT validation will fail"


async def test_keycloak_oscar_realm_configured():
    """Oscar realm must have the expected clients registered."""
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{KEYCLOAK_BASE}/.well-known/openid-configuration")
    assert response.status_code == 200
    config = response.json()
    assert config["issuer"] == KEYCLOAK_BASE
    assert "authorization_endpoint" in config
    assert "token_endpoint" in config
    assert "jwks_uri" in config
    # SMART on FHIR custom scopes must be present
    scopes = config.get("scopes_supported", [])
    assert "openid" in scopes
    assert "fhir/Patient.read" in scopes


async def test_jwks_url_in_settings():
    """Settings must produce a valid JWKS URL."""
    jwks_url = settings.jwks_url
    assert settings.keycloak_realm in jwks_url
    assert "openid-connect/certs" in jwks_url
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
    assert response.status_code == 200
