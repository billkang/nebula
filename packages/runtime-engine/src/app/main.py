from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.runtime import runtime_router
from app.api.registry import registry_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    artifacts_path = Path(settings.artifacts_dir)
    artifacts_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title="Nebula Runtime", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"data": None, "error": "Internal server error"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


app.include_router(runtime_router, prefix="/api/v1/runtime")
app.include_router(registry_router, prefix="/api/v1/registry")
