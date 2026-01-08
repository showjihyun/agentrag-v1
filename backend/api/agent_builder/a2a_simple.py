"""
Simple A2A Protocol API Endpoints.

간단한 A2A API 엔드포인트 (테스트용)
"""

from fastapi import APIRouter

router = APIRouter(prefix="/a2a", tags=["A2A Protocol"])


@router.get("/health")
async def health_check():
    """A2A 서비스 상태 확인."""
    return {"status": "ok", "service": "A2A Protocol"}


@router.get("/agents")
async def list_agents():
    """외부 A2A 에이전트 목록 조회."""
    return {"agents": [], "total": 0}


@router.get("/servers")
async def list_servers():
    """A2A 서버 설정 목록 조회."""
    return {"servers": [], "total": 0}


@router.post("/agents")
async def create_agent():
    """외부 A2A 에이전트 추가."""
    return {"message": "Not implemented yet"}


@router.post("/servers")
async def create_server():
    """A2A 서버 설정 추가."""
    return {"message": "Not implemented yet"}