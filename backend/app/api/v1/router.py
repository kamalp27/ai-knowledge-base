from fastapi import APIRouter
from backend.app.api.v1.endpoints import documents, health, query

api_router = APIRouter()

# Register endpoint routers
api_router.include_router(health.router, tags=["Health & Readiness"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(query.router, prefix="/query", tags=["Question Answering"])
