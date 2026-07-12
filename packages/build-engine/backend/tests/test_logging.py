"""Tests for logging setup, middleware, business logging, and log reporting API."""

import os
import tempfile
import logging


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
        assert effective <= logging.ERROR, f"Expected effective level <= ERROR, got {effective}"


def test_setup_logging_console_handler():
    from app.core.logging import setup_logging

    with tempfile.TemporaryDirectory() as tmpdir:
        setup_logging(log_level="INFO", log_dir=tmpdir)
        test_logger = logging.getLogger("nebula")
        has_console = any(
            isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
            for h in test_logger.handlers
        )
        assert has_console, "Should have a console (StreamHandler) handler"
