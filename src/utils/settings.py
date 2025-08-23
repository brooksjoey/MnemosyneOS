src/utils/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_keys: List[str] = Field(default=["dev-key-123"], alias="API_KEYS")
    max_request_bytes: int = Field(default=1_048_576, alias="MAX_REQUEST_BYTES")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    embed_model: str = Field(default="text-embedding-3-small", alias="EMBED_MODEL")

    backup_backend: str = Field(default="local", alias="BACKUP_BACKEND")
    backup_dir: str = Field(default="/var/lib/mnemo/snapshots", alias="BACKUP_DIR")
    s3_bucket: Optional[str] = Field(default=None, alias="S3_BUCKET")
    s3_prefix: Optional[str] = Field(default=None, alias="S3_PREFIX")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = Field(default=None, alias="AWS_REGION")
    backup_key_file: str = Field(default="/etc/mnemo/backup.key", alias="BACKUP_KEY_FILE")

    auto_migrate: int = Field(default=1, alias="AUTO_MIGRATE")

    # Observability
    otel_exporter_otlp_endpoint: Optional[str] = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

settings = Settings()