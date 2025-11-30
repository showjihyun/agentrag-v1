"""
API Version 2

This module contains the v2 API endpoints with improved:
- Standardized response format
- Better error handling
- Enhanced rate limiting
- Audit logging
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v2", tags=["v2"])
