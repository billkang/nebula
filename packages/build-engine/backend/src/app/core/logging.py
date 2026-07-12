"""Application logging configuration and business stage logging utilities.

Provides:
- setup_logging(): Initialize system-wide logging with file + console handlers
- biz_logger / biz_stage_start/step/end: Business stage logging with [BIZ] markers
- setup_project_logging(): Per-project independent log file
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

# Track per-project log handlers to avoid duplicate attachments
_project_log_handlers: set[str] = set()


def setup_logging(log_level: str = "INFO", log_dir: str = "./logs") -> None:
    """Initialize the application-wide logging configuration.

    Configures a TimedRotatingFileHandler (daily rotation, 30-day retention)
    and a StreamHandler (console output). Must be called once at app startup.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Log file name: nebula-{YYYY-MM-DD}.log
    log_file = os.path.join(log_dir, f"nebula-{datetime.now().strftime('%Y-%m-%d')}.log")

    # Formatter: 2026-07-12 14:30:00,123 | INFO  | module_name | message
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler — daily rotation, 30-day retention
    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", backupCount=30, encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger — all nebula.* loggers propagate to root by default
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Prevent nebula namespace from double-logging through both its own handlers
    # and root's handlers. Setting propagate=False means nebula.* messages only
    # go to root's handlers (where they were already registered above).
    app_logger = logging.getLogger("nebula")
    app_logger.setLevel(level)
    app_logger.propagate = True


# Business stage logger
biz_logger = logging.getLogger("nebula.biz")


def biz_stage_start(stage: str, **metadata) -> None:
    """Mark the start of a business stage. Logs [BIZ] [STAGE] START with metadata."""
    meta_str = _fmt_meta(metadata)
    biz_logger.info("[BIZ] [%s] START | %s", stage, meta_str)


def biz_stage_end(stage: str, status: str = "ok", **metadata) -> None:
    """Mark the end of a business stage. Logs [BIZ] [STAGE] END status= with metadata."""
    meta_str = _fmt_meta(metadata)
    biz_logger.info("[BIZ] [%s] END status=%s | %s", stage, status, meta_str)


def biz_step(stage: str, step: str, **metadata) -> None:
    """Log a step within a business stage. Logs [BIZ] [STAGE] [STEP] with metadata."""
    meta_str = _fmt_meta(metadata)
    biz_logger.info("[BIZ] [%s] [%s] | %s", stage, step, meta_str)


def _fmt_meta(metadata: dict) -> str:
    """Format metadata dict as 'key=val key=val' string.

    Values containing spaces are quoted so the output remains parseable:
    ``key="hello world" plain=ok``
    """
    return " ".join(
        f'{k}="{v}"' if " " in str(v) else f"{k}={v}"
        for k, v in metadata.items()
    )


def setup_project_logging(project_dir: str, change_name: str) -> None:
    """Configure a per-project log file for business stage logs.

    Creates a TimedRotatingFileHandler at {project_dir}/logs/{change_name}.log
    that captures all [BIZ] entries for this project.

    Idempotent — repeated calls with the same (project_dir, change_name)
    do not add duplicate handlers.
    """
    log_dir = os.path.join(project_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"{change_name}.log")
    handler_key = f"{log_file}"

    # Skip if this project log handler already exists
    if handler_key in _project_log_handlers:
        return
    _project_log_handlers.add(handler_key)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = TimedRotatingFileHandler(
        log_file, when="midnight", backupCount=30, encoding="utf-8",
    )
    handler.setLevel(logging.INFO)
    handler.setFormatter(formatter)

    # Attach to the nebula.biz logger so all business logs go to this file
    biz_logger.addHandler(handler)
