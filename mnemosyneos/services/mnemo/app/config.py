"""
Configuration settings for MnemosyneOS.
Loads from environment variables with reasonable defaults.
"""
import os
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    # LLM Provider settings
    LVC_PROVIDER: str = Field(
        default="openai",
        env="LVC_PROVIDER",
        description="LLM provider for Lucian Voss (openai, anthropic, deepseek)"
    )
    
    # API Keys (loaded from environment variables)
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    DEEPSEEK_API_KEY: Optional[str] = Field(default=None, env="DEEPSEEK_API_KEY")
    
    # Directory paths with defaults
    CHROMA_DIR: str = Field(
        default="/var/lib/jb-vps/mnemo/chroma",
        env="CHROMA_DIR",
        description="Directory for ChromaDB storage"
    )
    LOG_DIR: str = Field(
        default="/var/log/jb-vps",
        env="LOG_DIR",
        description="Directory for log files"
    )
    STATE_DIR: str = Field(
        default="/var/lib/jb-vps/mnemo",
        env="STATE_DIR", 
        description="Directory for state files"
    )
    CONFIG_DIR: str = Field(
        default="/etc/jb-vps",
        env="CONFIG_DIR",
        description="Directory for configuration files"
    )
    
    # Service settings
    HOST: str = Field(
        default="127.0.0.1",
        env="MNEMO_HOST",
        description="Host to bind the API server to"
    )
    PORT: int = Field(
        default=8077,
        env="MNEMO_PORT",
        description="Port to bind the API server to"
    )
    
    # LLM settings
    DEFAULT_MODEL: str = Field(
        default="gpt-4o",  # OpenAI default model
        env="LVC_DEFAULT_MODEL",
        description="Default model to use for LLM operations"
    )
    
    # Memory settings
    MEMORY_TTL: int = Field(
        default=365,  # days
        env="MEMORY_TTL", 
        description="Default time-to-live for memories in days"
    )
    REFLECTION_INTERVAL: int = Field(
        default=24,  # hours
        env="REFLECTION_INTERVAL",
        description="Interval for automatic reflections in hours"
    )
    
    # RSS settings
    RSS_CHECK_INTERVAL: int = Field(
        default=3600,  # seconds (1 hour)
        env="RSS_CHECK_INTERVAL",
        description="Default interval to check RSS feeds in seconds"
    )
    
    class Config:
        env_file = "/etc/jb-vps/ai.env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Ensure directories exist
def ensure_dirs_exist():
    """Ensure all required directories exist"""
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    os.makedirs(settings.STATE_DIR, exist_ok=True)
    os.makedirs(settings.CONFIG_DIR, exist_ok=True)
    
    # Create subdirectories for different memory types
    os.makedirs(os.path.join(settings.STATE_DIR, "episodic"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "semantic"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "procedural"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "reflective"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "affective"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "identity"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "meta"), exist_ok=True)
    os.makedirs(os.path.join(settings.STATE_DIR, "rss"), exist_ok=True)

# Validate LLM provider
def validate_provider():
    """Validate the configured LLM provider has API key set"""
    if settings.LVC_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        raise ValueError("OpenAI provider selected but OPENAI_API_KEY not set")
    elif settings.LVC_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise ValueError("Anthropic provider selected but ANTHROPIC_API_KEY not set")
    elif settings.LVC_PROVIDER == "deepseek" and not settings.DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek provider selected but DEEPSEEK_API_KEY not set")
    return True
