"""
AI Agent Olympics Manager
AI 에이전트 올림픽 관리 시스템 - 2025 Future Roadmap 구현
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

class CompetitionType(Enum):
    """경쟁 유형"""
    SPEED = "speed"                    # 속도 경쟁
    ACCURACY = "accuracy"              # 정확도 경쟁
    COLLABORATION = "collaboration"    # 협업 경쟁
    CREATIVITY = "creativity"          # 창의성 경쟁
    ENDURANCE = "endurance"           # 지구력 경쟁
    EFFICIENCY = "efficiency"          # 효율성 경쟁

class AgentStatus(Enum):
    """에이전트 상태"""
    COMPETING = "competing"    # 경쟁 중
    IDLE = "idle"             # 대기 중
    TRAINING = "training"      # 훈련 중
    OFFLINE = "offline"        # 오프라인

class CompetitionStatus(Enum):
    """경쟁 상태"""
    UPCOMING = "upcoming"      # 예정
    ACTIVE = "active"         # 진행 중
    COMPLETED = "completed"    # 완료
    CANCELLED = "cancelled"    # 취소

@dataclass
class AgentPerformance:
    """에이전트 성능 지표"""
    speed: float = 0.0
    accuracy: float = 0.0
    efficiency: float = 0.0
    creativity: float = 0.0
    collaboration: float = 0.0

@dataclass
class AgentStats:
    """에이전트 통계"""
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_competitions: int = 0
    ranking: int = 0
    points: int = 0
    win_rate: float = 0.0

@dataclass
class Agent:
    """AI 에이전트"""
    id: str
    name: str
    type: str
    avatar: str
    performance: AgentPerformance
    stats: AgentStats
    status: AgentStatus = AgentStatus.IDLE
    current_position: Optional[int] = None
    progress: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Competition:
    """경쟁 대회"""
    id: str
    name: str
    type: CompetitionType
    status: CompetitionStatus
    participants: List[Agent]
    start_time: datetime
    duration: int  # 초
    prize: int
    spectators: int
    description: str
    results: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CompetitionResult:
    """경쟁 결과"""
    competition_id: str
    winner_id: str
    rankings: List[Tuple[str, float]]  # (agent_id, score)
    performance_metrics: Dict[str, Dict[str, float]]
    duration: float
    spectator_count: int
    highlights: List[str]
    completed_at: datetime = field(default_factory=datetime.now)

class AgentOlympicsManager:
    """AI 에이전트 올림픽 관리자"""
    
    def __init__(self):
        # 데이터 저장소
        self.agents: Dict[str, Agent] = {}
        self.competitions: Dict[str, Competition] = {}
        self.competition_history: List[CompetitionResult] = []
        
        # 실시간 상태
        self.active_competitions: Dict[str, Competition] = {}
        self.live_progress: Dict[str, Dict[str, float]] = {}  # competition_id -> agent_id -> progress
        self.spectator_counts: Dict[str, int] = {}
        
        # 설정
        self.config = {
            "max_concurrent_competitions": 5,
            "default_competition_duration": 300,  # 5분
            "spectator_update_interval": 10,  # 10초
            "performance_decay_rate": 0.95,  # 성능 감소율
            "ranking_update_interval": 60,  # 1분
        }
        
        # 초기 데이터 생성
        self._initialize_mock_data()
        
        # 백그라운드 작업 시작
        asyncio.create_task(self._start_background_tasks())
        
        logger.info("Agent Olympics Manager initialized")
    
    def _initialize_mock_data(self):
        """초기 모의 데이터 생성"""
        # 에이전트 생성
        agent_templates = [
            ("Lightning Bolt", "Speed Specialist", "⚡", {"speed": 0.95, "accuracy": 0.85, "efficiency": 0.90, "creativity": 0.70, "collaboration": 0.80}),
            ("Precision Master", "Accuracy Expert", "🎯", {"speed": 0.75, "accuracy": 0.98, "efficiency": 0.85, "creativity": 0.80, "collaboration": 0.90}),
            ("Creative Genius", "Innovation Leader", "🧠", {"speed": 0.80, "accuracy": 0.88, "efficiency": 0.75, "creativity": 0.99, "collaboration": 0.85}),
            ("Team Player", "Collaboration Pro", "🤝", {"speed": 0.85, "accuracy": 0.90, "efficiency": 0.88, "creativity": 0.85, "collaboration": 0.97}),
            ("Efficiency King", "Resource Optimizer", "⚙️", {"speed": 0.88, "accuracy": 0.92, "efficiency": 0.96, "creativity": 0.78, "collaboration": 0.82}),
            ("Speed Demon", "Ultra Fast", "🏃", {"speed": 0.99, "accuracy": 0.75, "efficiency": 0.85, "creativity": 0.65, "collaboration": 0.70}),
            ("Perfect Balance", "All-Rounder", "⚖️", {"speed": 0.85, "accuracy": 0.85, "efficiency": 0.85, "creativity": 0.85, "collaboration": 0.85}),
            ("Innovation Bot", "Creative Thinker", "💡", {"speed": 0.70, "accuracy": 0.80, "efficiency": 0.75, "creativity": 0.95, "collaboration": 0.88}),
        ]
        
        for i, (name, agent_type, avatar, perf) in enumerate(agent_templates):
            agent_id = f"agent_{i+1}"
            
            # 통계 생성
            total_comps = random.randint(50, 100)
            wins = random.randint(int(total_comps * 0.2), int(total_comps * 0.6))
            losses = random.randint(int(total_comps * 0.2), int(total_comps * 0.5))
            draws = total_comps - wins - losses
            
            stats = AgentStats(
                wins=wins,
                losses=losses,
                draws=draws,
                total_competitions=total_comps,
                ranking=i + 1,
                points=wins * 50 + draws * 20 - losses * 10,
                win_rate=wins / total_comps if total_comps > 0 else 0.0
            )
            
            agent = Agent(
                id=agent_id,
                name=name,
                type=agent_type,
                avatar=avatar,
                performance=AgentPerformance(**perf),
                stats=stats,
                status=AgentStatus.IDLE
            )
            
            self.agents[agent_id] = agent
        
        # 경쟁 대회 생성
        self._create_sample_competitions()
    
    def _create_sample_competitions(self):
        """샘플 경쟁 대회 생성"""
        competitions_data = [
            {
                "name": "Speed Challenge 2025",
                "type": CompetitionType.SPEED,
                "status": CompetitionStatus.ACTIVE,
                "duration": 300,
                "prize": 1000,
                "description": "Ultimate speed test for AI agents - who can process tasks the fastest?"
            },
            {
                "name": "Collaboration Championship",
                "type": CompetitionType.COLLABORATION,
                "status": CompetitionStatus.UPCOMING,
                "duration": 600,
                "prize": 2000,
                "description": "Test of teamwork and coordination between multiple agents"
            },
            {
                "name": "Creativity Contest",
                "type": CompetitionType.CREATIVITY,
                "status": CompetitionStatus.UPCOMING,
                "duration": 900,
                "prize": 1500,
                "description": "Innovation and creative problem-solving competition"
            }
        ]
        
        for i, comp_data in enumerate(competitions_data):
            comp_id = f"comp_{i+1}"
            
            # 참가자 선택 (랜덤하게 4-6명)
            participant_count = random.randint(4, 6)
            participants = random.sample(list(self.agents.values()), participant_count)
            
            competition = Competition(
                id=comp_id,
                name=comp_data["name"],
                type=comp_data["type"],
                status=comp_data["status"],
                participants=participants,
                start_time=datetime.now() if comp_data["status"] == CompetitionStatus.ACTIVE else datetime.now() + timedelta(hours=1),
                duration=comp_data["duration"],
                prize=comp_data["prize"],
                spectators=random.randint(500, 2000),
                description=comp_data["description"]
            )
            
            self.competitions[comp_id] = competition
            
            if comp_data["status"] == CompetitionStatus.ACTIVE:
                self.active_competitions[comp_id] = competition
                # 초기 진행률 설정
                self.live_progress[comp_id] = {agent.id: 0.0 for agent in participants}
    
    async def _start_background_tasks(self):
        """백그라운드 작업 시작"""
        # 실시간 경쟁 업데이트
        asyncio.create_task(self._update_live_competitions())
        # 관중 수 업데이트
        asyncio.create_task(self._update_spectator_counts())
        # 랭킹 업데이트
        asyncio.create_task(self._update_rankings())
    
    async def _update_live_competitions(self):
        """실시간 경쟁 업데이트"""
        while True:
            try:
                for comp_id, competition in self.active_competitions.items():
                    if comp_id in self.live_progress:
                        # 각 에이전트의 진행률 업데이트
                        for agent in competition.participants:
                            current_progress = self.live_progress[comp_id].get(agent.id, 0.0)
                            
                            if current_progress < 100.0:
                                # 성능에 따른 진행률 증가
                                speed_factor = getattr(agent.performance, competition.type.value, 0.5)
                                random_factor = 0.5 + random.random() * 0.5
                                increment = speed_factor * random_factor * 0.8
                                
                                new_progress = min(100.0, current_progress + increment)
                                self.live_progress[comp_id][agent.id] = new_progress
                                
                                # 에이전트 상태 업데이트
                                agent.progress = new_progress
                                agent.status = AgentStatus.COMPETING
                        
                        # 경쟁 완료 확인
                        max_progress = max(self.live_progress[comp_id].values())
                        if max_progress >= 100.0:
                            await self._complete_competition(comp_id)
                
                await asyncio.sleep(1)  # 1초마다 업데이트
                
            except Exception as e:
                logger.error(f"Live competition update failed: {str(e)}", exc_info=True)
                await asyncio.sleep(5)
    
    async def _update_spectator_counts(self):
        """관중 수 업데이트"""
        while True:
            try:
                for comp_id, competition in self.active_competitions.items():
                    # 관중 수 변동 (±10%)
                    base_count = competition.spectators
                    variation = random.uniform(-0.1, 0.1)
                    new_count = int(base_count * (1 + variation))
                    competition.spectators = max(0, new_count)
                    self.spectator_counts[comp_id] = competition.spectators
                
                await asyncio.sleep(self.config["spectator_update_interval"])
                
            except Exception as e:
                logger.error(f"Spectator count update failed: {str(e)}", exc_info=True)
                await asyncio.sleep(30)
    
    async def _update_rankings(self):
        """랭킹 업데이트"""
        while True:
            try:
                # 포인트 기준으로 랭킹 재계산
                sorted_agents = sorted(
                    self.agents.values(),
                    key=lambda a: a.stats.points,
                    reverse=True
                )
                
                for i, agent in enumerate(sorted_agents):
                    agent.stats.ranking = i + 1
                
                await asyncio.sleep(self.config["ranking_update_interval"])
                
            except Exception as e:
                logger.error(f"Ranking update failed: {str(e)}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _complete_competition(self, comp_id: str):
        """경쟁 완료 처리"""
        try:
            competition = self.active_competitions.get(comp_id)
            if not competition:
                return
            
            # 결과 계산
            progress_data = self.live_progress.get(comp_id, {})
            rankings = sorted(
                [(agent_id, progress) for agent_id, progress in progress_data.items()],
                key=lambda x: x[1],
                reverse=True
            )
            
            # 승자 결정
            winner_id = rankings[0][0] if rankings else None
            
            # 성능 메트릭 수집
            performance_metrics = {}
            for agent in competition.participants:
                perf = agent.performance
                performance_metrics[agent.id] = {
                    "speed": perf.speed,
                    "accuracy": perf.accuracy,
                    "efficiency": perf.efficiency,
                    "creativity": perf.creativity,
                    "collaboration": perf.collaboration,
                    "final_progress": progress_data.get(agent.id, 0.0)
                }
            
            # 결과 저장
            result = CompetitionResult(
                competition_id=comp_id,
                winner_id=winner_id,
                rankings=rankings,
                performance_metrics=performance_metrics,
                duration=(datetime.now() - competition.start_time).total_seconds(),
                spectator_count=competition.spectators,
                highlights=[
                    f"{self.agents[winner_id].name} wins with {rankings[0][1]:.1f}% completion!" if winner_id else "Competition completed",
                    f"Total spectators: {competition.spectators}",
                    f"Competition type: {competition.type.value}"
                ]
            )
            
            self.competition_history.append(result)
            
            # 에이전트 통계 업데이트
            await self._update_agent_stats(competition, rankings)
            
            # 경쟁 상태 업데이트
            competition.status = CompetitionStatus.COMPLETED
            competition.results = result.__dict__
            
            # 활성 경쟁에서 제거
            if comp_id in self.active_competitions:
                del self.active_competitions[comp_id]
            if comp_id in self.live_progress:
                del self.live_progress[comp_id]
            
            # 에이전트 상태 초기화
            for agent in competition.participants:
                agent.status = AgentStatus.IDLE
                agent.progress = 0.0
                agent.current_position = None
            
            logger.info(f"Competition {comp_id} completed. Winner: {winner_id}")
            
        except Exception as e:
            logger.error(f"Failed to complete competition {comp_id}: {str(e)}", exc_info=True)
    
    async def _update_agent_stats(self, competition: Competition, rankings: List[Tuple[str, float]]):
        """에이전트 통계 업데이트"""
        try:
            for i, (agent_id, score) in enumerate(rankings):
                agent = self.agents.get(agent_id)
                if not agent:
                    continue
                
                # 순위에 따른 포인트 계산
                position = i + 1
                if position == 1:
                    points = 100
                    agent.stats.wins += 1
                elif position == 2:
                    points = 70
                    agent.stats.losses += 1
                elif position == 3:
                    points = 50
                    agent.stats.losses += 1
                else:
                    points = 20
                    agent.stats.losses += 1
                
                # 통계 업데이트
                agent.stats.points += points
                agent.stats.total_competitions += 1
                agent.stats.win_rate = agent.stats.wins / agent.stats.total_competitions
                
                # 성능 조정 (경험에 따른 미세 조정)
                performance_boost = 0.001 if position <= 3 else -0.0005
                comp_type = competition.type.value
                
                if hasattr(agent.performance, comp_type):
                    current_value = getattr(agent.performance, comp_type)
                    new_value = min(1.0, max(0.0, current_value + performance_boost))
                    setattr(agent.performance, comp_type, new_value)
            
        except Exception as e:
            logger.error(f"Failed to update agent stats: {str(e)}", exc_info=True)
    
    # Public API Methods
    
    async def get_agents(self) -> List[Dict[str, Any]]:
        """모든 에이전트 조회"""
        return [self._agent_to_dict(agent) for agent in self.agents.values()]
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """특정 에이전트 조회"""
        agent = self.agents.get(agent_id)
        return self._agent_to_dict(agent) if agent else None
    
    async def get_competitions(self) -> List[Dict[str, Any]]:
        """모든 경쟁 대회 조회"""
        return [self._competition_to_dict(comp) for comp in self.competitions.values()]
    
    async def get_active_competitions(self) -> List[Dict[str, Any]]:
        """활성 경쟁 대회 조회"""
        return [self._competition_to_dict(comp) for comp in self.active_competitions.values()]
    
    async def get_competition(self, comp_id: str) -> Optional[Dict[str, Any]]:
        """특정 경쟁 대회 조회"""
        comp = self.competitions.get(comp_id)
        return self._competition_to_dict(comp) if comp else None
    
    async def get_live_progress(self, comp_id: str) -> Optional[Dict[str, float]]:
        """실시간 경쟁 진행률 조회"""
        return self.live_progress.get(comp_id)
    
    async def get_leaderboard(self) -> List[Dict[str, Any]]:
        """리더보드 조회"""
        sorted_agents = sorted(
            self.agents.values(),
            key=lambda a: a.stats.points,
            reverse=True
        )
        return [self._agent_to_dict(agent) for agent in sorted_agents]
    
    async def start_competition(self, comp_id: str) -> bool:
        """경쟁 시작"""
        try:
            competition = self.competitions.get(comp_id)
            if not competition or competition.status != CompetitionStatus.UPCOMING:
                return False
            
            # 경쟁 시작
            competition.status = CompetitionStatus.ACTIVE
            competition.start_time = datetime.now()
            self.active_competitions[comp_id] = competition
            
            # 진행률 초기화
            self.live_progress[comp_id] = {agent.id: 0.0 for agent in competition.participants}
            
            # 에이전트 상태 업데이트
            for agent in competition.participants:
                agent.status = AgentStatus.COMPETING
                agent.progress = 0.0
            
            logger.info(f"Competition {comp_id} started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start competition {comp_id}: {str(e)}", exc_info=True)
            return False
    
    async def stop_competition(self, comp_id: str) -> bool:
        """경쟁 중단"""
        try:
            if comp_id in self.active_competitions:
                await self._complete_competition(comp_id)
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to stop competition {comp_id}: {str(e)}", exc_info=True)
            return False
    
    async def create_competition(self, competition_data: Dict[str, Any]) -> str:
        """새 경쟁 대회 생성"""
        try:
            comp_id = f"comp_{uuid.uuid4().hex[:8]}"
            
            # 참가자 선택
            participant_ids = competition_data.get("participant_ids", [])
            participants = [self.agents[aid] for aid in participant_ids if aid in self.agents]
            
            competition = Competition(
                id=comp_id,
                name=competition_data["name"],
                type=CompetitionType(competition_data["type"]),
                status=CompetitionStatus.UPCOMING,
                participants=participants,
                start_time=datetime.now() + timedelta(minutes=5),  # 5분 후 시작
                duration=competition_data.get("duration", 300),
                prize=competition_data.get("prize", 500),
                spectators=random.randint(100, 500),
                description=competition_data.get("description", "")
            )
            
            self.competitions[comp_id] = competition
            
            logger.info(f"Competition {comp_id} created: {competition.name}")
            return comp_id
            
        except Exception as e:
            logger.error(f"Failed to create competition: {str(e)}", exc_info=True)
            raise
    
    async def get_analytics(self) -> Dict[str, Any]:
        """분석 데이터 조회"""
        try:
            total_competitions = len(self.competition_history)
            active_agents = len([a for a in self.agents.values() if a.status != AgentStatus.OFFLINE])
            total_spectators = sum(comp.spectators for comp in self.active_competitions.values())
            total_prize_pool = sum(comp.prize for comp in self.competitions.values())
            
            # 성능 트렌드 (시뮬레이션)
            performance_trends = {}
            for agent in list(self.agents.values())[:5]:  # 상위 5명
                trend_data = []
                base_performance = getattr(agent.performance, "speed", 0.5)
                for i in range(4):  # 4주간 데이터
                    variation = random.uniform(-0.05, 0.05)
                    trend_data.append(min(1.0, max(0.0, base_performance + variation)))
                performance_trends[agent.name.lower().replace(" ", "_")] = trend_data
            
            return {
                "total_competitions": total_competitions,
                "active_agents": active_agents,
                "total_spectators": total_spectators,
                "total_prize_pool": total_prize_pool,
                "performance_trends": performance_trends,
                "competition_types": {ct.value: len([c for c in self.competitions.values() if c.type == ct]) for ct in CompetitionType},
                "agent_status_distribution": {status.value: len([a for a in self.agents.values() if a.status == status]) for status in AgentStatus}
            }
            
        except Exception as e:
            logger.error(f"Failed to get analytics: {str(e)}", exc_info=True)
            return {}
    
    def _agent_to_dict(self, agent: Agent) -> Dict[str, Any]:
        """에이전트를 딕셔너리로 변환"""
        return {
            "id": agent.id,
            "name": agent.name,
            "type": agent.type,
            "avatar": agent.avatar,
            "performance": {
                "speed": agent.performance.speed,
                "accuracy": agent.performance.accuracy,
                "efficiency": agent.performance.efficiency,
                "creativity": agent.performance.creativity,
                "collaboration": agent.performance.collaboration
            },
            "stats": {
                "wins": agent.stats.wins,
                "losses": agent.stats.losses,
                "draws": agent.stats.draws,
                "total_competitions": agent.stats.total_competitions,
                "ranking": agent.stats.ranking,
                "points": agent.stats.points,
                "win_rate": agent.stats.win_rate
            },
            "status": agent.status.value,
            "current_position": agent.current_position,
            "progress": agent.progress,
            "created_at": agent.created_at.isoformat()
        }
    
    def _competition_to_dict(self, competition: Competition) -> Dict[str, Any]:
        """경쟁 대회를 딕셔너리로 변환"""
        return {
            "id": competition.id,
            "name": competition.name,
            "type": competition.type.value,
            "status": competition.status.value,
            "participants": [self._agent_to_dict(agent) for agent in competition.participants],
            "start_time": competition.start_time.isoformat(),
            "duration": competition.duration,
            "prize": competition.prize,
            "spectators": competition.spectators,
            "description": competition.description,
            "results": competition.results,
            "created_at": competition.created_at.isoformat()
        }

# 싱글톤 인스턴스
_olympics_manager = None

def get_olympics_manager() -> AgentOlympicsManager:
    """Agent Olympics Manager 싱글톤 인스턴스 반환"""
    global _olympics_manager
    if _olympics_manager is None:
        _olympics_manager = AgentOlympicsManager()
    return _olympics_manager