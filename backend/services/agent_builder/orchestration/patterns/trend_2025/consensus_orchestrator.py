"""
Consensus Building Orchestrator
합의 기반 의사결정 오케스트레이션 패턴
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from backend.services.agent_builder.orchestration.base_orchestrator import BaseOrchestrator
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


class VoteType(Enum):
    FOR = "for"
    AGAINST = "against"
    ABSTAIN = "abstain"


class ConsensusStrategy(Enum):
    SIMPLE_MAJORITY = "simple_majority"
    WEIGHTED_VOTING = "weighted_voting"
    UNANIMITY = "unanimity"
    SUPERMAJORITY = "supermajority"


@dataclass
class Vote:
    """투표 정보"""
    voter_id: str
    voter_name: str
    vote_type: VoteType
    confidence: float  # 0.0 - 1.0
    reasoning: Optional[str] = None
    weight: float = 1.0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ConsensusRound:
    """합의 라운드 정보"""
    round_number: int
    topic: str
    description: str
    votes: List[Vote]
    start_time: str
    end_time: Optional[str] = None
    consensus_reached: bool = False
    consensus_level: float = 0.0
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().isoformat()


@dataclass
class ConsensusSession:
    """합의 세션 정보"""
    session_id: str
    topic: str
    description: str
    participants: List[str]
    strategy: ConsensusStrategy
    threshold: float  # 합의 임계값 (0.0 - 1.0)
    max_rounds: int
    round_timeout: int  # 라운드 제한 시간 (초)
    current_round: int = 1
    rounds: List[ConsensusRound] = None
    status: str = "active"  # active, completed, failed, timeout
    facilitator_id: Optional[str] = None
    
    def __post_init__(self):
        if self.rounds is None:
            self.rounds = []
        if not self.session_id:
            self.session_id = str(uuid.uuid4())


class ConsensusOrchestrator(BaseOrchestrator):
    """합의 기반 의사결정 오케스트레이터"""
    
    def __init__(self):
        super().__init__()
        self.pattern_type = "consensus_building"
        self.active_sessions: Dict[str, ConsensusSession] = {}
        
    async def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """설정 검증"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # 필수 필드 검증
            required_fields = ["consensus_strategy", "threshold", "max_rounds", "participants"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Missing required field: {field}")
            
            # 임계값 검증
            threshold = config.get("threshold", 0.5)
            if not 0.0 <= threshold <= 1.0:
                errors.append("Threshold must be between 0.0 and 1.0")
            
            # 참가자 수 검증
            participants = config.get("participants", [])
            if len(participants) < 2:
                errors.append("At least 2 participants required for consensus")
            elif len(participants) > 20:
                warnings.append("Large number of participants may slow down consensus")
            
            # 전략별 검증
            strategy = config.get("consensus_strategy", "simple_majority")
            if strategy == "unanimity" and threshold < 1.0:
                suggestions.append("Unanimity strategy requires threshold of 1.0")
            elif strategy == "supermajority" and threshold < 0.67:
                suggestions.append("Supermajority typically requires threshold >= 0.67")
            
            # 라운드 수 검증
            max_rounds = config.get("max_rounds", 3)
            if max_rounds < 1:
                errors.append("Max rounds must be at least 1")
            elif max_rounds > 10:
                warnings.append("Too many rounds may lead to decision fatigue")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Configuration validation error: {e}")
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": warnings,
                "suggestions": suggestions
            }
    
    async def execute(self, config: Dict[str, Any], input_data: Dict[str, Any], 
                     user_id: str, execution_id: str) -> Dict[str, Any]:
        """합의 기반 실행"""
        try:
            logger.info(f"Starting consensus orchestration: {execution_id}")
            
            # 합의 세션 생성
            session = await self._create_consensus_session(config, input_data, execution_id)
            self.active_sessions[session.session_id] = session
            
            # 합의 프로세스 실행
            result = await self._run_consensus_process(session, config, input_data)
            
            # 세션 정리
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Consensus orchestration error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_id": execution_id
            }
    
    async def _create_consensus_session(self, config: Dict[str, Any], 
                                      input_data: Dict[str, Any], 
                                      execution_id: str) -> ConsensusSession:
        """합의 세션 생성"""
        strategy_map = {
            "simple_majority": ConsensusStrategy.SIMPLE_MAJORITY,
            "weighted_voting": ConsensusStrategy.WEIGHTED_VOTING,
            "unanimity": ConsensusStrategy.UNANIMITY,
            "supermajority": ConsensusStrategy.SUPERMAJORITY
        }
        
        session = ConsensusSession(
            session_id=execution_id,
            topic=input_data.get("topic", "Decision Making"),
            description=input_data.get("description", "Consensus building session"),
            participants=config.get("participants", []),
            strategy=strategy_map.get(config.get("consensus_strategy", "simple_majority")),
            threshold=config.get("threshold", 0.5),
            max_rounds=config.get("max_rounds", 3),
            round_timeout=config.get("round_timeout", 300),  # 5분
            facilitator_id=config.get("facilitator_id")
        )
        
        logger.info(f"Created consensus session: {session.session_id}")
        return session
    
    async def _run_consensus_process(self, session: ConsensusSession, 
                                   config: Dict[str, Any], 
                                   input_data: Dict[str, Any]) -> Dict[str, Any]:
        """합의 프로세스 실행"""
        try:
            consensus_reached = False
            final_decision = None
            
            for round_num in range(1, session.max_rounds + 1):
                logger.info(f"Starting consensus round {round_num}/{session.max_rounds}")
                
                # 라운드 생성
                round_data = ConsensusRound(
                    round_number=round_num,
                    topic=session.topic,
                    description=f"Round {round_num} of consensus building",
                    votes=[]
                )
                
                # 투표 수집
                votes = await self._collect_votes(session, round_data, config, input_data)
                round_data.votes = votes
                
                # 합의 분석
                consensus_result = await self._analyze_consensus(session, round_data)
                round_data.consensus_reached = consensus_result["reached"]
                round_data.consensus_level = consensus_result["level"]
                round_data.end_time = datetime.now().isoformat()
                
                session.rounds.append(round_data)
                session.current_round = round_num
                
                if consensus_result["reached"]:
                    consensus_reached = True
                    final_decision = consensus_result["decision"]
                    session.status = "completed"
                    break
                
                # 다음 라운드를 위한 피드백 생성
                if round_num < session.max_rounds:
                    await self._provide_round_feedback(session, round_data, consensus_result)
            
            if not consensus_reached:
                session.status = "failed"
                logger.warning(f"Consensus not reached after {session.max_rounds} rounds")
            
            return {
                "success": consensus_reached,
                "consensus_reached": consensus_reached,
                "final_decision": final_decision,
                "session_summary": await self._generate_session_summary(session),
                "rounds_completed": len(session.rounds),
                "execution_id": session.session_id
            }
            
        except Exception as e:
            logger.error(f"Consensus process error: {e}")
            session.status = "failed"
            raise
    
    async def _collect_votes(self, session: ConsensusSession, round_data: ConsensusRound,
                           config: Dict[str, Any], input_data: Dict[str, Any]) -> List[Vote]:
        """투표 수집 (병렬 처리 최적화)"""
        votes = []
        
        try:
            # 병렬 투표 수집으로 성능 개선
            tasks = [
                self._get_participant_vote(participant_id, session, round_data, config, input_data)
                for participant_id in session.participants
            ]
            
            # 모든 투표를 병렬로 수집
            vote_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for i, result in enumerate(vote_results):
                if isinstance(result, Exception):
                    self.logger.warning(f"Failed to get vote from participant {session.participants[i]}: {result}")
                elif result:
                    votes.append(result)
            
            logger.info(f"Collected {len(votes)} votes for round {round_data.round_number} (parallel)")
            return votes
            
        except Exception as e:
            logger.error(f"Vote collection error: {e}")
            return votes
    
    async def _get_participant_vote(self, participant_id: str, session: ConsensusSession,
                                  round_data: ConsensusRound, config: Dict[str, Any],
                                  input_data: Dict[str, Any]) -> Optional[Vote]:
        """개별 참가자 투표 수집"""
        try:
            # 실제 구현에서는 Agent에게 투표 요청을 보냄
            # 여기서는 시뮬레이션된 투표 생성
            
            # 투표 컨텍스트 생성
            vote_context = {
                "topic": session.topic,
                "description": session.description,
                "round_number": round_data.round_number,
                "previous_rounds": [asdict(r) for r in session.rounds],
                "current_votes": [asdict(v) for v in round_data.votes]
            }
            
            # Agent에게 투표 요청 (시뮬레이션)
            vote_response = await self._simulate_agent_vote(participant_id, vote_context)
            
            if vote_response:
                vote = Vote(
                    voter_id=participant_id,
                    voter_name=f"Agent_{participant_id}",
                    vote_type=VoteType(vote_response["vote"]),
                    confidence=vote_response["confidence"],
                    reasoning=vote_response.get("reasoning"),
                    weight=config.get("participant_weights", {}).get(participant_id, 1.0)
                )
                
                logger.debug(f"Received vote from {participant_id}: {vote.vote_type.value}")
                return vote
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting vote from {participant_id}: {e}")
            return None
    
    async def _simulate_agent_vote(self, participant_id: str, 
                                 context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Agent 투표 시뮬레이션 (실제 구현에서는 Agent 호출)"""
        import random
        
        # 시뮬레이션된 투표 생성
        vote_options = ["for", "against", "abstain"]
        weights = [0.6, 0.3, 0.1]  # 찬성에 더 높은 가중치
        
        vote = random.choices(vote_options, weights=weights)[0]
        confidence = random.uniform(0.6, 0.95)
        
        reasoning_templates = {
            "for": [
                "이 제안이 전체적으로 유익하다고 판단됩니다.",
                "제시된 근거가 충분히 설득력이 있습니다.",
                "예상되는 긍정적 효과가 부정적 영향을 상회합니다."
            ],
            "against": [
                "제안된 방안에 중대한 결함이 있다고 생각합니다.",
                "더 나은 대안이 존재할 것으로 판단됩니다.",
                "리스크가 예상 이익보다 크다고 평가됩니다."
            ],
            "abstain": [
                "추가 정보가 필요하다고 판단됩니다.",
                "현재로서는 명확한 입장을 정하기 어렵습니다.",
                "다른 참가자들의 의견을 더 들어보고 싶습니다."
            ]
        }
        
        reasoning = random.choice(reasoning_templates[vote])
        
        return {
            "vote": vote,
            "confidence": confidence,
            "reasoning": reasoning
        }
    
    async def _analyze_consensus(self, session: ConsensusSession, 
                               round_data: ConsensusRound) -> Dict[str, Any]:
        """합의 분석"""
        try:
            votes = round_data.votes
            if not votes:
                return {
                    "reached": False,
                    "level": 0.0,
                    "decision": None,
                    "analysis": "No votes received"
                }
            
            # 전략별 합의 분석
            if session.strategy == ConsensusStrategy.SIMPLE_MAJORITY:
                return await self._analyze_simple_majority(session, votes)
            elif session.strategy == ConsensusStrategy.WEIGHTED_VOTING:
                return await self._analyze_weighted_voting(session, votes)
            elif session.strategy == ConsensusStrategy.UNANIMITY:
                return await self._analyze_unanimity(session, votes)
            elif session.strategy == ConsensusStrategy.SUPERMAJORITY:
                return await self._analyze_supermajority(session, votes)
            
            return {
                "reached": False,
                "level": 0.0,
                "decision": None,
                "analysis": "Unknown consensus strategy"
            }
            
        except Exception as e:
            logger.error(f"Consensus analysis error: {e}")
            return {
                "reached": False,
                "level": 0.0,
                "decision": None,
                "analysis": f"Analysis error: {str(e)}"
            }
    
    async def _analyze_simple_majority(self, session: ConsensusSession, 
                                     votes: List[Vote]) -> Dict[str, Any]:
        """단순 다수결 분석"""
        vote_counts = {"for": 0, "against": 0, "abstain": 0}
        
        for vote in votes:
            vote_counts[vote.vote_type.value] += 1
        
        total_votes = len(votes)
        for_percentage = vote_counts["for"] / total_votes if total_votes > 0 else 0
        
        consensus_reached = for_percentage >= session.threshold
        
        return {
            "reached": consensus_reached,
            "level": for_percentage,
            "decision": "approved" if consensus_reached else "rejected",
            "analysis": {
                "vote_counts": vote_counts,
                "for_percentage": for_percentage,
                "threshold": session.threshold
            }
        }
    
    async def _analyze_weighted_voting(self, session: ConsensusSession, 
                                     votes: List[Vote]) -> Dict[str, Any]:
        """가중 투표 분석"""
        weighted_counts = {"for": 0.0, "against": 0.0, "abstain": 0.0}
        total_weight = 0.0
        
        for vote in votes:
            weighted_counts[vote.vote_type.value] += vote.weight
            total_weight += vote.weight
        
        for_percentage = weighted_counts["for"] / total_weight if total_weight > 0 else 0
        consensus_reached = for_percentage >= session.threshold
        
        return {
            "reached": consensus_reached,
            "level": for_percentage,
            "decision": "approved" if consensus_reached else "rejected",
            "analysis": {
                "weighted_counts": weighted_counts,
                "for_percentage": for_percentage,
                "total_weight": total_weight,
                "threshold": session.threshold
            }
        }
    
    async def _analyze_unanimity(self, session: ConsensusSession, 
                               votes: List[Vote]) -> Dict[str, Any]:
        """만장일치 분석"""
        for_votes = [v for v in votes if v.vote_type == VoteType.FOR]
        against_votes = [v for v in votes if v.vote_type == VoteType.AGAINST]
        
        consensus_reached = len(against_votes) == 0 and len(for_votes) > 0
        consensus_level = 1.0 if consensus_reached else 0.0
        
        return {
            "reached": consensus_reached,
            "level": consensus_level,
            "decision": "approved" if consensus_reached else "rejected",
            "analysis": {
                "for_votes": len(for_votes),
                "against_votes": len(against_votes),
                "abstain_votes": len(votes) - len(for_votes) - len(against_votes),
                "unanimity_required": True
            }
        }
    
    async def _analyze_supermajority(self, session: ConsensusSession, 
                                   votes: List[Vote]) -> Dict[str, Any]:
        """절대다수 분석"""
        return await self._analyze_simple_majority(session, votes)
    
    async def _provide_round_feedback(self, session: ConsensusSession, 
                                    round_data: ConsensusRound,
                                    consensus_result: Dict[str, Any]) -> None:
        """라운드 피드백 제공"""
        try:
            feedback = {
                "round_number": round_data.round_number,
                "consensus_level": consensus_result["level"],
                "threshold": session.threshold,
                "gap": session.threshold - consensus_result["level"],
                "suggestions": []
            }
            
            # 개선 제안 생성
            if consensus_result["level"] < session.threshold:
                gap = session.threshold - consensus_result["level"]
                if gap > 0.3:
                    feedback["suggestions"].append("Consider revising the proposal significantly")
                elif gap > 0.1:
                    feedback["suggestions"].append("Minor adjustments to the proposal may help")
                else:
                    feedback["suggestions"].append("Very close to consensus, small refinements needed")
            
            logger.info(f"Round {round_data.round_number} feedback: {feedback}")
            
        except Exception as e:
            logger.error(f"Error providing round feedback: {e}")
    
    async def _generate_session_summary(self, session: ConsensusSession) -> Dict[str, Any]:
        """세션 요약 생성"""
        try:
            total_votes = sum(len(round_data.votes) for round_data in session.rounds)
            final_consensus_level = session.rounds[-1].consensus_level if session.rounds else 0.0
            
            summary = {
                "session_id": session.session_id,
                "topic": session.topic,
                "status": session.status,
                "strategy": session.strategy.value,
                "threshold": session.threshold,
                "rounds_completed": len(session.rounds),
                "max_rounds": session.max_rounds,
                "total_participants": len(session.participants),
                "total_votes": total_votes,
                "final_consensus_level": final_consensus_level,
                "consensus_reached": session.status == "completed",
                "duration": self._calculate_session_duration(session)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating session summary: {e}")
            return {"error": str(e)}
    
    def _calculate_session_duration(self, session: ConsensusSession) -> Optional[float]:
        """세션 지속 시간 계산"""
        try:
            if not session.rounds:
                return None
            
            start_time = datetime.fromisoformat(session.rounds[0].start_time)
            end_time = datetime.fromisoformat(session.rounds[-1].end_time) if session.rounds[-1].end_time else datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            return duration
            
        except Exception as e:
            logger.error(f"Error calculating session duration: {e}")
            return None
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 상태 조회"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "status": session.status,
            "current_round": session.current_round,
            "max_rounds": session.max_rounds,
            "consensus_level": session.rounds[-1].consensus_level if session.rounds else 0.0,
            "threshold": session.threshold,
            "participants": len(session.participants)
        }
    
    async def intervene_session(self, session_id: str, action: str, 
                              parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """세션 개입"""
        session = self.active_sessions.get(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}
        
        try:
            if action == "extend_rounds":
                additional_rounds = parameters.get("additional_rounds", 1)
                session.max_rounds += additional_rounds
                return {"success": True, "message": f"Extended by {additional_rounds} rounds"}
            
            elif action == "adjust_threshold":
                new_threshold = parameters.get("threshold")
                if new_threshold and 0.0 <= new_threshold <= 1.0:
                    session.threshold = new_threshold
                    return {"success": True, "message": f"Threshold adjusted to {new_threshold}"}
                else:
                    return {"success": False, "error": "Invalid threshold value"}
            
            elif action == "end_session":
                session.status = "terminated"
                return {"success": True, "message": "Session terminated"}
            
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
                
        except Exception as e:
            logger.error(f"Session intervention error: {e}")
            return {"success": False, "error": str(e)}