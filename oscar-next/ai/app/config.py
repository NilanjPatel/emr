from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    # Anthropic — async, de-identified tasks only
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Ollama — on-premise, real-time PHI tasks
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.3"          # or mistral-medical when available

    # Redis — AI event queue (db=1, separate from backend's db=0)
    redis_url: str = "redis://localhost:6379/1"

    # Allowed CORS origins (comma-separated) — set to real domain in production
    cors_origins: str = "http://localhost:3000"

    # Safety gates
    max_tokens_per_request: int = 2000
    suggestion_only: bool = True            # must stay True — AI never auto-saves

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def anthropic_available(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def ollama_available(self) -> bool:
        return bool(self.ollama_host)


@lru_cache
def get_settings() -> Settings:
    return Settings()
