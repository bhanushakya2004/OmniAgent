"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for OmniMission AI service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+psycopg://omni:omni@localhost:5432/omnimission"

    # Security & JWT
    jwt_secret: str = "default-insecure-jwt-secret-key-32-chars-minimum"
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 15
    jwt_refresh_ttl_days: int = 14

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Storage Port
    storage_backend: Literal["local", "gcs"] = "local"
    local_storage_path: str = "./.data/uploads"

    # Google Gemini Models & Vertex Access
    gemini_backend: Literal["api_key", "vertex"] = "api_key"
    google_api_key: str | None = None
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    gemini_model_reasoning: str = "gemini-2.5-flash"
    gemini_model_fast: str = "gemini-2.5-flash"
    gemini_model_vision: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"

    # Tooling
    agno_mcp_token: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
