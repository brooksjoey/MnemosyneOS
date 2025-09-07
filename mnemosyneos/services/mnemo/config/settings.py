from __future__ import annotations

import os
from pathlib import Path
from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for MnemosyneOS. Values can be set via environment
    variables or a local .env file at the repo root. Pydantic v2 is required.
    """

    # App
    APP_NAME: str = Field(default="MnemosyneOS", description="Human-friendly app name.")
    ENV: str = Field(default="development", description='"development" or "production".')
    HOST: str = Field(default="0.0.0.0", description="Bind host for uvicorn.")
    PORT: int = Field(default=8208, description="Bind port for uvicorn.")

    # Providers / backends
    OPENAI_API_KEY: str | None = Field(default=None, description="OpenAI API key.")
    EMBEDDINGS_PROVIDER: str = Field(default="openai", description='e.g., "openai"')
    VECTOR_BACKEND: str = Field(default="chroma", description='e.g., "chroma"')

    # Paths
    DATA_DIR: str = Field(default="./data", description="Root data directory.")
    LOG_DIR: str = Field(default="./logs", description="Root log directory.")
    CHROMA_DIR: str = Field(default="", description="Directory for Chroma persistence.")

    # Security / limits
    API_KEY: str | None = Field(default=None, description="API key for incoming requests.")
    RATE_LIMIT: str = Field(default="100/minute", description='SlowAPI style, e.g. "100/minute".')

    # Timeouts
    REQUEST_TIMEOUT_SECONDS: int = Field(default=30, description="Client timeout for outbound calls.")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("ENV")
    @classmethod
    def _validate_env(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in {"development", "production"}:
            raise ValueError('ENV must be "development" or "production"')
        return v

    @field_validator("CHROMA_DIR")
    @classmethod
    def _default_chroma_dir(cls, v: str, info: ValidationInfo) -> str:
        if v:
            return v
        data_dir = info.data.get("DATA_DIR") or "./data"
        return str(Path(data_dir) / "chroma")

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def _require_openai_in_prod(cls, v: str | None, info: ValidationInfo) -> str | None:
        env = (info.data.get("ENV") or "development").lower()
        if env == "production" and not v:
            raise ValueError("OPENAI_API_KEY must be set in production.")
        return v

    @field_validator("API_KEY")
    @classmethod
    def _require_api_key_in_prod(cls, v: str | None, info: ValidationInfo) -> str | None:
        env = (info.data.get("ENV") or "development").lower()
        if env == "production" and not v:
            raise ValueError("API_KEY must be set in production.")
        return v


settings = Settings()

# Ensure directories exist on import (safe for multi-import)
Path(settings.DATA_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.CHROMA_DIR).mkdir(parents=True, exist_ok=True)