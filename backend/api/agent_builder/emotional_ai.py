"""
Emotional AI API
감정 AI API - 2025 Future Roadmap 구현
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from backend.services.emotional.emotional_ai_service import (
    get_emotional_ai_service,
    EmotionalAIService,
    EmotionType,
    CommunicationStyle,
    WorkPace,
    FeedbackType
)
from backend.core.structured_logging import get_logger
from pydantic import BaseModel, Field

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/emotional-ai",
    tags=["emotional-ai"]
)

# Request/Response Models
class EmotionAnalysisRequest(BaseModel):
    """감정 분석 요청"""
    user_id: str = Field(description="사용자 ID")
    input_data: Dict[str, Any] = Field(description="분석할 입력 데이터")
    context: Optional[str] = Field(default="", description="상황 컨텍스트")

class UserPreferencesUpdateRequest(BaseModel):
    """사용자 선호도 업데이트 요청"""
    communication_style: Optional[str] = Field(default=None, description="의사소통 스타일")
    work_pace: Optional[str] = Field(default=None, description="작업 속도")
    feedback_type: Optional[str] = Field(default=None, description="피드백 유형")
    stress_threshold: Optional[float] = Field(default=None, description="스트레스 임계값")

class EmotionHistoryRequest(BaseModel):
    """감정 히스토리 요청"""
    hours: int = Field(default=24, description="조회할 시간 범위 (시간)")

class UserEmotionResponse(BaseModel):
    """사용자 감정 응답"""
    user_emotion: Dict[str, Any]
    adaptive_recommendations: List[str]
    wellness_alerts: List[str]
    ui_theme: str

class EmotionHistoryResponse(BaseModel):
    """감정 히스토리 응답"""
    emotion_history: List[Dict[str, Any]]
    total_entries: int
    time_range: Dict[str, datetime]
    emotion_summary: Dict[str, Any]

class TeamDynamicsResponse(BaseModel):
    """팀 역학 응답"""
    team_dynamics: Dict[str, Any]
    risk_indicators: List[str]
    improvement_suggestions: List[str]
    team_health_score: float

class InsightsResponse(BaseModel):
    """인사이트 응답"""
    insights: List[Dict[str, Any]]
    total_insights: int
    priority_insights: List[Dict[str, Any]]
    actionable_count: int

class EmotionAnalysisResponse(BaseModel):
    """감정 분석 응답"""
    detected_emotion: str
    intensity: float
    confidence: float
    recommended_theme: str
    wellness_impact: Dict[str, float]
    adaptive_suggestions: List[str]

@router.get("/users/{user_id}/emotion", response_model=UserEmotionResponse)
async def get_user_emotion(
    user_id: str,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    사용자 감정 상태 조회
    
    지정된 사용자의 현재 감정 상태와 웰니스 메트릭을 반환합니다.
    """
    try:
        logger.info(f"Getting emotion for user: {user_id}")
        
        user_emotion = await emotional_ai.get_user_emotion(user_id)
        if not user_emotion:
            raise HTTPException(status_code=404, detail=f"User emotion data not found: {user_id}")
        
        # 적응형 추천사항 생성
        adaptive_recommendations = []
        wellness_metrics = user_emotion["wellness_metrics"]
        
        if wellness_metrics["stress_level"] > 70:
            adaptive_recommendations.append("Consider taking a break to reduce stress")
        if wellness_metrics["energy_level"] > 80:
            adaptive_recommendations.append("Great energy levels! Perfect time for challenging tasks")
        if wellness_metrics["focus_level"] > 85:
            adaptive_recommendations.append("Excellent focus - tackle your most important work now")
        
        # 웰니스 알림
        wellness_alerts = []
        if wellness_metrics["wellness_score"] < 50:
            wellness_alerts.append("Wellness score is below optimal - consider wellness activities")
        if wellness_metrics["stress_level"] > 80:
            wellness_alerts.append("High stress detected - immediate stress management recommended")
        
        # 적응형 테마
        ui_theme = await emotional_ai.get_adaptive_theme(user_id)
        
        response = UserEmotionResponse(
            user_emotion=user_emotion,
            adaptive_recommendations=adaptive_recommendations,
            wellness_alerts=wellness_alerts,
            ui_theme=ui_theme
        )
        
        logger.info(f"Retrieved emotion data for user {user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user emotion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user emotion: {str(e)}")

@router.get("/users/{user_id}/emotion/history", response_model=EmotionHistoryResponse)
async def get_emotion_history(
    user_id: str,
    hours: int = 24,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    감정 히스토리 조회
    
    지정된 시간 범위 내의 사용자 감정 변화 히스토리를 반환합니다.
    """
    try:
        logger.info(f"Getting emotion history for user {user_id}, hours: {hours}")
        
        emotion_history = await emotional_ai.get_emotion_history(user_id, hours)
        
        if not emotion_history:
            raise HTTPException(status_code=404, detail=f"No emotion history found for user: {user_id}")
        
        # 감정 요약 계산
        emotion_counts = {}
        total_intensity = 0
        
        for entry in emotion_history:
            emotion = entry["primary"]
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_intensity += entry["intensity"]
        
        most_common_emotion = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "unknown"
        avg_intensity = total_intensity / len(emotion_history) if emotion_history else 0
        
        emotion_summary = {
            "most_common_emotion": most_common_emotion,
            "emotion_distribution": emotion_counts,
            "average_intensity": avg_intensity,
            "total_entries": len(emotion_history),
            "emotional_stability": 1.0 - (len(set(entry["primary"] for entry in emotion_history)) / len(emotion_history)) if emotion_history else 0
        }
        
        response = EmotionHistoryResponse(
            emotion_history=emotion_history,
            total_entries=len(emotion_history),
            time_range={
                "start": datetime.now().replace(hour=datetime.now().hour - hours),
                "end": datetime.now()
            },
            emotion_summary=emotion_summary
        )
        
        logger.info(f"Retrieved {len(emotion_history)} emotion history entries")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get emotion history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get emotion history: {str(e)}")

@router.get("/teams/{team_id}/dynamics", response_model=TeamDynamicsResponse)
async def get_team_dynamics(
    team_id: str,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    팀 감정 역학 조회
    
    팀의 전반적인 감정 상태, 응집력, 위험 요소 등을 분석하여 반환합니다.
    """
    try:
        logger.info(f"Getting team dynamics for team: {team_id}")
        
        team_dynamics = await emotional_ai.get_team_dynamics(team_id)
        if not team_dynamics:
            raise HTTPException(status_code=404, detail=f"Team dynamics not found: {team_id}")
        
        # 위험 지표 생성
        risk_indicators = []
        if team_dynamics["conflict_risk"] > 50:
            risk_indicators.append(f"High conflict risk: {team_dynamics['conflict_risk']:.1f}%")
        if team_dynamics["burnout_risk"] > 60:
            risk_indicators.append(f"Burnout risk detected: {team_dynamics['burnout_risk']:.1f}%")
        if team_dynamics["cohesion_score"] < 60:
            risk_indicators.append(f"Low team cohesion: {team_dynamics['cohesion_score']:.1f}%")
        
        # 개선 제안
        improvement_suggestions = team_dynamics.get("recommendations", [])
        
        # 팀 건강 점수 계산
        team_health_score = (
            team_dynamics["cohesion_score"] * 0.4 +
            (100 - team_dynamics["conflict_risk"]) * 0.3 +
            (100 - team_dynamics["burnout_risk"]) * 0.3
        )
        
        response = TeamDynamicsResponse(
            team_dynamics=team_dynamics,
            risk_indicators=risk_indicators,
            improvement_suggestions=improvement_suggestions,
            team_health_score=team_health_score
        )
        
        logger.info(f"Retrieved team dynamics for team {team_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get team dynamics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get team dynamics: {str(e)}")

@router.get("/users/{user_id}/insights", response_model=InsightsResponse)
async def get_user_insights(
    user_id: str,
    limit: int = 10,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    사용자 감정 인사이트 조회
    
    사용자의 감정 패턴 분석 결과와 개인화된 추천사항을 반환합니다.
    """
    try:
        logger.info(f"Getting insights for user {user_id}, limit: {limit}")
        
        insights = await emotional_ai.get_insights(user_id, limit)
        
        # 우선순위 인사이트 필터링
        priority_insights = [insight for insight in insights if insight["priority"] in ["high", "urgent"]]
        
        # 실행 가능한 인사이트 수 계산
        actionable_count = len([insight for insight in insights if insight["actionable_items"]])
        
        response = InsightsResponse(
            insights=insights,
            total_insights=len(insights),
            priority_insights=priority_insights,
            actionable_count=actionable_count
        )
        
        logger.info(f"Retrieved {len(insights)} insights for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to get user insights: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get user insights: {str(e)}")

@router.post("/users/{user_id}/analyze", response_model=EmotionAnalysisResponse)
async def analyze_emotion(
    user_id: str,
    request: EmotionAnalysisRequest,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    감정 분석 수행
    
    사용자의 입력 데이터를 분석하여 감정 상태를 탐지하고 적응형 추천사항을 제공합니다.
    """
    try:
        logger.info(f"Analyzing emotion for user: {user_id}")
        
        analysis_result = await emotional_ai.analyze_emotion(user_id, request.input_data)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=400, detail=analysis_result["error"])
        
        # 적응형 제안 생성
        adaptive_suggestions = []
        emotion = analysis_result["emotion"]
        intensity = analysis_result["intensity"]
        
        if emotion == "stressed" and intensity > 0.7:
            adaptive_suggestions.extend([
                "Switch to calming UI theme",
                "Reduce notification frequency",
                "Suggest break reminders",
                "Enable focus mode"
            ])
        elif emotion == "happy" and intensity > 0.8:
            adaptive_suggestions.extend([
                "Use vibrant UI theme",
                "Increase interaction opportunities",
                "Suggest collaborative tasks",
                "Enable celebration animations"
            ])
        elif emotion == "focused" and intensity > 0.7:
            adaptive_suggestions.extend([
                "Use minimal UI theme",
                "Reduce distractions",
                "Optimize for productivity",
                "Enable deep work mode"
            ])
        
        response = EmotionAnalysisResponse(
            detected_emotion=analysis_result["emotion"],
            intensity=analysis_result["intensity"],
            confidence=analysis_result["confidence"],
            recommended_theme=analysis_result["recommended_theme"],
            wellness_impact=analysis_result["wellness_impact"],
            adaptive_suggestions=adaptive_suggestions
        )
        
        logger.info(f"Emotion analysis completed for user {user_id}: {analysis_result['emotion']}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze emotion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze emotion: {str(e)}")

@router.put("/users/{user_id}/preferences")
async def update_user_preferences(
    user_id: str,
    request: UserPreferencesUpdateRequest,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    사용자 선호도 업데이트
    
    사용자의 감정 AI 관련 선호도 설정을 업데이트합니다.
    """
    try:
        logger.info(f"Updating preferences for user: {user_id}")
        
        # 요청 데이터를 딕셔너리로 변환 (None 값 제외)
        preferences_data = {}
        if request.communication_style is not None:
            preferences_data["communication_style"] = request.communication_style
        if request.work_pace is not None:
            preferences_data["work_pace"] = request.work_pace
        if request.feedback_type is not None:
            preferences_data["feedback_type"] = request.feedback_type
        if request.stress_threshold is not None:
            preferences_data["stress_threshold"] = request.stress_threshold
        
        success = await emotional_ai.update_user_preferences(user_id, preferences_data)
        
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to update preferences for user: {user_id}")
        
        return {
            "success": True,
            "user_id": user_id,
            "updated_preferences": preferences_data,
            "message": "User preferences updated successfully",
            "updated_at": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {str(e)}")

@router.get("/users/{user_id}/adaptive-theme")
async def get_adaptive_theme(
    user_id: str,
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    적응형 테마 조회
    
    사용자의 현재 감정 상태에 기반한 적응형 UI 테마를 반환합니다.
    """
    try:
        logger.info(f"Getting adaptive theme for user: {user_id}")
        
        theme = await emotional_ai.get_adaptive_theme(user_id)
        
        # 테마별 설정
        theme_configs = {
            "warm": {
                "primary_color": "#f59e0b",
                "background": "gradient-to-br from-orange-50 to-yellow-50",
                "mood": "energetic and positive"
            },
            "cool": {
                "primary_color": "#06b6d4",
                "background": "gradient-to-br from-blue-50 to-green-50",
                "mood": "calm and focused"
            },
            "minimal": {
                "primary_color": "#6b7280",
                "background": "white",
                "mood": "focused and productive"
            },
            "soothing": {
                "primary_color": "#8b5cf6",
                "background": "gradient-to-br from-purple-50 to-pink-50",
                "mood": "relaxed and stress-free"
            },
            "vibrant": {
                "primary_color": "#ef4444",
                "background": "gradient-to-br from-red-50 to-orange-50",
                "mood": "excited and dynamic"
            },
            "default": {
                "primary_color": "#3b82f6",
                "background": "white",
                "mood": "neutral and balanced"
            }
        }
        
        theme_config = theme_configs.get(theme, theme_configs["default"])
        
        return {
            "theme": theme,
            "config": theme_config,
            "user_id": user_id,
            "generated_at": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get adaptive theme: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get adaptive theme: {str(e)}")

@router.get("/emotion-types")
async def get_emotion_types():
    """
    감정 유형 목록 조회
    
    시스템에서 지원하는 모든 감정 유형을 반환합니다.
    """
    try:
        emotion_types = [
            {
                "type": emotion.value,
                "name": emotion.value.replace("_", " ").title(),
                "icon": {
                    "happy": "😊",
                    "sad": "😢",
                    "angry": "😠",
                    "excited": "🤩",
                    "calm": "😌",
                    "stressed": "😰",
                    "focused": "🧐",
                    "frustrated": "😤",
                    "confident": "😎",
                    "anxious": "😟"
                }.get(emotion.value, "😐"),
                "theme": {
                    "happy": "warm",
                    "calm": "cool",
                    "focused": "minimal",
                    "stressed": "soothing",
                    "excited": "vibrant"
                }.get(emotion.value, "default")
            }
            for emotion in EmotionType
        ]
        
        return {
            "emotion_types": emotion_types,
            "total_types": len(emotion_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to get emotion types: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get emotion types: {str(e)}")

@router.get("/status")
async def get_emotional_ai_status(
    emotional_ai: EmotionalAIService = Depends(get_emotional_ai_service)
):
    """
    감정 AI 시스템 상태 조회
    
    감정 AI 시스템의 전반적인 상태와 통계를 반환합니다.
    """
    try:
        return {
            "total_users": len(emotional_ai.users),
            "total_teams": len(emotional_ai.teams),
            "total_insights": len(emotional_ai.insights),
            "active_patterns": len(emotional_ai.emotion_patterns),
            "adaptive_ui_enabled": emotional_ai.config["adaptive_ui_enabled"],
            "emotion_update_interval": emotional_ai.config["emotion_update_interval"],
            "supported_emotions": len(EmotionType),
            "system_status": "active",
            "last_updated": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get emotional AI status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get emotional AI status: {str(e)}")