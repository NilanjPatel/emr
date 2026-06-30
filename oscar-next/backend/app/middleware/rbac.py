"""
RBAC middleware — Phase 0.6.

Maps Keycloak realm roles → Oscar secObjPrivilege permissions.
Reads Oscar's secRole / secObjPrivilege tables (read-only, schema frozen).

Design:
- Keycloak role on the JWT (e.g. "doctor") maps 1:1 to secRole.role_name
- secObjPrivilege defines what each role can do on each object (r/u/x/o)
- This middleware loads the full privilege matrix at startup and caches it
- Per-request: resolves user's roles → merged privilege set → stored on request.state.permissions
- Individual routers use the require_permission() dependency to enforce access

Privilege values from Oscar:
  r = read only
  u = update (read + write)
  x = full access (execute — same as u for our purposes)
  o = owner level (superuser on that object)
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Callable, Awaitable

from fastapi import Request, HTTPException, status, Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Oscar object names → FHIR resource path prefixes
# Used to derive required object from the request path
FHIR_PATH_TO_OSCAR_OBJECT: dict[str, str] = {
    "/fhir/R4/Patient":              "_demographic",
    "/fhir/R4/RelatedPerson":        "_demographic",
    "/fhir/R4/Appointment":          "_appointment",
    "/fhir/R4/Schedule":             "_appointment",
    "/fhir/R4/Slot":                 "_appointment",
    "/fhir/R4/Encounter":            "_encounter",
    "/fhir/R4/Composition":          "_encounter",
    "/fhir/R4/MedicationRequest":    "_rx",
    "/fhir/R4/Medication":           "_rx",
    "/fhir/R4/DiagnosticReport":     "_lab",
    "/fhir/R4/Observation":          "_lab",
    "/fhir/R4/AllergyIntolerance":   "_demographic",
    "/fhir/R4/Condition":            "_encounter",
    "/fhir/R4/Immunization":         "_preventions",
    "/fhir/R4/ImmunizationRecommendation": "_preventions",
    "/fhir/R4/Claim":                "_billing",
    "/fhir/R4/ClaimResponse":        "_billing",
    "/fhir/R4/DocumentReference":    "_document",
    "/fhir/R4/Communication":        "_msg",
    "/fhir/R4/Task":                 "_tickler",
    "/fhir/R4/Practitioner":         "_admin.provider",
    "/fhir/R4/ServiceRequest":       "_consult",
    "/fhir/R4/Questionnaire":        "_eform",
    "/fhir/R4/QuestionnaireResponse": "_eform",
}

# HTTP method → minimum privilege required
METHOD_PRIVILEGE: dict[str, str] = {
    "GET":    "r",
    "HEAD":   "r",
    "POST":   "u",
    "PUT":    "u",
    "PATCH":  "u",
    "DELETE": "x",
}

# Privilege ordering: higher index = more access
PRIVILEGE_ORDER = ["r", "u", "x", "o"]


def _privilege_gte(have: str, need: str) -> bool:
    """Return True if `have` privilege satisfies `need` privilege level."""
    try:
        return PRIVILEGE_ORDER.index(have) >= PRIVILEGE_ORDER.index(need)
    except ValueError:
        return False


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Attaches a permission-check function to request.state.can().
    Does NOT enforce anything itself — enforcement is at the router level
    via the require_permission() dependency, keeping middleware thin.
    """

    async def dispatch(self, request: Request, call_next):
        # Attach a permission resolver using roles already set by AuthMiddleware
        roles: list[str] = getattr(request.state, "roles", [])

        def can(oscar_object: str, privilege: str = "r") -> bool:
            return _roles_have_privilege(roles, oscar_object, privilege)

        request.state.can = can
        request.state.oscar_object = _resolve_oscar_object(request)

        return await call_next(request)


def _resolve_oscar_object(request: Request) -> str | None:
    """Map a FHIR request path to an Oscar secObjPrivilege objectName."""
    path = request.url.path
    for prefix, obj in FHIR_PATH_TO_OSCAR_OBJECT.items():
        if path.startswith(prefix):
            return obj
    return None


def _roles_have_privilege(
    roles: list[str],
    oscar_object: str,
    required_privilege: str,
) -> bool:
    """
    Check cached privilege matrix: do any of these roles have at least
    `required_privilege` on `oscar_object`?
    """
    matrix = _get_privilege_matrix()
    for role in roles:
        privs = matrix.get(role, {})
        have = privs.get(oscar_object)
        if have and _privilege_gte(have, required_privilege):
            return True
    return False


# ── In-process privilege matrix cache ─────────────────────────────────────────
# Loaded once from DB at first use. Cleared by calling _invalidate_privilege_cache().
# Structure: {role_name: {objectName: privilege}}

_privilege_matrix: dict[str, dict[str, str]] | None = None


def _get_privilege_matrix() -> dict[str, dict[str, str]]:
    """Return the cached matrix. Raises if not yet populated (call load_privilege_matrix first)."""
    if _privilege_matrix is None:
        return {}
    return _privilege_matrix


def _invalidate_privilege_cache() -> None:
    global _privilege_matrix
    _privilege_matrix = None


async def load_privilege_matrix(db: AsyncSession) -> None:
    """
    Load the full secObjPrivilege table into the in-process cache.
    Called once at application startup from the lifespan handler.
    """
    global _privilege_matrix
    result = await db.execute(
        text("SELECT roleUserGroup, objectName, privilege FROM secObjPrivilege")
    )
    rows = result.fetchall()

    matrix: dict[str, dict[str, str]] = {}
    for role, obj, priv in rows:
        if role not in matrix:
            matrix[role] = {}
        # Keep the highest privilege if a role has multiple entries for the same object
        existing = matrix[role].get(obj)
        if existing is None or _privilege_gte(priv, existing):
            matrix[role][obj] = priv

    _privilege_matrix = matrix
    logger.info(
        "RBAC privilege matrix loaded — %d roles, %d total privilege entries",
        len(matrix),
        sum(len(v) for v in matrix.values()),
    )


# ── FastAPI dependency for route-level enforcement ────────────────────────────

def require_permission(oscar_object: str, privilege: str = "r"):
    """
    FastAPI dependency. Raises 403 if the authenticated user's roles
    do not have the required privilege on the given Oscar object.

    Usage:
        @router.get("/fhir/R4/Patient/{id}",
                    dependencies=[Depends(require_permission("_demographic", "r"))])
    """
    async def _check(request: Request):
        roles: list[str] = getattr(request.state, "roles", [])
        if not roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No roles assigned — contact your administrator",
            )
        if not _roles_have_privilege(roles, oscar_object, privilege):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient privileges on {oscar_object}",
            )

    return Depends(_check)
