from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.upload import router as upload_router
from app.api.documents import router as documents_router
from app.api.auth import router as auth_router, admin_router
from app.api.comparison import router as comparison_router
from app.api.reports import router as reports_router
from app.api.cases import router as cases_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(upload_router)
api_router.include_router(documents_router)
api_router.include_router(auth_router)
api_router.include_router(admin_router)
api_router.include_router(comparison_router)
api_router.include_router(reports_router)
api_router.include_router(cases_router)

__all__ = ["api_router"]
