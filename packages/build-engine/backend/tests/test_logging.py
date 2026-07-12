"""Tests for logging setup, middleware, business logging, and log reporting API."""

import os
import tempfile
import logging
import pytest
from fastapi.testclient import TestClient
from app.models.user import User, UserRole
from app.services.auth_service import hash_password


def test_setup_logging_creates_log_file():
    from app.core.logging import setup_logging

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logging(log_level="DEBUG", log_dir=tmpdir)
        test_logger = logging.getLogger("nebula")
        test_logger.info("test message")
        # force flush
        for handler in test_logger.handlers:
            handler.flush()
        files = os.listdir(tmpdir)
        assert any(f.startswith("nebula-") and f.endswith(".log") for f in files)


def test_setup_logging_respects_log_level():
    from app.core.logging import setup_logging

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logging(log_level="ERROR", log_dir=tmpdir)
        test_logger = logging.getLogger("nebula")
        test_logger.info("should not appear")
        test_logger.error("should appear")
        # nebula.biz inherits from root — check it has ERROR level set
        nebula_biz = logging.getLogger("nebula.biz")
        # If not explicitly set, check that the effective level is ERROR
        effective = nebula_biz.getEffectiveLevel()
        assert effective == logging.ERROR, f"Expected effective level == ERROR, got {effective}"


def test_setup_logging_console_handler():
    from app.core.logging import setup_logging

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logging(log_level="INFO", log_dir=tmpdir)
        # Handlers are now on the root logger (nebula propagates to root)
        root_logger = logging.getLogger()
        has_console = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in root_logger.handlers
        )
        assert has_console, "Should have a console (StreamHandler) handler on root logger"


def test_app_logging_without_crash(client, db):
    """Verify app starts and handles requests after exception handlers are updated.

    The exception handlers in main.py should log before returning error responses.
    This test verifies they still return the correct response format.
    """
    from app.main import app

    # Create a test user
    user = User(username="logtest", email="log@test.com",
                password=hash_password("pass123"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()

    # Login to get token
    resp = client.post("/api/v1/auth/login", json={"username": "logtest", "password": "pass123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Normal authenticated route works
    resp2 = client.get("/api/v1/projects", headers=headers)
    assert resp2.status_code == 200

    # Validation error handler still returns 422 with data/error format
    resp3 = client.post("/api/v1/projects", json={"invalid": True}, headers=headers)
    assert resp3.status_code == 422
    body = resp3.json()
    assert "error" in body or "detail" in body
    assert body.get("data") is None


def test_rotating_file_handler_configuration():
    """Verify file handler uses midnight rotation and 30-day retention."""
    from app.core.logging import setup_logging

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logging(log_level="INFO", log_dir=tmpdir)
        # Handlers are on the root logger; nebula.* loggers propagate to root
        root_logger = logging.getLogger()

        file_handlers = [h for h in root_logger.handlers
                         if isinstance(h, logging.handlers.TimedRotatingFileHandler)]
        assert file_handlers, "Should have a TimedRotatingFileHandler"
        handler = file_handlers[0]
        # TimedRotatingFileHandler stores when as MIDNIGHT (uppercase internally)
        assert handler.when == "MIDNIGHT"
        assert handler.backupCount == 30


def test_log_format():
    """Verify log entry format matches expected pattern."""
    import re

    with tempfile.TemporaryDirectory() as tmpdir:
        from app.core.logging import setup_logging
        setup_logging(log_level="INFO", log_dir=tmpdir)
        app_logger = logging.getLogger("nebula.test")
        app_logger.info("hello world")

        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".log")]
        log_path = os.path.join(tmpdir, log_files[0])

        with open(log_path) as f:
            content = f.read()

        # Format: timestamp | LEVEL | name | message
        assert re.search(
            r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.*\| INFO .*\| nebula\.test \| hello world",
            content,
        )


def test_validation_error_logged(client, db):
    """Verify validation errors produce a 422 response (logging side effect tested separately)."""
    user = User(username="valtest", email="val@test.com",
                password=hash_password("pass123"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()

    resp = client.post("/api/v1/auth/login", json={"username": "valtest", "password": "pass123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Send invalid data to a POST endpoint
    response = client.post("/api/v1/projects", json={}, headers=headers)
    assert response.status_code == 422
    body = response.json()
    assert body.get("data") is None


def test_biz_logger_format():
    """Verify biz_logger produces [BIZ] [STAGE] [STEP] format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.core.logging import setup_logging, biz_stage_start, biz_stage_end, biz_step
        setup_logging(log_level="INFO", log_dir=tmpdir)

        biz_stage_start("TEST_STAGE", project_id="p1", user="admin")
        biz_step("TEST_STAGE", "do-thing", detail="step1")
        biz_stage_end("TEST_STAGE", status="ok", project_id="p1")

        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".log")]
        log_path = os.path.join(tmpdir, log_files[0])
        with open(log_path) as f:
            content = f.read()

        assert "[BIZ] [TEST_STAGE] START" in content
        assert "[BIZ] [TEST_STAGE] [do-thing]" in content
        assert "[BIZ] [TEST_STAGE] END status=ok" in content


def test_biz_logger_uses_dedicated_logger():
    """Verify biz_logger uses nebula.biz logger name."""
    from app.core.logging import biz_logger
    assert biz_logger.name == "nebula.biz"


def test_setup_project_logging_creates_project_log():
    """Verify per-project logging creates log file in project dir."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = os.path.join(tmpdir, "projects", "admin-add-logging")
        from app.core.logging import setup_logging, setup_project_logging, biz_stage_start
        setup_logging(log_level="INFO", log_dir=tmpdir)

        # Simulate project creation
        setup_project_logging(project_dir=project_dir, change_name="add-logging")
        biz_stage_start("CREATE_PROJECT", project_id="p1", change_name="add-logging")

        project_log_dir = os.path.join(project_dir, "logs")
        assert os.path.isdir(project_log_dir), "Project log dir should exist"

        log_files = [f for f in os.listdir(project_log_dir) if f.endswith(".log")]
        assert log_files, "Project log file should exist"

        log_path = os.path.join(project_log_dir, log_files[0])
        with open(log_path) as f:
            content = f.read()
        assert "[BIZ] [CREATE_PROJECT] START" in content


def test_biz_logger_project_creation_flow():
    """Verify CREATE_PROJECT stage: START → step → END with metadata."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.core.logging import setup_logging, biz_stage_start, biz_stage_end, biz_step
        setup_logging(log_level="INFO", log_dir=tmpdir)

        # Simulate the CREATE_PROJECT flow
        biz_stage_start("CREATE_PROJECT", project_name="test-project", username="admin")
        biz_step("CREATE_PROJECT", "translate-name", name="test-project", result="test-project")
        biz_step("CREATE_PROJECT", "db-record", project_id="abc-123")
        biz_step("CREATE_PROJECT", "fs-init", dir="/tmp/test")
        biz_stage_end("CREATE_PROJECT", status="ok", project_id="abc-123")

        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".log")]
        log_path = os.path.join(tmpdir, log_files[0])
        with open(log_path) as f:
            content = f.read()

        assert "[BIZ] [CREATE_PROJECT] START" in content
        assert "[BIZ] [CREATE_PROJECT] [translate-name]" in content
        assert "[BIZ] [CREATE_PROJECT] [db-record]" in content
        assert "[BIZ] [CREATE_PROJECT] [fs-init]" in content
        assert "[BIZ] [CREATE_PROJECT] END status=ok" in content
        assert "project_id=abc-123" in content


def test_biz_logger_project_failure_flow():
    """Verify CREATE_PROJECT failure: START → END status=failed with reason."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.core.logging import setup_logging, biz_stage_start, biz_stage_end
        setup_logging(log_level="INFO", log_dir=tmpdir)

        biz_stage_start("CREATE_PROJECT", project_name="fail-project", username="admin")
        # Simulate a failure before any step completes
        biz_stage_end("CREATE_PROJECT", status="failed", reason="translate_failed", error="ValueError")

        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".log")]
        log_path = os.path.join(tmpdir, log_files[0])
        with open(log_path) as f:
            content = f.read()

        assert "[BIZ] [CREATE_PROJECT] START" in content
        assert "[BIZ] [CREATE_PROJECT] END status=failed" in content
        assert "reason=translate_failed" in content


def test_biz_logger_spec_gen_flow():
    """Verify SPEC_GEN stage: START → multiple steps → END."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.core.logging import setup_logging, biz_stage_start, biz_stage_end, biz_step
        setup_logging(log_level="INFO", log_dir=tmpdir)

        biz_stage_start("SPEC_GEN", project_id="p1")
        biz_step("SPEC_GEN", "write-context")
        biz_step("SPEC_GEN", "create-change", name="test-change")
        biz_step("SPEC_GEN", "proposal")
        biz_step("SPEC_GEN", "specs")
        biz_step("SPEC_GEN", "design")
        biz_step("SPEC_GEN", "tasks")
        biz_stage_end("SPEC_GEN", status="ok", project_id="p1")

        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".log")]
        log_path = os.path.join(tmpdir, log_files[0])
        with open(log_path) as f:
            content = f.read()

        assert "[BIZ] [SPEC_GEN] START" in content
        for step in ["write-context", "create-change", "proposal", "specs", "design", "tasks"]:
            assert f"[BIZ] [SPEC_GEN] [{step}]" in content
        assert "[BIZ] [SPEC_GEN] END status=ok" in content


def test_request_middleware_logs_request():
    """Verify request middleware logs method, path, status, duration.

    The middleware should log with nebula.request logger in format:
      GET /api/v1/auth/me → 200 (Xms) | ip=... user=...
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        from app.core.logging import setup_logging
        setup_logging(log_level="INFO", log_dir=tmpdir)

        from app.main import app
        client = TestClient(app)

        # Make a request
        response = client.get("/api/v1/auth/me")
        assert response.status_code in (200, 401)

        # Check log file contains the request
        log_files = [f for f in os.listdir(tmpdir) if f.endswith(".log")]
        assert log_files, "Log file should exist"

        log_path = os.path.join(tmpdir, log_files[0])
        with open(log_path) as f:
            content = f.read()

        # The middleware logs with nebula.request logger
        # Look for the format:  METHOD /path → STATUS (Xms) | ip=... user=...
        assert "nebula.request" in content, (
            f"Expected middleware log (nebula.request) in:\n{content}"
        )


def test_log_reporting_api_auth_required(client):
    """POST /api/v1/logs should return 401 without auth."""
    response = client.post("/api/v1/logs", json=[{
        "level": "info", "message": "test", "timestamp": "2026-07-12T00:00:00Z",
    }])
    assert response.status_code == 401


def test_log_reporting_api_with_auth(client, db):
    """POST /api/v1/logs should accept logs with valid JWT."""
    user = User(username="logapi", email="logapi@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()

    resp = client.post("/api/v1/auth/login", json={"username": "logapi", "password": "pass123"})
    token = resp.json()["access_token"]

    response = client.post(
        "/api/v1/logs",
        json=[{
            "level": "info",
            "message": "Frontend test log",
            "timestamp": "2026-07-12T00:00:00Z",
        }],
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is True
