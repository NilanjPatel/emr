"""
Admin config endpoint — allows editing .env values through the web UI.

Protected: requires 'admin' role in Keycloak token.
Secrets are masked on read — never returned in plaintext.
A restart is required after changes for new values to take effect.
"""
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from pathlib import Path
import re

router = APIRouter(prefix="/admin/config", tags=["admin"])

ENV_FILE = Path(".env")

# Fields that are masked on read (shown as ***** in UI)
SENSITIVE_FIELDS = {
    "db_password", "keycloak_client_secret", "secret_key",
}

# Fields that are never writable through the UI (structural settings)
READONLY_FIELDS = {
    "app_env",
}


class ConfigUpdate(BaseModel):
    key: str
    value: str


def _require_admin(request: Request):
    token_data = getattr(request.state, "token_data", {})
    roles = token_data.get("realm_access", {}).get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )


def _read_env_file() -> dict[str, str]:
    if not ENV_FILE.exists():
        return {}
    config = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            config[key.strip().lower()] = value.strip()
    return config


def _write_env_value(key: str, value: str):
    content = ENV_FILE.read_text() if ENV_FILE.exists() else ""
    pattern = re.compile(rf"^({re.escape(key.upper())})\s*=.*$", re.MULTILINE | re.IGNORECASE)
    new_line = f"{key.upper()}={value}"
    if pattern.search(content):
        content = pattern.sub(new_line, content)
    else:
        content = content.rstrip("\n") + f"\n{new_line}\n"
    ENV_FILE.write_text(content)


@router.get("")
async def get_config(request: Request):
    _require_admin(request)
    config = _read_env_file()
    masked = {}
    for key, value in config.items():
        masked[key] = "*****" if key in SENSITIVE_FIELDS else value
    return {
        "config": masked,
        "note": "Sensitive fields are masked. Changes require a backend restart to take effect.",
        "restart_required_after_change": True,
    }


@router.patch("")
async def update_config(update: ConfigUpdate, request: Request):
    _require_admin(request)
    key = update.key.lower().strip()

    if key in READONLY_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{key}' cannot be changed through the UI",
        )

    _write_env_value(key, update.value)
    return {
        "updated": key,
        "value": "*****" if key in SENSITIVE_FIELDS else update.value,
        "message": "Restart the backend container to apply this change.",
    }
