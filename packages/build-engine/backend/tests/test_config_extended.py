from app.config import settings


def test_coder_backend_default():
    assert hasattr(settings, "coder_backend")
    assert settings.coder_backend == "docker"


def test_docker_image_defaults():
    assert settings.coder_image == "nebula-coder:latest"
    assert settings.builder_image == "nebula-builder:latest"


def test_resource_config_defaults():
    assert settings.coder_cpu_limit == 2
    assert settings.coder_memory_limit == "2g"
    assert settings.builder_cpu_limit == 1
    assert settings.builder_memory_limit == "512m"
