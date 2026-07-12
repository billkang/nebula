from fastapi import APIRouter
from app.api.auth import auth_router
from app.api.projects import projects_router
from app.api.chat import chat_router
from app.api.documents import doc_router
from app.api.executor import executor_router
from app.api.build import build_router
from app.api.sandbox import sandbox_router
from app.api.logs import logs_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(doc_router)
api_router.include_router(chat_router)
api_router.include_router(executor_router)
api_router.include_router(build_router)
api_router.include_router(sandbox_router)
api_router.include_router(logs_router)
