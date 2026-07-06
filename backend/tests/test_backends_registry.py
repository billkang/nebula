import pytest
from app.services.backends import register_backend, get_backend, create_backend
from app.services.coder_backend import CoderBackend, CodingResult, BuildResult


class FakeBackend(CoderBackend):
    def execute_coding(self, spec, skill, project_dir, *, timeout=3600):
        return CodingResult(status="success", source_dir="", message="fake")

    def execute_build(self, project_dir, version=None, *, timeout=600):
        return BuildResult(status="success", message="fake")


def _clean_registry():
    """Helper to clean the global registry for test isolation."""
    from app.services.backends import _registry
    _registry.clear()


def test_register_and_get():
    _clean_registry()
    register_backend("fake", FakeBackend)
    cls = get_backend("fake")
    assert cls is FakeBackend


def test_unknown_backend_raises():
    _clean_registry()
    with pytest.raises(ValueError, match="unknown-backend"):
        get_backend("unknown-backend")


def test_create_backend_instance():
    _clean_registry()
    register_backend("fake2", FakeBackend)
    backend = create_backend("fake2")
    assert isinstance(backend, FakeBackend)
