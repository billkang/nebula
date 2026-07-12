import logging
from typing import List, Union
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.log import LogEntry, LogResponse

logger = logging.getLogger("nebula.logs")

logs_router = APIRouter(prefix="/logs", tags=["logs"])

LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


@logs_router.post("", response_model=dict)
async def report_logs(
    entries: Union[LogEntry, List[LogEntry]],
    current_user: User = Depends(get_current_user),
):
    """Accept frontend log entries and write them to the backend log file.

    Accepts a single LogEntry or a list of LogEntry. Invalid entries are
    logged as server-side warnings but don't cause the whole batch to fail.
    """
    if not isinstance(entries, list):
        entries = [entries]

    accepted = 0
    for entry in entries:
        try:
            entry_level = LEVEL_MAP.get(entry.level, logging.INFO)
            log_message = f"[Frontend] {entry.message}"
            if entry.stack:
                log_message += f"\n{entry.stack}"
            logger.log(entry_level, log_message)
            accepted += 1
        except Exception as e:
            logger.warning("Invalid log entry skipped: %s", e)

    logger.info("Accepted %d/%d frontend log entries", accepted, len(entries))
    return {"data": {"accepted": True}}
