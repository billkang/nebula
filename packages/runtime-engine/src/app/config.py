from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    runtime_port: int = 8001
    artifacts_dir: str = str(Path(__file__).resolve().parent.parent / "artifacts")
    platform_url: str = ""
    cors_origins: str = "*"

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
