"""
AI Agent Olympics API
AI 에이전트 올림픽 API - 2025 Future Roadmap 구현
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from backend.services.olympics.agent_olympics_manager import (
    get_olympics_manager,
    AgentOlympicsManager,
    CompetitionType,
    AgentStatus,
    CompetitionStatus
)
from backend.core.structured_logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/agent-olympics",
    tags=["agent-olympics"]
)

# Request/Response Models
class CompetitionCreateRequest(BaseModel):
    """경쟁 대회 생성 요청"""
    name: str = Field(description="경쟁 대회 이름")
    type: str = Field(description="경쟁 유형 (speed, accuracy, collaboration, creativity, endurance, efficiency)")
    participant_ids: List[str] = Field(description="참가자 ID 목록")
    duration: Optional[int] = Field(default=300, description="경쟁 시간 (초)")
    prize: Optional[int] = Field(default=500, description="상금")
    description: Optional[str] = Field(default="", description="경쟁 설명")

class AgentResponse(BaseModel):
    """에이전트 응답"""
    agents: List[Dict[str, Any]]
    total_count: int
    active_count: int
    top_performer: Optional[Dict[str, Any]]

class CompetitionResponse(BaseModel):
    """경쟁 대회 응답"""
    competitions: List[Dict[str, Any]]
    active_competitions: List[Dict[str, Any]]
    total_count: int
    upcoming_count: int

class LeaderboardResponse(BaseModel):
    """리더보드 응답"""
    leaderboard: List[Dict[str, Any]]
    total_agents: int
    ranking_updated_at: datetime

class LiveProgressResponse(BaseModel):
    """실시간 진행률 응답"""
    competition_id: str
    progress: Dict[str, float]
    rankings: List[Dict[str, Any]]
    spectators: int
    is_completed: bool

class AnalyticsResponse(BaseModel):
    """분석 데이터 응답"""
    total_competitions: int
    active_agents: int
    total_spectators: int
    total_prize_pool: int
    performance_trends: Dict[str, List[float]]
    competition_distribution: Dict[str, int]
    agent_status_distribution: Dict[str, int]

@router.get("/agents", response_model=AgentResponse)
async def get_agents(
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    모든 에이전트 조회
    
    AI 에이전트 올림픽에 참가하는 모든 에이전트의 정보를 반환합니다.
    """
    try:
        logger.info("Getting all agents")
        
        agents = await olympics_manager.get_agents()
        active_agents = [agent for agent in agents if agent["status"] != AgentStatus.OFFLINE.value]
        
        # 최고 성과자 찾기
        top_performer = None
        if agents:
            top_performer = max(agents, key=lambda x: x["stats"]["points"])
        
        response = AgentResponse(
            agents=agents,
            total_count=len(agents),
            active_count=len(active_agents),
            top_performer=top_performer
        )
        
        logger.info(f"Retrieved {len(agents)} agents")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get agents: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agents: {str(e)}")

@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    특정 에이전트 조회
    
    지정된 ID의 에이전트 상세 정보를 반환합니다.
    """
    try:
        logger.info(f"Getting agent: {agent_id}")
        
        agent = await olympics_manager.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent {agent_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get agent: {str(e)}")

@router.get("/competitions", response_model=CompetitionResponse)
async def get_competitions(
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    모든 경쟁 대회 조회
    
    진행 중, 예정된, 완료된 모든 경쟁 대회 정보를 반환합니다.
    """
    try:
        logger.info("Getting all competitions")
        
        competitions = await olympics_manager.get_competitions()
        active_competitions = await olympics_manager.get_active_competitions()
        
        upcoming_competitions = [
            comp for comp in competitions 
            if comp["status"] == CompetitionStatus.UPCOMING.value
        ]
        
        response = CompetitionResponse(
            competitions=competitions,
            active_competitions=active_competitions,
            total_count=len(competitions),
            upcoming_count=len(upcoming_competitions)
        )
        
        logger.info(f"Retrieved {len(competitions)} competitions")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get competitions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get competitions: {str(e)}")

@router.get("/competitions/{competition_id}")
async def get_competition(
    competition_id: str,
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    특정 경쟁 대회 조회
    
    지정된 ID의 경쟁 대회 상세 정보를 반환합니다.
    """
    try:
        logger.info(f"Getting competition: {competition_id}")
        
        competition = await olympics_manager.get_competition(competition_id)
        if not competition:
            raise HTTPException(status_code=404, detail=f"Competition not found: {competition_id}")
        
        return competition
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get competition {competition_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get competition: {str(e)}")

@router.get("/competitions/{competition_id}/progress", response_model=LiveProgressResponse)
async def get_live_progress(
    competition_id: str,
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    실시간 경쟁 진행률 조회
    
    진행 중인 경쟁의 실시간 진행률과 순위를 반환합니다.
    """
    try:
        logger.info(f"Getting live progress for competition: {competition_id}")
        
        progress = await olympics_manager.get_live_progress(competition_id)
        if progress is None:
            raise HTTPException(status_code=404, detail=f"Live progress not found for competition: {competition_id}")
        
        competition = await olympics_manager.get_competition(competition_id)
        if not competition:
            raise HTTPException(status_code=404, detail=f"Competition not found: {competition_id}")
        
        # 순위 계산
        rankings = []
        for agent in competition["participants"]:
            agent_progress = progress.get(agent["id"], 0.0)
            rankings.append({
                "agent_id": agent["id"],
                "name": agent["name"],
                "avatar": agent["avatar"],
                "progress": agent_progress,
                "position": 0  # 나중에 계산
            })
        
        # 진행률 기준으로 순위 정렬
        rankings.sort(key=lambda x: x["progress"], reverse=True)
        for i, ranking in enumerate(rankings):
            ranking["position"] = i + 1
        
        # 완료 여부 확인
        is_completed = max(progress.values()) >= 100.0 if progress else False
        
        response = LiveProgressResponse(
            competition_id=competition_id,
            progress=progress,
            rankings=rankings,
            spectators=competition.get("spectators", 0),
            is_completed=is_completed
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get live progress: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get live progress: {str(e)}")

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    리더보드 조회
    
    포인트 기준으로 정렬된 에이전트 리더보드를 반환합니다.
    """
    try:
        logger.info("Getting leaderboard")
        
        leaderboard = await olympics_manager.get_leaderboard()
        
        response = LeaderboardResponse(
            leaderboard=leaderboard,
            total_agents=len(leaderboard),
            ranking_updated_at=datetime.now()
        )
        
        logger.info(f"Retrieved leaderboard with {len(leaderboard)} agents")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get leaderboard: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get leaderboard: {str(e)}")

@router.post("/competitions")
async def create_competition(
    request: CompetitionCreateRequest,
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    새 경쟁 대회 생성
    
    새로운 AI 에이전트 경쟁 대회를 생성합니다.
    """
    try:
        logger.info(f"Creating competition: {request.name}")
        
        # 경쟁 유형 검증
        try:
            CompetitionType(request.type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid competition type: {request.type}")
        
        competition_data = {
            "name": request.name,
            "type": request.type,
            "participant_ids": request.participant_ids,
            "duration": request.duration,
            "prize": request.prize,
            "description": request.description
        }
        
        competition_id = await olympics_manager.create_competition(competition_data)
        
        return {
            "success": True,
            "competition_id": competition_id,
            "message": f"Competition '{request.name}' created successfully",
            "created_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create competition: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create competition: {str(e)}")

@router.post("/competitions/{competition_id}/start")
async def start_competition(
    competition_id: str,
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    경쟁 시작
    
    지정된 경쟁 대회를 시작합니다.
    """
    try:
        logger.info(f"Starting competition: {competition_id}")
        
        success = await olympics_manager.start_competition(competition_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to start competition: {competition_id}")
        
        return {
            "success": True,
            "competition_id": competition_id,
            "message": "Competition started successfully",
            "started_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start competition: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start competition: {str(e)}")

@router.post("/competitions/{competition_id}/stop")
async def stop_competition(
    competition_id: str,
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    경쟁 중단
    
    진행 중인 경쟁 대회를 중단합니다.
    """
    try:
        logger.info(f"Stopping competition: {competition_id}")
        
        success = await olympics_manager.stop_competition(competition_id)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to stop competition: {competition_id}")
        
        return {
            "success": True,
            "competition_id": competition_id,
            "message": "Competition stopped successfully",
            "stopped_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop competition: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop competition: {str(e)}")

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    분석 데이터 조회
    
    AI 에이전트 올림픽의 전체 통계 및 분석 데이터를 반환합니다.
    """
    try:
        logger.info("Getting analytics data")
        
        analytics = await olympics_manager.get_analytics()
        
        response = AnalyticsResponse(
            total_competitions=analytics.get("total_competitions", 0),
            active_agents=analytics.get("active_agents", 0),
            total_spectators=analytics.get("total_spectators", 0),
            total_prize_pool=analytics.get("total_prize_pool", 0),
            performance_trends=analytics.get("performance_trends", {}),
            competition_distribution=analytics.get("competition_types", {}),
            agent_status_distribution=analytics.get("agent_status_distribution", {})
        )
        
        logger.info("Analytics data retrieved successfully")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get analytics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/status")
async def get_olympics_status(
    olympics_manager: AgentOlympicsManager = Depends(get_olympics_manager)
):
    """
    올림픽 상태 요약 조회
    
    AI 에이전트 올림픽의 전반적인 상태를 간단히 요약하여 반환합니다.
    """
    try:
        competitions = await olympics_manager.get_competitions()
        active_competitions = await olympics_manager.get_active_competitions()
        agents = await olympics_manager.get_agents()
        
        active_agents = [agent for agent in agents if agent["status"] != AgentStatus.OFFLINE.value]
        
        return {
            "total_agents": len(agents),
            "active_agents": len(active_agents),
            "total_competitions": len(competitions),
            "active_competitions": len(active_competitions),
            "upcoming_competitions": len([c for c in competitions if c["status"] == CompetitionStatus.UPCOMING.value]),
            "completed_competitions": len([c for c in competitions if c["status"] == CompetitionStatus.COMPLETED.value]),
            "total_spectators": sum(comp.get("spectators", 0) for comp in active_competitions),
            "system_status": "active" if active_competitions else "idle",
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get olympics status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get olympics status: {str(e)}")

@router.get("/competition-types")
async def get_competition_types():
    """
    경쟁 유형 목록 조회
    
    사용 가능한 모든 경쟁 유형을 반환합니다.
    """
    try:
        competition_types = [
            {
                "type": comp_type.value,
                "name": comp_type.value.replace("_", " ").title(),
                "description": {
                    "speed": "Ultimate speed test for AI agents",
                    "accuracy": "Precision and correctness competition",
                    "collaboration": "Teamwork and coordination test",
                    "creativity": "Innovation and creative problem-solving",
                    "endurance": "Long-duration performance test",
                    "efficiency": "Resource optimization challenge"
                }.get(comp_type.value, "AI agent competition")
            }
            for comp_type in CompetitionType
        ]
        
        return {
            "competition_types": competition_types,
            "total_types": len(competition_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to get competition types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get competition types: {str(e)}")