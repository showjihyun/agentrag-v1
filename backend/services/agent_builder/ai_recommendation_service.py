"""AI-based recommendation service for agents and workflows."""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_

from backend.db.models.agent_builder import Agent, AgentExecution, ExecutionMetrics
from backend.db.models.flows import Agentflow, FlowExecution
from backend.db.models.user import User

logger = logging.getLogger(__name__)


class AIRecommendationService:
    """AI-powered recommendation service for agents and workflows."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_personalized_agent_recommendations(
        self, 
        user_id: str, 
        orchestration_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get personalized agent recommendations based on user behavior and preferences.
        
        Args:
            user_id: User ID
            orchestration_type: Optional orchestration type filter
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended agents with scores and reasons
        """
        try:
            # Get user's usage patterns
            user_patterns = self._analyze_user_patterns(user_id)
            
            # Get all available agents (excluding user's own agents)
            available_agents = self.db.query(Agent).filter(
                and_(
                    Agent.user_id != user_id,
                    Agent.is_public == True,
                    Agent.deleted_at.is_(None)
                )
            ).all()
            
            # Score and rank agents
            scored_agents = []
            for agent in available_agents:
                score = self._calculate_recommendation_score(
                    agent, user_patterns, orchestration_type
                )
                if score > 0.1:  # Minimum threshold
                    scored_agents.append({
                        'agent': agent,
                        'score': score,
                        'reasons': self._generate_recommendation_reasons(
                            agent, user_patterns, orchestration_type
                        )
                    })
            
            # Sort by score and limit results
            scored_agents.sort(key=lambda x: x['score'], reverse=True)
            return scored_agents[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get personalized recommendations: {e}")
            return []
    
    def get_similar_agents(
        self, 
        agent_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find agents similar to the given agent.
        
        Args:
            agent_id: Reference agent ID
            limit: Maximum number of similar agents
            
        Returns:
            List of similar agents with similarity scores
        """
        try:
            # Get reference agent
            reference_agent = self.db.query(Agent).filter(
                Agent.id == agent_id
            ).first()
            
            if not reference_agent:
                return []
            
            # Get other agents
            other_agents = self.db.query(Agent).filter(
                and_(
                    Agent.id != agent_id,
                    Agent.is_public == True,
                    Agent.deleted_at.is_(None)
                )
            ).all()
            
            # Calculate similarity scores
            similar_agents = []
            for agent in other_agents:
                similarity = self._calculate_agent_similarity(reference_agent, agent)
                if similarity > 0.3:  # Minimum similarity threshold
                    similar_agents.append({
                        'agent': agent,
                        'similarity': similarity,
                        'common_features': self._get_common_features(reference_agent, agent)
                    })
            
            # Sort by similarity and limit results
            similar_agents.sort(key=lambda x: x['similarity'], reverse=True)
            return similar_agents[:limit]
            
        except Exception as e:
            logger.error(f"Failed to find similar agents: {e}")
            return []
    
    def get_trending_agents(
        self, 
        time_period: str = '7d',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get trending agents based on usage and performance metrics.
        
        Args:
            time_period: Time period for trend analysis ('24h', '7d', '30d')
            limit: Maximum number of trending agents
            
        Returns:
            List of trending agents with trend metrics
        """
        try:
            # Calculate time threshold
            if time_period == '24h':
                threshold = datetime.utcnow() - timedelta(hours=24)
            elif time_period == '7d':
                threshold = datetime.utcnow() - timedelta(days=7)
            elif time_period == '30d':
                threshold = datetime.utcnow() - timedelta(days=30)
            else:
                threshold = datetime.utcnow() - timedelta(days=7)
            
            # Get agents with recent activity
            trending_query = self.db.query(
                Agent,
                func.count(AgentExecution.id).label('execution_count'),
                func.avg(
                    func.case(
                        [(AgentExecution.status == 'completed', 1)],
                        else_=0
                    )
                ).label('success_rate'),
                func.count(func.distinct(AgentExecution.user_id)).label('unique_users')
            ).join(
                AgentExecution, Agent.id == AgentExecution.agent_id
            ).filter(
                and_(
                    Agent.is_public == True,
                    Agent.deleted_at.is_(None),
                    AgentExecution.started_at >= threshold
                )
            ).group_by(Agent.id).having(
                func.count(AgentExecution.id) > 0
            )
            
            trending_agents = []
            for agent, exec_count, success_rate, unique_users in trending_query.all():
                trend_score = self._calculate_trend_score(
                    exec_count, success_rate or 0, unique_users
                )
                trending_agents.append({
                    'agent': agent,
                    'trend_score': trend_score,
                    'execution_count': exec_count,
                    'success_rate': success_rate or 0,
                    'unique_users': unique_users,
                    'trend_period': time_period
                })
            
            # Sort by trend score and limit results
            trending_agents.sort(key=lambda x: x['trend_score'], reverse=True)
            return trending_agents[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get trending agents: {e}")
            return []
    
    def get_workflow_recommendations(
        self, 
        user_id: str, 
        agent_ids: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recommend workflows based on selected agents.
        
        Args:
            user_id: User ID
            agent_ids: List of selected agent IDs
            limit: Maximum number of workflow recommendations
            
        Returns:
            List of recommended workflows
        """
        try:
            # Get user's workflow patterns
            user_workflows = self.db.query(Agentflow).filter(
                Agentflow.user_id == user_id
            ).all()
            
            # Analyze agent combinations
            recommendations = []
            
            # Mock workflow recommendations based on agent types
            for i, agent_id in enumerate(agent_ids[:limit]):
                agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
                if agent:
                    recommendations.append({
                        'workflow_type': self._suggest_workflow_type(agent),
                        'orchestration_type': self._suggest_orchestration_for_agent(agent),
                        'confidence': 0.8 - (i * 0.1),
                        'description': f"{agent.name}에 최적화된 워크플로우",
                        'estimated_performance': {
                            'execution_time': '2-5초',
                            'success_rate': '85-95%',
                            'complexity': 'medium'
                        }
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get workflow recommendations: {e}")
            return []
    
    def _analyze_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's usage patterns and preferences."""
        try:
            # Get user's agents
            user_agents = self.db.query(Agent).filter(
                Agent.user_id == user_id
            ).all()
            
            # Get user's executions
            user_executions = self.db.query(AgentExecution).filter(
                AgentExecution.user_id == user_id
            ).all()
            
            # Analyze patterns
            patterns = {
                'preferred_llm_providers': {},
                'preferred_agent_types': {},
                'usage_frequency': len(user_executions),
                'success_rate': 0,
                'avg_execution_time': 0,
                'preferred_tools': set(),
                'active_hours': [],
                'complexity_preference': 'medium'
            }
            
            # Analyze LLM provider preferences
            for agent in user_agents:
                provider = agent.llm_provider
                patterns['preferred_llm_providers'][provider] = \
                    patterns['preferred_llm_providers'].get(provider, 0) + 1
            
            # Analyze agent type preferences
            for agent in user_agents:
                agent_type = agent.agent_type
                patterns['preferred_agent_types'][agent_type] = \
                    patterns['preferred_agent_types'].get(agent_type, 0) + 1
            
            # Calculate success rate
            if user_executions:
                successful = sum(1 for ex in user_executions if ex.status == 'completed')
                patterns['success_rate'] = successful / len(user_executions)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Failed to analyze user patterns: {e}")
            return {}
    
    def _calculate_recommendation_score(
        self, 
        agent: Agent, 
        user_patterns: Dict[str, Any],
        orchestration_type: Optional[str] = None
    ) -> float:
        """Calculate recommendation score for an agent."""
        score = 0.0
        
        # Base popularity score
        score += 0.2
        
        # LLM provider preference match
        preferred_providers = user_patterns.get('preferred_llm_providers', {})
        if agent.llm_provider in preferred_providers:
            score += 0.3 * (preferred_providers[agent.llm_provider] / 
                           sum(preferred_providers.values()))
        
        # Agent type preference match
        preferred_types = user_patterns.get('preferred_agent_types', {})
        if agent.agent_type in preferred_types:
            score += 0.2 * (preferred_types[agent.agent_type] / 
                           sum(preferred_types.values()))
        
        # Orchestration compatibility
        if orchestration_type:
            # Mock orchestration compatibility check
            compatible_types = {
                'sequential': ['custom', 'template_based'],
                'parallel': ['custom'],
                'hierarchical': ['template_based'],
            }
            if agent.agent_type in compatible_types.get(orchestration_type, []):
                score += 0.3
        
        return min(score, 1.0)
    
    def _calculate_agent_similarity(self, agent1: Agent, agent2: Agent) -> float:
        """Calculate similarity score between two agents."""
        similarity = 0.0
        
        # LLM provider similarity
        if agent1.llm_provider == agent2.llm_provider:
            similarity += 0.3
        
        # Agent type similarity
        if agent1.agent_type == agent2.agent_type:
            similarity += 0.2
        
        # Configuration similarity (mock)
        if agent1.configuration and agent2.configuration:
            # Simple key overlap check
            keys1 = set(agent1.configuration.keys())
            keys2 = set(agent2.configuration.keys())
            if keys1 and keys2:
                overlap = len(keys1.intersection(keys2)) / len(keys1.union(keys2))
                similarity += 0.3 * overlap
        
        # Description similarity (mock - could use NLP)
        if agent1.description and agent2.description:
            # Simple word overlap
            words1 = set(agent1.description.lower().split())
            words2 = set(agent2.description.lower().split())
            if words1 and words2:
                overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                similarity += 0.2 * overlap
        
        return min(similarity, 1.0)
    
    def _get_common_features(self, agent1: Agent, agent2: Agent) -> List[str]:
        """Get common features between two agents."""
        features = []
        
        if agent1.llm_provider == agent2.llm_provider:
            features.append(f"동일한 LLM 제공자 ({agent1.llm_provider})")
        
        if agent1.agent_type == agent2.agent_type:
            features.append(f"동일한 에이전트 유형 ({agent1.agent_type})")
        
        # Mock tool similarity
        features.append("유사한 도구 구성")
        
        return features
    
    def _calculate_trend_score(
        self, 
        execution_count: int, 
        success_rate: float, 
        unique_users: int
    ) -> float:
        """Calculate trend score based on metrics."""
        # Normalize metrics
        exec_score = min(execution_count / 100, 1.0)  # Normalize to 100 executions
        success_score = success_rate
        user_score = min(unique_users / 10, 1.0)  # Normalize to 10 users
        
        # Weighted combination
        trend_score = (exec_score * 0.4) + (success_score * 0.3) + (user_score * 0.3)
        
        return trend_score
    
    def _generate_recommendation_reasons(
        self, 
        agent: Agent, 
        user_patterns: Dict[str, Any],
        orchestration_type: Optional[str] = None
    ) -> List[str]:
        """Generate human-readable reasons for recommendation."""
        reasons = []
        
        # LLM provider match
        preferred_providers = user_patterns.get('preferred_llm_providers', {})
        if agent.llm_provider in preferred_providers:
            reasons.append(f"선호하는 {agent.llm_provider} 제공자 사용")
        
        # Agent type match
        preferred_types = user_patterns.get('preferred_agent_types', {})
        if agent.agent_type in preferred_types:
            reasons.append(f"자주 사용하는 {agent.agent_type} 유형")
        
        # Orchestration compatibility
        if orchestration_type:
            reasons.append(f"{orchestration_type} 오케스트레이션에 최적화")
        
        # Performance
        reasons.append("높은 성공률과 안정성")
        
        # Popularity
        reasons.append("다른 사용자들이 자주 사용")
        
        return reasons[:3]  # Limit to top 3 reasons
    
    def _suggest_workflow_type(self, agent: Agent) -> str:
        """Suggest workflow type based on agent characteristics."""
        if 'analysis' in agent.name.lower() or 'data' in agent.name.lower():
            return 'data_processing'
        elif 'content' in agent.name.lower() or 'writer' in agent.name.lower():
            return 'content_generation'
        elif 'search' in agent.name.lower():
            return 'information_retrieval'
        else:
            return 'general_automation'
    
    def _suggest_orchestration_for_agent(self, agent: Agent) -> str:
        """Suggest orchestration type for an agent."""
        if 'manager' in agent.name.lower() or 'coordinator' in agent.name.lower():
            return 'hierarchical'
        elif 'parallel' in agent.name.lower() or 'concurrent' in agent.name.lower():
            return 'parallel'
        else:
            return 'sequential'