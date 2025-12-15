"""
Emotional AI Service
감정 AI 서비스 - 2025 Future Roadmap 구현
"""

import asyncio
import json
import uuid
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import logging
from collections import defaultdict, deque
import random

from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

class EmotionType(Enum):
    """감정 유형"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    STRESSED = "stressed"
    FOCUSED = "focused"
    FRUSTRATED = "frustrated"
    CONFIDENT = "confident"
    ANXIOUS = "anxious"

class CommunicationStyle(Enum):
    """의사소통 스타일"""
    DIRECT = "direct"
    CASUAL = "casual"
    FORMAL = "formal"
    EMPATHETIC = "empathetic"
    ENCOURAGING = "encouraging"

class WorkPace(Enum):
    """작업 속도"""
    SLOW = "slow"
    STEADY = "steady"
    FAST = "fast"
    ADAPTIVE = "adaptive"

class FeedbackType(Enum):
    """피드백 유형"""
    CONSTRUCTIVE = "constructive"
    POSITIVE = "positive"
    DETAILED = "detailed"
    BRIEF = "brief"

@dataclass
class EmotionState:
    """감정 상태"""
    primary: EmotionType
    intensity: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    timestamp: datetime
    triggers: List[str]
    context: str

@dataclass
class UserPreferences:
    """사용자 선호도"""
    communication_style: CommunicationStyle
    work_pace: WorkPace
    feedback_type: FeedbackType
    preferred_interaction_time: List[int]  # 선호 시간대 (시간)
    stress_threshold: float  # 스트레스 임계값
    energy_pattern: Dict[int, float]  # 시간별 에너지 패턴

@dataclass
class UserMood:
    """사용자 기분"""
    user_id: str
    name: str
    current_emotion: EmotionState
    emotion_history: List[EmotionState]
    stress_level: float  # 0-100
    energy_level: float  # 0-100
    focus_level: float  # 0-100
    wellness_score: float  # 0-100
    preferences: UserPreferences
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class TeamEmotionalDynamics:
    """팀 감정 역학"""
    team_id: str
    team_name: str
    overall_mood: EmotionType
    cohesion_score: float  # 0-100
    stress_indicators: List[str]
    productivity_correlation: float  # -1.0 to 1.0
    conflict_risk: float  # 0-100
    burnout_risk: float  # 0-100
    recommendations: List[str]
    last_analyzed: datetime = field(default_factory=datetime.now)

@dataclass
class EmotionalInsight:
    """감정 인사이트"""
    insight_id: str
    user_id: str
    insight_type: str  # pattern, recommendation, alert
    title: str
    description: str
    confidence: float
    actionable_items: List[str]
    priority: str  # low, medium, high
    generated_at: datetime = field(default_factory=datetime.now)

class EmotionalAIService:
    """감정 AI 서비스"""
    
    def __init__(self):
        # 데이터 저장소
        self.users: Dict[str, UserMood] = {}
        self.teams: Dict[str, TeamEmotionalDynamics] = {}
        self.emotion_patterns: Dict[str, List[EmotionState]] = {}
        self.insights: List[EmotionalInsight] = []
        
        # 감정 분석 모델 (시뮬레이션)
        self.emotion_classifier = self._initialize_emotion_model()
        
        # 설정
        self.config = {
            "emotion_update_interval": 30,  # 30초
            "pattern_analysis_interval": 300,  # 5분
            "wellness_calculation_interval": 600,  # 10분
            "team_analysis_interval": 900,  # 15분
            "emotion_history_limit": 100,
            "adaptive_ui_enabled": True,
            "stress_alert_threshold": 80.0,
            "burnout_risk_threshold": 70.0
        }
        
        # 감정-테마 매핑
        self.emotion_themes = {
            EmotionType.HAPPY: "warm",
            EmotionType.CALM: "cool",
            EmotionType.FOCUSED: "minimal",
            EmotionType.STRESSED: "soothing",
            EmotionType.EXCITED: "vibrant",
            EmotionType.SAD: "soft",
            EmotionType.ANGRY: "neutral",
            EmotionType.FRUSTRATED: "calming"
        }
        
        # 초기 데이터 생성
        self._initialize_mock_data()
        
        # 백그라운드 작업 시작
        asyncio.create_task(self._start_background_analysis())
        
        logger.info("Emotional AI Service initialized")
    
    def _initialize_emotion_model(self):
        """감정 분석 모델 초기화 (시뮬레이션)"""
        # 실제로는 ML 모델을 로드하겠지만, 여기서는 시뮬레이션
        return {
            "model_version": "1.0.0",
            "accuracy": 0.92,
            "supported_emotions": [e.value for e in EmotionType],
            "confidence_threshold": 0.7
        }
    
    def _initialize_mock_data(self):
        """초기 모의 데이터 생성"""
        # 사용자 생성
        user_data = {
            "user_id": "user_1",
            "name": "Alex Johnson",
            "current_emotion": EmotionState(
                primary=EmotionType.FOCUSED,
                intensity=0.8,
                confidence=0.92,
                timestamp=datetime.now(),
                triggers=["productive_work", "clear_goals"],
                context="Working on important project"
            ),
            "stress_level": 35.0,
            "energy_level": 75.0,
            "focus_level": 85.0,
            "wellness_score": 78.0,
            "preferences": UserPreferences(
                communication_style=CommunicationStyle.DIRECT,
                work_pace=WorkPace.STEADY,
                feedback_type=FeedbackType.CONSTRUCTIVE,
                preferred_interaction_time=[9, 10, 11, 14, 15, 16],
                stress_threshold=70.0,
                energy_pattern={i: 50 + 30 * np.sin((i - 6) * np.pi / 12) for i in range(24)}
            )
        }
        
        # 감정 히스토리 생성
        emotion_history = []
        emotions = [EmotionType.HAPPY, EmotionType.FOCUSED, EmotionType.STRESSED, EmotionType.EXCITED, EmotionType.CALM]
        
        for i in range(24):  # 24시간 데이터
            emotion_history.append(EmotionState(
                primary=random.choice(emotions),
                intensity=random.uniform(0.3, 0.9),
                confidence=random.uniform(0.7, 0.95),
                timestamp=datetime.now() - timedelta(hours=23-i),
                triggers=random.sample(["work_task", "meeting", "break", "achievement", "challenge"], 2),
                context="Daily work activity"
            ))
        
        user_mood = UserMood(
            user_id=user_data["user_id"],
            name=user_data["name"],
            current_emotion=user_data["current_emotion"],
            emotion_history=emotion_history,
            stress_level=user_data["stress_level"],
            energy_level=user_data["energy_level"],
            focus_level=user_data["focus_level"],
            wellness_score=user_data["wellness_score"],
            preferences=user_data["preferences"]
        )
        
        self.users[user_data["user_id"]] = user_mood
        
        # 팀 데이터 생성
        team_dynamics = TeamEmotionalDynamics(
            team_id="team_1",
            team_name="Product Development Team",
            overall_mood=EmotionType.FOCUSED,
            cohesion_score=82.0,
            stress_indicators=["deadline_pressure", "scope_changes"],
            productivity_correlation=0.76,
            conflict_risk=15.0,
            burnout_risk=25.0,
            recommendations=[
                "Schedule team building activity",
                "Consider workload redistribution",
                "Implement stress management techniques"
            ]
        )
        
        self.teams["team_1"] = team_dynamics
    
    async def _start_background_analysis(self):
        """백그라운드 분석 시작"""
        # 감정 상태 업데이트
        asyncio.create_task(self._update_emotion_states())
        # 패턴 분석
        asyncio.create_task(self._analyze_emotion_patterns())
        # 웰니스 점수 계산
        asyncio.create_task(self._calculate_wellness_scores())
        # 팀 분석
        asyncio.create_task(self._analyze_team_dynamics())
    
    async def _update_emotion_states(self):
        """감정 상태 업데이트"""
        while True:
            try:
                for user_id, user_mood in self.users.items():
                    # 새로운 감정 상태 생성 (시뮬레이션)
                    new_emotion = await self._detect_emotion(user_id)
                    
                    if new_emotion:
                        # 감정 히스토리 업데이트
                        user_mood.emotion_history.append(new_emotion)
                        if len(user_mood.emotion_history) > self.config["emotion_history_limit"]:
                            user_mood.emotion_history.pop(0)
                        
                        # 현재 감정 업데이트
                        user_mood.current_emotion = new_emotion
                        user_mood.last_updated = datetime.now()
                        
                        # 스트레스/에너지/집중도 업데이트
                        await self._update_wellness_metrics(user_mood)
                
                await asyncio.sleep(self.config["emotion_update_interval"])
                
            except Exception as e:
                logger.error(f"Emotion state update failed: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _detect_emotion(self, user_id: str) -> Optional[EmotionState]:
        """감정 탐지 (시뮬레이션)"""
        try:
            # 실제로는 다양한 입력(텍스트, 음성, 행동 패턴)을 분석
            # 여기서는 시뮬레이션으로 랜덤 감정 생성
            
            emotions = list(EmotionType)
            primary_emotion = random.choice(emotions)
            
            # 시간대에 따른 감정 조정
            current_hour = datetime.now().hour
            if 9 <= current_hour <= 11:  # 오전 집중 시간
                primary_emotion = random.choice([EmotionType.FOCUSED, EmotionType.CALM, EmotionType.CONFIDENT])
            elif 14 <= current_hour <= 16:  # 오후 활동 시간
                primary_emotion = random.choice([EmotionType.HAPPY, EmotionType.EXCITED, EmotionType.FOCUSED])
            elif current_hour >= 18:  # 저녁 시간
                primary_emotion = random.choice([EmotionType.CALM, EmotionType.HAPPY, EmotionType.STRESSED])
            
            return EmotionState(
                primary=primary_emotion,
                intensity=random.uniform(0.4, 0.9),
                confidence=random.uniform(0.75, 0.95),
                timestamp=datetime.now(),
                triggers=random.sample([
                    "ui_interaction", "task_completion", "meeting", "break", 
                    "achievement", "challenge", "collaboration", "feedback"
                ], random.randint(1, 3)),
                context="System interaction"
            )
            
        except Exception as e:
            logger.error(f"Emotion detection failed for user {user_id}: {str(e)}")
            return None
    
    async def _update_wellness_metrics(self, user_mood: UserMood):
        """웰니스 메트릭 업데이트"""
        try:
            emotion = user_mood.current_emotion
            
            # 감정에 따른 스트레스 레벨 조정
            stress_impact = {
                EmotionType.STRESSED: 10,
                EmotionType.ANXIOUS: 8,
                EmotionType.FRUSTRATED: 6,
                EmotionType.ANGRY: 5,
                EmotionType.CALM: -5,
                EmotionType.HAPPY: -3,
                EmotionType.CONFIDENT: -2
            }
            
            stress_change = stress_impact.get(emotion.primary, 0) * emotion.intensity
            user_mood.stress_level = max(0, min(100, user_mood.stress_level + stress_change * 0.1))
            
            # 에너지 레벨 조정
            energy_impact = {
                EmotionType.EXCITED: 5,
                EmotionType.HAPPY: 3,
                EmotionType.CONFIDENT: 2,
                EmotionType.FOCUSED: 1,
                EmotionType.STRESSED: -3,
                EmotionType.SAD: -5,
                EmotionType.FRUSTRATED: -2
            }
            
            energy_change = energy_impact.get(emotion.primary, 0) * emotion.intensity
            user_mood.energy_level = max(0, min(100, user_mood.energy_level + energy_change * 0.1))
            
            # 집중도 조정
            focus_impact = {
                EmotionType.FOCUSED: 5,
                EmotionType.CALM: 3,
                EmotionType.CONFIDENT: 2,
                EmotionType.STRESSED: -4,
                EmotionType.ANXIOUS: -6,
                EmotionType.EXCITED: -2
            }
            
            focus_change = focus_impact.get(emotion.primary, 0) * emotion.intensity
            user_mood.focus_level = max(0, min(100, user_mood.focus_level + focus_change * 0.1))
            
            # 웰니스 점수 계산
            user_mood.wellness_score = (
                (100 - user_mood.stress_level) * 0.3 +
                user_mood.energy_level * 0.3 +
                user_mood.focus_level * 0.4
            )
            
        except Exception as e:
            logger.error(f"Wellness metrics update failed: {str(e)}")
    
    async def _analyze_emotion_patterns(self):
        """감정 패턴 분석"""
        while True:
            try:
                for user_id, user_mood in self.users.items():
                    if len(user_mood.emotion_history) >= 10:
                        # 패턴 분석
                        patterns = await self._identify_patterns(user_mood.emotion_history)
                        self.emotion_patterns[user_id] = patterns
                        
                        # 인사이트 생성
                        insights = await self._generate_insights(user_id, patterns)
                        self.insights.extend(insights)
                
                await asyncio.sleep(self.config["pattern_analysis_interval"])
                
            except Exception as e:
                logger.error(f"Pattern analysis failed: {str(e)}", exc_info=True)
                await asyncio.sleep(300)
    
    async def _identify_patterns(self, emotion_history: List[EmotionState]) -> List[Dict[str, Any]]:
        """감정 패턴 식별"""
        patterns = []
        
        try:
            # 최근 24시간 데이터 분석
            recent_emotions = emotion_history[-24:] if len(emotion_history) >= 24 else emotion_history
            
            # 가장 빈번한 감정
            emotion_counts = {}
            for emotion_state in recent_emotions:
                emotion_counts[emotion_state.primary] = emotion_counts.get(emotion_state.primary, 0) + 1
            
            most_common = max(emotion_counts, key=emotion_counts.get) if emotion_counts else None
            
            if most_common:
                patterns.append({
                    "type": "dominant_emotion",
                    "emotion": most_common.value,
                    "frequency": emotion_counts[most_common] / len(recent_emotions),
                    "description": f"Most common emotion: {most_common.value}"
                })
            
            # 스트레스 패턴
            stress_emotions = [EmotionType.STRESSED, EmotionType.ANXIOUS, EmotionType.FRUSTRATED]
            stress_count = sum(1 for e in recent_emotions if e.primary in stress_emotions)
            
            if stress_count > len(recent_emotions) * 0.3:
                patterns.append({
                    "type": "stress_pattern",
                    "severity": "high" if stress_count > len(recent_emotions) * 0.5 else "medium",
                    "frequency": stress_count / len(recent_emotions),
                    "description": "Elevated stress levels detected"
                })
            
            # 에너지 패턴
            high_energy_emotions = [EmotionType.EXCITED, EmotionType.HAPPY, EmotionType.CONFIDENT]
            energy_count = sum(1 for e in recent_emotions if e.primary in high_energy_emotions)
            
            if energy_count > len(recent_emotions) * 0.4:
                patterns.append({
                    "type": "energy_pattern",
                    "level": "high",
                    "frequency": energy_count / len(recent_emotions),
                    "description": "High energy levels maintained"
                })
            
        except Exception as e:
            logger.error(f"Pattern identification failed: {str(e)}")
        
        return patterns
    
    async def _generate_insights(self, user_id: str, patterns: List[Dict[str, Any]]) -> List[EmotionalInsight]:
        """인사이트 생성"""
        insights = []
        
        try:
            for pattern in patterns:
                if pattern["type"] == "stress_pattern" and pattern["severity"] == "high":
                    insights.append(EmotionalInsight(
                        insight_id=f"insight_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type="alert",
                        title="High Stress Level Detected",
                        description="Your stress levels have been consistently high. Consider taking breaks and practicing stress management techniques.",
                        confidence=0.85,
                        actionable_items=[
                            "Take a 10-minute break",
                            "Practice deep breathing exercises",
                            "Consider delegating some tasks",
                            "Schedule a wellness check-in"
                        ],
                        priority="high"
                    ))
                
                elif pattern["type"] == "energy_pattern" and pattern["level"] == "high":
                    insights.append(EmotionalInsight(
                        insight_id=f"insight_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type="recommendation",
                        title="Optimal Energy Window",
                        description="You're in a high-energy state. This is a great time for challenging tasks and creative work.",
                        confidence=0.9,
                        actionable_items=[
                            "Tackle your most important tasks now",
                            "Engage in creative problem-solving",
                            "Consider collaborative activities",
                            "Set ambitious but achievable goals"
                        ],
                        priority="medium"
                    ))
                
                elif pattern["type"] == "dominant_emotion" and pattern["emotion"] == "focused":
                    insights.append(EmotionalInsight(
                        insight_id=f"insight_{uuid.uuid4().hex[:8]}",
                        user_id=user_id,
                        insight_type="pattern",
                        title="Strong Focus Pattern",
                        description="You've maintained excellent focus levels. Keep up the great work!",
                        confidence=0.8,
                        actionable_items=[
                            "Continue current work practices",
                            "Share focus techniques with team",
                            "Consider mentoring others",
                            "Document successful strategies"
                        ],
                        priority="low"
                    ))
            
        except Exception as e:
            logger.error(f"Insight generation failed: {str(e)}")
        
        return insights
    
    async def _calculate_wellness_scores(self):
        """웰니스 점수 계산"""
        while True:
            try:
                for user_mood in self.users.values():
                    # 이미 _update_wellness_metrics에서 계산되므로 여기서는 검증만
                    if user_mood.wellness_score < 40:
                        # 낮은 웰니스 점수에 대한 알림 생성
                        await self._create_wellness_alert(user_mood)
                
                await asyncio.sleep(self.config["wellness_calculation_interval"])
                
            except Exception as e:
                logger.error(f"Wellness calculation failed: {str(e)}", exc_info=True)
                await asyncio.sleep(600)
    
    async def _create_wellness_alert(self, user_mood: UserMood):
        """웰니스 알림 생성"""
        try:
            alert = EmotionalInsight(
                insight_id=f"wellness_alert_{uuid.uuid4().hex[:8]}",
                user_id=user_mood.user_id,
                insight_type="alert",
                title="Wellness Score Below Threshold",
                description=f"Your wellness score is {user_mood.wellness_score:.1f}. Consider taking steps to improve your well-being.",
                confidence=0.9,
                actionable_items=[
                    "Take a longer break",
                    "Practice mindfulness or meditation",
                    "Engage in physical activity",
                    "Connect with colleagues or friends",
                    "Consider adjusting workload"
                ],
                priority="high"
            )
            
            self.insights.append(alert)
            
        except Exception as e:
            logger.error(f"Wellness alert creation failed: {str(e)}")
    
    async def _analyze_team_dynamics(self):
        """팀 역학 분석"""
        while True:
            try:
                for team_id, team_dynamics in self.teams.items():
                    # 팀 구성원들의 감정 상태 분석
                    team_emotions = []
                    team_stress_levels = []
                    
                    # 실제로는 팀 구성원 데이터를 가져와야 하지만, 여기서는 시뮬레이션
                    for _ in range(5):  # 5명의 팀원 시뮬레이션
                        team_emotions.append(random.choice(list(EmotionType)))
                        team_stress_levels.append(random.uniform(20, 80))
                    
                    # 전체 팀 기분 계산
                    positive_emotions = [EmotionType.HAPPY, EmotionType.EXCITED, EmotionType.CONFIDENT, EmotionType.CALM]
                    positive_count = sum(1 for e in team_emotions if e in positive_emotions)
                    
                    if positive_count > len(team_emotions) * 0.6:
                        team_dynamics.overall_mood = EmotionType.HAPPY
                    elif positive_count > len(team_emotions) * 0.4:
                        team_dynamics.overall_mood = EmotionType.CALM
                    else:
                        team_dynamics.overall_mood = EmotionType.STRESSED
                    
                    # 응집력 점수 업데이트
                    avg_stress = sum(team_stress_levels) / len(team_stress_levels)
                    team_dynamics.cohesion_score = max(0, 100 - avg_stress * 0.5)
                    
                    # 갈등 위험도 계산
                    high_stress_count = sum(1 for s in team_stress_levels if s > 70)
                    team_dynamics.conflict_risk = (high_stress_count / len(team_stress_levels)) * 100
                    
                    # 번아웃 위험도 계산
                    team_dynamics.burnout_risk = min(100, avg_stress * 0.8)
                    
                    # 권장사항 업데이트
                    team_dynamics.recommendations = await self._generate_team_recommendations(team_dynamics)
                    team_dynamics.last_analyzed = datetime.now()
                
                await asyncio.sleep(self.config["team_analysis_interval"])
                
            except Exception as e:
                logger.error(f"Team dynamics analysis failed: {str(e)}", exc_info=True)
                await asyncio.sleep(900)
    
    async def _generate_team_recommendations(self, team_dynamics: TeamEmotionalDynamics) -> List[str]:
        """팀 권장사항 생성"""
        recommendations = []
        
        try:
            if team_dynamics.conflict_risk > 50:
                recommendations.append("Schedule conflict resolution session")
                recommendations.append("Implement team communication guidelines")
            
            if team_dynamics.burnout_risk > 60:
                recommendations.append("Consider workload redistribution")
                recommendations.append("Plan team wellness activities")
                recommendations.append("Increase break frequency")
            
            if team_dynamics.cohesion_score < 60:
                recommendations.append("Organize team building activities")
                recommendations.append("Improve collaboration tools")
                recommendations.append("Schedule regular team check-ins")
            
            if team_dynamics.overall_mood in [EmotionType.STRESSED, EmotionType.FRUSTRATED]:
                recommendations.append("Address team stressors")
                recommendations.append("Provide stress management resources")
                recommendations.append("Review project timelines")
            
            if not recommendations:
                recommendations.append("Team dynamics are healthy - maintain current practices")
            
        except Exception as e:
            logger.error(f"Team recommendations generation failed: {str(e)}")
        
        return recommendations
    
    # Public API Methods
    
    async def get_user_emotion(self, user_id: str) -> Optional[Dict[str, Any]]:
        """사용자 감정 상태 조회"""
        user_mood = self.users.get(user_id)
        if not user_mood:
            return None
        
        return {
            "user_id": user_mood.user_id,
            "name": user_mood.name,
            "current_emotion": {
                "primary": user_mood.current_emotion.primary.value,
                "intensity": user_mood.current_emotion.intensity,
                "confidence": user_mood.current_emotion.confidence,
                "timestamp": user_mood.current_emotion.timestamp.isoformat(),
                "triggers": user_mood.current_emotion.triggers,
                "context": user_mood.current_emotion.context
            },
            "wellness_metrics": {
                "stress_level": user_mood.stress_level,
                "energy_level": user_mood.energy_level,
                "focus_level": user_mood.focus_level,
                "wellness_score": user_mood.wellness_score
            },
            "preferences": {
                "communication_style": user_mood.preferences.communication_style.value,
                "work_pace": user_mood.preferences.work_pace.value,
                "feedback_type": user_mood.preferences.feedback_type.value
            },
            "last_updated": user_mood.last_updated.isoformat()
        }
    
    async def get_emotion_history(self, user_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """감정 히스토리 조회"""
        user_mood = self.users.get(user_id)
        if not user_mood:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        filtered_history = [
            e for e in user_mood.emotion_history
            if e.timestamp >= cutoff_time
        ]
        
        return [
            {
                "primary": emotion.primary.value,
                "intensity": emotion.intensity,
                "confidence": emotion.confidence,
                "timestamp": emotion.timestamp.isoformat(),
                "triggers": emotion.triggers,
                "context": emotion.context
            }
            for emotion in filtered_history
        ]
    
    async def get_team_dynamics(self, team_id: str) -> Optional[Dict[str, Any]]:
        """팀 역학 조회"""
        team_dynamics = self.teams.get(team_id)
        if not team_dynamics:
            return None
        
        return {
            "team_id": team_dynamics.team_id,
            "team_name": team_dynamics.team_name,
            "overall_mood": team_dynamics.overall_mood.value,
            "cohesion_score": team_dynamics.cohesion_score,
            "stress_indicators": team_dynamics.stress_indicators,
            "productivity_correlation": team_dynamics.productivity_correlation,
            "conflict_risk": team_dynamics.conflict_risk,
            "burnout_risk": team_dynamics.burnout_risk,
            "recommendations": team_dynamics.recommendations,
            "last_analyzed": team_dynamics.last_analyzed.isoformat()
        }
    
    async def get_insights(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """사용자 인사이트 조회"""
        user_insights = [
            insight for insight in self.insights
            if insight.user_id == user_id
        ]
        
        # 최신순 정렬
        user_insights.sort(key=lambda x: x.generated_at, reverse=True)
        
        return [
            {
                "insight_id": insight.insight_id,
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "confidence": insight.confidence,
                "actionable_items": insight.actionable_items,
                "priority": insight.priority,
                "generated_at": insight.generated_at.isoformat()
            }
            for insight in user_insights[:limit]
        ]
    
    async def get_adaptive_theme(self, user_id: str) -> str:
        """적응형 테마 조회"""
        user_mood = self.users.get(user_id)
        if not user_mood:
            return "default"
        
        return self.emotion_themes.get(user_mood.current_emotion.primary, "default")
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """사용자 선호도 업데이트"""
        try:
            user_mood = self.users.get(user_id)
            if not user_mood:
                return False
            
            if "communication_style" in preferences:
                user_mood.preferences.communication_style = CommunicationStyle(preferences["communication_style"])
            
            if "work_pace" in preferences:
                user_mood.preferences.work_pace = WorkPace(preferences["work_pace"])
            
            if "feedback_type" in preferences:
                user_mood.preferences.feedback_type = FeedbackType(preferences["feedback_type"])
            
            if "stress_threshold" in preferences:
                user_mood.preferences.stress_threshold = preferences["stress_threshold"]
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update user preferences: {str(e)}")
            return False
    
    async def analyze_emotion(self, user_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """감정 분석 수행"""
        try:
            # 실제로는 텍스트, 음성, 행동 패턴 등을 분석
            # 여기서는 시뮬레이션
            
            detected_emotion = await self._detect_emotion(user_id)
            if not detected_emotion:
                return {"error": "Failed to detect emotion"}
            
            # 사용자 감정 상태 업데이트
            user_mood = self.users.get(user_id)
            if user_mood:
                user_mood.current_emotion = detected_emotion
                user_mood.emotion_history.append(detected_emotion)
                await self._update_wellness_metrics(user_mood)
            
            return {
                "emotion": detected_emotion.primary.value,
                "intensity": detected_emotion.intensity,
                "confidence": detected_emotion.confidence,
                "recommended_theme": self.emotion_themes.get(detected_emotion.primary, "default"),
                "wellness_impact": {
                    "stress_change": random.uniform(-5, 5),
                    "energy_change": random.uniform(-3, 3),
                    "focus_change": random.uniform(-2, 4)
                }
            }
            
        except Exception as e:
            logger.error(f"Emotion analysis failed: {str(e)}")
            return {"error": str(e)}

# 싱글톤 인스턴스
_emotional_ai_service = None

def get_emotional_ai_service() -> EmotionalAIService:
    """Emotional AI Service 싱글톤 인스턴스 반환"""
    global _emotional_ai_service
    if _emotional_ai_service is None:
        _emotional_ai_service = EmotionalAIService()
    return _emotional_ai_service