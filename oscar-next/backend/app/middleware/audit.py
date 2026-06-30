"""
Audit middleware — writes to oscar_log table on every request that touches patient data.

PHIPA requirement: every access to personal health information must be logged with:
user, timestamp, action, resource type, resource ID, patient ID.

This middleware is a GATE — no patient data endpoint ships without this wired.
"""
from datetime import datetime
from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

# Paths that contain patient data and must be audited
AUDITED_PATH_PREFIXES = (
    "/fhir/R4/Patient",
    "/fhir/R4/Appointment",
    "/fhir/R4/Encounter",
    "/fhir/R4/MedicationRequest",
    "/fhir/R4/DiagnosticReport",
    "/fhir/R4/Observation",
    "/fhir/R4/AllergyIntolerance",
    "/fhir/R4/Condition",
    "/fhir/R4/Immunization",
    "/fhir/R4/Claim",
    "/fhir/R4/DocumentReference",
    "/fhir/R4/Composition",
)

# Paths that are never audited (health checks, static assets)
SKIP_AUDIT_PREFIXES = (
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if self._should_audit(path) and response.status_code < 400:
            await self._write_audit_log(request, response.status_code)

        return response

    def _should_audit(self, path: str) -> bool:
        if any(path.startswith(skip) for skip in SKIP_AUDIT_PREFIXES):
            return False
        return any(path.startswith(audited) for audited in AUDITED_PATH_PREFIXES)

    async def _write_audit_log(self, request: Request, status_code: int):
        try:
            db = getattr(request.state, "db", None)
            user = self._extract_user(request)
            action = self._map_method_to_action(request.method)
            data = f"{request.method} {request.url.path}"

            if db is None:
                # Should never happen after Phase 0.3 — DBSessionMiddleware guarantees this
                logger.error("AUDIT FAILURE: no db session on request — path=%s", request.url.path)
                return

            await db.execute(
                text("""
                    INSERT INTO log
                        (dateTime, provider_no, action, content, contentId, ip, data)
                    VALUES
                        (:datetime, :provider_no, :action, :content, :content_id, :ip, :data)
                """),
                {
                    "datetime": datetime.now(),
                    "provider_no": user,
                    "action": action,
                    "content": self._path_to_table(request.url.path),
                    "content_id": self._extract_resource_id(request.url.path),
                    "ip": self._get_client_ip(request),
                    "data": data,
                }
            )
            await db.commit()
        except Exception as e:
            # Audit failures must never crash the request — but must be visible
            logger.error("AUDIT FAILURE: %s — path=%s", e, request.url.path)

    def _extract_user(self, request: Request) -> str:
        # Will be populated from JWT claims once auth middleware is wired (Phase 0.5)
        token_data = getattr(request.state, "token_data", None)
        if token_data:
            return token_data.get("preferred_username", "unknown")
        return "unauthenticated"

    def _extract_resource_id(self, path: str) -> Optional[str]:
        parts = [p for p in path.split("/") if p]
        # Pattern: /fhir/R4/ResourceType/id
        if len(parts) >= 4:
            return parts[3]
        return None

    def _path_to_table(self, path: str) -> str:
        parts = [p for p in path.split("/") if p]
        resource_to_table = {
            "Patient": "demographic",
            "Appointment": "appointment",
            "Encounter": "casemgmt_note",
            "MedicationRequest": "prescription",
            "DiagnosticReport": "labTestResults",
            "Observation": "measurements",
            "AllergyIntolerance": "allergies",
            "Condition": "casemgmt_issue",
            "Immunization": "preventions",
            "Claim": "billing",
            "DocumentReference": "document",
            "Composition": "casemgmt_note",
        }
        if len(parts) >= 3:
            return resource_to_table.get(parts[2], parts[2])
        return "unknown"

    def _map_method_to_action(self, method: str) -> str:
        return {
            "GET": "read",
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete",
        }.get(method, method.lower())

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
