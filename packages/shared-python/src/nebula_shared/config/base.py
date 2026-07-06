from pydantic_settings import BaseSettings


class BaseConfig(BaseSettings):
    """Base configuration class for all Nebula services.

    Extend this class in each service's config.py for service-specific fields.
    """

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
