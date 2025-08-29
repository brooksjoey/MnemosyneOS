<<<<<<< HEAD
from pydantic import Field, validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
=======
src/utils/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List, Optional
>>>>>>> bbeef0f (Initial commit with all project files)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

<<<<<<< HEAD
    # --- API Security ---
    api_keys: List[str] = Field(default=[], alias="API_KEYS") # CHANGE: Default to empty list!
    
    @field_validator('api_keys', mode='before')
    @classmethod
    def validate_api_keys(cls, v):
        """Ensure API keys are provided and not the default."""
        if isinstance(v, str):
            v = [key.strip() for key in v.split(",") if key.strip()]
        if not v:
            # You could allow this only in a dev mode, but it's safer to require keys.
            # Let's make it a hard requirement.
            raise ValueError("API_KEYS environment variable must be set with at least one key.")
        if "dev-key-123" in v:
            raise ValueError("The default key 'dev-key-123' is not allowed for security reasons.")
        return v

    max_request_bytes: int = Field(default=1_048_576, alias="MAX_REQUEST_BYTES")

    # --- Database ---
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    # --- LLM --- 
=======
    api_keys: List[str] = Field(default=["dev-key-123"], alias="API_KEYS")
    max_request_bytes: int = Field(default=1_048_576, alias="MAX_REQUEST_BYTES")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

>>>>>>> bbeef0f (Initial commit with all project files)
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    embed_model: str = Field(default="text-embedding-3-small", alias="EMBED_MODEL")
<<<<<<< HEAD
    # NEW: Add a setting for embedding dimensions
    embed_dim: int = Field(default=1536, alias="EMBED_DIM") 

    @field_validator('openai_api_key', 'anthropic_api_key')
    @classmethod
    def validate_llm_keys(cls, v, info):
        """Validate that the necessary API key is provided for the chosen provider."""
        provider = info.data.get('llm_provider')
        key_name = info.field_name
        
        # If this key field matches the chosen provider, it must be set.
        if provider == 'openai' and key_name == 'openai_api_key':
            if not v:
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        if provider == 'anthropic' and key_name == 'anthropic_api_key':
            if not v:
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'")
        return v

    # --- Backup ---
    backup_backend: str = Field(default="local", alias="BACKUP_BACKEND")
    backup_dir: str = Field(default="/var/lib/mnemo/snapshots", alias="BACKUP_DIR")
    backup_key_file: str = Field(default="/etc/mnemo/backup.key", alias="BACKUP_KEY_FILE")
    
=======

    backup_backend: str = Field(default="local", alias="BACKUP_BACKEND")
    backup_dir: str = Field(default="/var/lib/mnemo/snapshots", alias="BACKUP_DIR")
>>>>>>> bbeef0f (Initial commit with all project files)
    s3_bucket: Optional[str] = Field(default=None, alias="S3_BUCKET")
    s3_prefix: Optional[str] = Field(default=None, alias="S3_PREFIX")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region: Optional[str] = Field(default=None, alias="AWS_REGION")
<<<<<<< HEAD

    @field_validator('backup_backend')
    @classmethod
    def validate_backend(cls, v, values):
        """Validate S3 configuration if the backend is set to 's3'."""
        if v == "s3":
            if not values.data.get('s3_bucket'):
                raise ValueError("S3_BUCKET is required when BACKUP_BACKEND is 's3'")
            # Check for AWS credentials or if we should rely on IAM roles
            if not (values.data.get('aws_access_key_id') and values.data.get('aws_secret_access_key')):
                # If not explicitly set, check if we're on EC2/IAM
                if not os.environ.get('AWS_ACCESS_KEY_ID') and not os.environ.get('AWS_SECRET_ACCESS_KEY'):
                    # Check for IAM role (simple check for EC2)
                    # This is just a warning; boto3 will handle auth failure at runtime.
                    print("Warning: No explicit AWS credentials found. Relying on IAM roles or environment.")
        return v
=======
    backup_key_file: str = Field(default="/etc/mnemo/backup.key", alias="BACKUP_KEY_FILE")
>>>>>>> bbeef0f (Initial commit with all project files)

    auto_migrate: int = Field(default=1, alias="AUTO_MIGRATE")

    # Observability
    otel_exporter_otlp_endpoint: Optional[str] = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

<<<<<<< HEAD
settings = Settings()
=======
settings = Settings()
>>>>>>> bbeef0f (Initial commit with all project files)
