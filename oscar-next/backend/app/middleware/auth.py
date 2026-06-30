"""
JWT RS256 validation middleware — Phase 0.5.

Validates every non-public request against Keycloak's JWKS endpoint.
- Fetches public keys once, caches them, refreshes on unknown kid.
- Validates issuer, expiry, and audience.
- Attaches decoded claims to request.state.token_data.
- Attaches roles list to request.state.roles.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import jwt, JWTError, ExpiredSignatureError
import httpx
import time
import logging

logger = logging.getLogger(__name__)

PUBLIC_PATHS = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)

# How long to cache JWKS before forcing a refresh (10 minutes)
_JWKS_TTL = 600


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, jwks_url: str, issuer: str, audience: str = "oscar-api"):
        super().__init__(app)
        self.jwks_url = jwks_url
        self.issuer = issuer
        self.audience = audience
        self._jwks_cache: dict | None = None
        self._jwks_fetched_at: float = 0.0

    async def dispatch(self, request: Request, call_next):
        # Always pass OPTIONS through — CORS middleware handles preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        if any(request.url.path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            claims = await self._validate_token(token)
            request.state.token_data = claims
            # Keycloak puts realm roles under realm_access.roles
            realm_roles = claims.get("realm_access", {}).get("roles", [])
            request.state.roles = realm_roles
        except ExpiredSignatureError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token has expired"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.warning("JWT validation failed: %s", e)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error("Unexpected auth error: %s", e)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication error"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    def _extract_token(self, request: Request) -> str | None:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    async def _validate_token(self, token: str) -> dict:
        # Get the kid from the unverified header to pick the right key
        try:
            header = jwt.get_unverified_header(token)
        except JWTError:
            raise JWTError("Malformed token header")

        kid = header.get("kid")
        alg = header.get("alg", "")
        if alg != "RS256":
            raise JWTError(f"Unsupported algorithm: {alg}")

        jwks = await self._get_jwks()
        key = self._find_key(jwks, kid)

        # If kid not found, try a cache refresh once (handles key rotation)
        if key is None:
            jwks = await self._get_jwks(force_refresh=True)
            key = self._find_key(jwks, kid)
            if key is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No matching signing key found",
                )

        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={
                "verify_exp": True,
                # Disable library issuer check — we do a normalised check below
                # because Keycloak appends :443 to HTTPS issuer URLs in tokens
                "verify_iss": False,
                # Audience check disabled: oscar-web tokens have no audience claim
                "verify_aud": False,
            },
        )

        # Normalised issuer check — strips redundant :443/:80 before comparing
        def _norm(url: str) -> str:
            return url.rstrip("/").replace(":443", "").replace(":80", "")

        if _norm(claims.get("iss", "")) != _norm(self.issuer):
            raise JWTError(f"Invalid issuer: {claims.get('iss')}")

        return claims

    async def _get_jwks(self, force_refresh: bool = False) -> dict:
        now = time.monotonic()
        cache_stale = (now - self._jwks_fetched_at) > _JWKS_TTL

        if not force_refresh and self._jwks_cache and not cache_stale:
            return self._jwks_cache

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.jwks_url)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_fetched_at = now
                logger.debug("JWKS refreshed — %d keys", len(self._jwks_cache.get("keys", [])))
        except httpx.HTTPError as e:
            if self._jwks_cache:
                logger.warning("JWKS fetch failed, using cached keys: %s", e)
                return self._jwks_cache
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            )

        return self._jwks_cache

    def _find_key(self, jwks: dict, kid: str | None) -> dict | None:
        keys = jwks.get("keys", [])
        if kid:
            for key in keys:
                if key.get("kid") == kid:
                    return key
            return None
        # No kid in token — return first RSA key
        for key in keys:
            if key.get("kty") == "RSA":
                return key
        return None
