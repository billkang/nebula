import pytest
from app.services.coder_backend import CoderBackend, CodingResult, BuildResult


def test_coder_backend_is_abstract():
    with pytest.raises(TypeError):
        CoderBackend()


def test_coding_result_defaults():
    r = CodingResult(status="success", source_dir="/tmp/src", message="done")
    assert r.status == "success"
    assert r.source_dir == "/tmp/src"
    assert r.message == "done"
    assert r.error is None


def test_build_result_defaults():
    r = BuildResult(status="failed", message="tests failed", error="AssertionError: x != y")
    assert r.status == "failed"
    assert r.artifact_path is None
    assert r.error == "AssertionError: x != y"


def test_build_result_success():
    r = BuildResult(status="success", artifact_path="/tmp/artifacts/v1/artifact.tar.gz",
                    version="v1", test_output="3 passed", message="build ok")
    assert r.artifact_path == "/tmp/artifacts/v1/artifact.tar.gz"
    assert r.version == "v1"
    assert r.test_output == "3 passed"
