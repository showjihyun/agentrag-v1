"""Admin API endpoints."""

from fastapi import APIRouter
from .rate_limit_management import router as rate_limit_router

# Create main admin router
router = APIRouter(prefix="/admin", tags=["admin"])

# Include sub-routers
router.include_router(rate_limit_router)
