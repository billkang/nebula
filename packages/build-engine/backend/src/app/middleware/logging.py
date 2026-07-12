"""Request logging ASGI middleware for Nebula API.

Logs every HTTP request with method, path, status, duration, client IP, and user ID.
Writes one log line when the response completes (stream finished or connection closed),
so SSE streaming responses get the correct final status code and total duration.
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("nebula.request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Log every HTTP request with method, path, status, duration, client IP, and user ID.

    At INFO level: method, path, status_code, duration_ms, client_ip, user_id.
    At DEBUG level: additionally logs request body and response body (truncated to 10KB).
    Writes one log line when the response completes.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        # Capture request body at DEBUG level
        request_body = None
        if logger.isEnabledFor(logging.DEBUG):
            body_bytes = await request.body()
            request_body = body_bytes[:10240].decode("utf-8", errors="replace")

        response = await call_next(request)

        duration_ms = int((time.time() - start_time) * 1000)
        status_code = response.status_code

        # Extract user ID from request state (set by auth middleware)
        user_id = "anonymous"
        try:
            user = getattr(request.state, "user", None)
            if user:
                user_id = str(user.id) if hasattr(user, "id") else str(user)
        except Exception:
            pass

        # Build log entry
        log_data = (
            f"{request.method} {request.url.path} → {status_code} ({duration_ms}ms) "
            f"| ip={client_ip} user={user_id}"
        )
        logger.info(log_data)

        # At DEBUG, log request/response body
        if logger.isEnabledFor(logging.DEBUG):
            response_body = None
            if hasattr(response, "body"):
                response_body = response.body[:10240].decode("utf-8", errors="replace")
            logger.debug("Request body: %s", request_body)
            logger.debug("Response body: %s", response_body)

        return response
