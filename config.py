from pydantic import BaseSettings

class Settings(BaseSettings):
    DEBUG: bool = False
    DATA_DIR: str = "/var/lib/mnemosyneos/data"
    VECTOR_DIR: str = "/var/lib/mnemosyneos/vectors"
    # Add other config variables as needed

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()