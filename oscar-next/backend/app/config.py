from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "oscar"
    db_user: str = "oscar"
    db_password: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )

    # Auth — Keycloak
    keycloak_url: str = "http://keycloak:8080"          # internal Docker URL for JWKS fetch
    keycloak_public_url: str = ""                        # public URL — used for issuer validation
    keycloak_realm: str = "oscar"
    keycloak_client_id: str = "oscar-api"
    keycloak_client_secret: str = ""

    @property
    def jwks_url(self) -> str:
        return f"{self.keycloak_url}/realms/{self.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def keycloak_issuer(self) -> str:
        # Token issuer claim uses the public URL; fall back to internal if not set.
        # Keycloak appends :443 to HTTPS URLs — normalise by removing it so the
        # string comparison in auth middleware matches both forms.
        base = self.keycloak_public_url or self.keycloak_url
        base = base.rstrip("/").replace(":443", "").replace(":80", "")
        return f"{base}/realms/{self.keycloak_realm}"

    # Application
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "changeme"
    log_level: str = "INFO"

    # FHIR
    fhir_base_url: str = "http://localhost:8000/fhir/R4"

    # External services
    drugref2_url: str = "http://drugref2-api:8080"
    ai_sidecar_url: str = "http://oscar-ai:8001"

    # CORS — comma-separated list of allowed origins; empty = block all cross-origin
    cors_origins: str = ""

    @property
    def allowed_origins(self) -> list[str]:
        # Always include any explicitly configured origins
        raw = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.is_development:
            dev = ["http://localhost:3000", "http://localhost:3001"]
            return list(dict.fromkeys(dev + raw))  # dev first, deduplicated
        return raw

    # Admin config UI
    admin_config_enabled: bool = True

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
