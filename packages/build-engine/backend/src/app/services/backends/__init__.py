from app.services.coder_backend import CoderBackend

_registry: dict[str, type[CoderBackend]] = {}


def register_backend(name: str, backend_cls: type[CoderBackend]) -> None:
    _registry[name] = backend_cls


# Import backends so their register_backend() calls execute at import time
import app.services.backends.docker_backend  # noqa: F401


def get_backend(name: str) -> type[CoderBackend]:
    if name not in _registry:
        raise ValueError(f"Unknown backend: {name}")
    return _registry[name]


def create_backend(name: str = "") -> CoderBackend:
    from app.config import settings
    name = name or settings.coder_backend
    cls = get_backend(name)
    return cls()
