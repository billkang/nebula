from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nebula.db"
    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_expiry_hours: int = 24
    cors_origins: str = "http://localhost:5173"
    admin_username: str = "admin"
    admin_password: str = "123456"
    pm_username: str = "pm"
    pm_password: str = "123456"
    runtime_url: str = "http://localhost:8001"

    # Docker executor config
    coder_backend: str = "docker"
    coder_image: str = "nebula-coder:latest"
    builder_image: str = "nebula-builder:latest"
    coder_cpu_limit: int = 2
    coder_memory_limit: str = "2g"
    builder_cpu_limit: int = 1
    builder_memory_limit: str = "512m"

    # LLM Provider config
    llm_provider: str = "deepseek"          # deepseek | openai | custom
    llm_model: str = "deepseek-chat"        # model name
    llm_api_key: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    llm_base_url: str = "https://api.deepseek.com"  # API base URL

    # Logging config
    log_level: str = "INFO"
    log_dir: str = "./logs"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "populate_by_name": True}


settings = Settings()
