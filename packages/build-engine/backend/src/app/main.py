from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import engine, Base
from app.api.router import api_router
from app.services.event_bus import init_event_bus
from app.core.logging import setup_logging
from app.middleware.logging import RequestLogMiddleware
import os
import logging

logger = logging.getLogger("nebula")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging before everything else
    setup_logging(log_level=settings.log_level, log_dir=settings.log_dir)
    logger.info("Logging initialized (level=%s, dir=%s)", settings.log_level, settings.log_dir)

    Base.metadata.create_all(bind=engine)
    # 确保 projects/ 目录存在
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "..", "projects"), exist_ok=True)
    # 初始化 EventBus 单例（需在事件循环已运行后）
    init_event_bus()
    logger.info("Nebula API started")
    yield
    logger.info("Nebula API shutting down")


app = FastAPI(title="Nebula API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLogMiddleware)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content={"data": None, "error": str(exc.errors())},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": "Internal server error"},
    )


app.include_router(api_router, prefix="/api/v1")
