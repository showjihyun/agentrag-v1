"""
Feedback Learning System for Agent Builder.

Learns from user feedback to improve agent performance over time.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from collections import defaultdict
import json

from sqlalchemy.orm import Session
from sqlalchemy import func

logger = logging.getLogger(__name__)


class FeedbackType:
    """Types of user feedback."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AgentLearningSystem:
    """
    Learns from user feedback to improve agents.
    
    Features:
    - Feedback collection and analysis
    - Prompt optimization suggestions
    - Performance tracking
    - A/B testing support
    """
    
    def __init__(self, db: Session):
        """
        Initialize learning system.
        
        Args:
            db: Database session
        """
        self.db = db
        self.feedback_cache = defaultdict(list)
        
        logger.info("AgentLearningSystem initialized")
    
    async def record_feedback(
        self,
        agent_id: str,
        execution_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record user feedback for an agent execution.
        
        Args:
            agent_id: Agent ID
            execution_id: Execution ID
            feedback_type: Type of feedback
            rating: Optional rating (1-5)
            comment: Optional comment
            metadata: Optional metadata
            
        Returns:
            Feedback record
        """
        feedback = {
            "agent_id": agent_id,
            "execution_id": execution_id,
            "feedback_type": feedback_type,
            "rating": rating,
            "comment": comment,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache feedback
        self.feedback_cache[agent_id].append(feedback)
        
        logger.info(f"Recorded {feedback_type} feedback for agent {agent_id}")
        
        # Analyze if we have enough feedback
        if len(self.feedback_cache[agent_id]) >= 10:
            await self._analyze_feedback(agent_id)
        
        return feedback
    
    async def _analyze_feedback(self, agent_id: str) -> Dict[str, Any]:
        """
        Analyze feedback for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Analysis results
        """
        feedbacks = self.feedback_cache[agent_id]
        
        if not feedbacks:
            return {}
        
        # Calculate metrics
        total = len(feedbacks)
        positive = sum(1 for f in feedbacks if f["feedback_type"] == FeedbackType.POSITIVE)
        negative = sum(1 for f in feedbacks if f["feedback_type"] == FeedbackType.NEGATIVE)
        
        ratings = [f["rating"] for f in feedbacks if f["rating"] is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        # Extract common issues from negative feedback
        issues = []
        for f in feedbacks:
            if f["feedback_type"] == FeedbackType.NEGATIVE and f["comment"]:
                issues.append(f["comment"])
        
        analysis = {
            "agent_id": agent_id,
            "total_feedback": total,
            "positive_count": positive,
            "negative_count": negative,
            "satisfaction_rate": positive / total if total > 0 else 0,
            "average_rating": avg_rating,
            "common_issues": self._extract_common_issues(issues),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Analyzed feedback for agent {agent_id}: {analysis['satisfaction_rate']:.2%} satisfaction")
        
        # Generate improvement suggestions
        if analysis["satisfaction_rate"] < 0.7:
            suggestions = await self._generate_improvement_suggestions(agent_id, analysis)
            analysis["suggestions"] = suggestions
        
        return analysis
    
    def _extract_common_issues(self, issues: List[str]) -> List[str]:
        """Extract common issues from feedback comments."""
        # Simplified - in production, use NLP
        issue_keywords = defaultdict(int)
        
        for issue in issues:
            words = issue.lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    issue_keywords[word] += 1
        
        # Get top issues
        sorted_issues = sorted(
            issue_keywords.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [word for word, count in sorted_issues[:5]]
    
    async def _generate_improvement_suggestions(
        self,
        agent_id: str,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions based on feedback analysis.
        
        Args:
            agent_id: Agent ID
            analysis: Feedback analysis
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Low satisfaction rate
        if analysis["satisfaction_rate"] < 0.5:
            suggestions.append({
                "type": "prompt_optimization",
                "priority": "high",
                "description": "Consider revising the agent's prompt template",
                "reason": f"Low satisfaction rate: {analysis['satisfaction_rate']:.1%}"
            })
        
        # Low average rating
        if analysis["average_rating"] and analysis["average_rating"] < 3.0:
            suggestions.append({
                "type": "tool_configuration",
                "priority": "high",
                "description": "Review tool selection and configuration",
                "reason": f"Low average rating: {analysis['average_rating']:.1f}/5"
            })
        
        # Common issues
        if analysis["common_issues"]:
            suggestions.append({
                "type": "issue_resolution",
                "priority": "medium",
                "description": f"Address common issues: {', '.join(analysis['common_issues'][:3])}",
                "reason": "Recurring feedback themes detected"
            })
        
        return suggestions
    
    async def get_agent_performance_trends(
        self,
        agent_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance trends for an agent.
        
        Args:
            agent_id: Agent ID
            days: Number of days to analyze
            
        Returns:
            Performance trends
        """
        feedbacks = self.feedback_cache.get(agent_id, [])
        
        if not feedbacks:
            return {
                "agent_id": agent_id,
                "no_data": True
            }
        
        # Group by date
        daily_stats = defaultdict(lambda: {"positive": 0, "negative": 0, "total": 0})
        
        for feedback in feedbacks:
            date = feedback["timestamp"][:10]  # YYYY-MM-DD
            daily_stats[date]["total"] += 1
            if feedback["feedback_type"] == FeedbackType.POSITIVE:
                daily_stats[date]["positive"] += 1
            elif feedback["feedback_type"] == FeedbackType.NEGATIVE:
                daily_stats[date]["negative"] += 1
        
        # Calculate trends
        dates = sorted(daily_stats.keys())
        trend_data = []
        
        for date in dates:
            stats = daily_stats[date]
            satisfaction = stats["positive"] / stats["total"] if stats["total"] > 0 else 0
            trend_data.append({
                "date": date,
                "satisfaction_rate": satisfaction,
                "total_feedback": stats["total"]
            })
        
        return {
            "agent_id": agent_id,
            "period_days": days,
            "trend_data": trend_data,
            "overall_satisfaction": sum(d["satisfaction_rate"] for d in trend_data) / len(trend_data) if trend_data else 0
        }
    
    async def compare_agent_versions(
        self,
        agent_id: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """
        Compare performance between two agent versions (A/B testing).
        
        Args:
            agent_id: Agent ID
            version_a: Version A identifier
            version_b: Version B identifier
            
        Returns:
            Comparison results
        """
        feedbacks = self.feedback_cache.get(agent_id, [])
        
        version_a_feedback = [
            f for f in feedbacks
            if f.get("metadata", {}).get("version") == version_a
        ]
        
        version_b_feedback = [
            f for f in feedbacks
            if f.get("metadata", {}).get("version") == version_b
        ]
        
        def calculate_metrics(feedback_list):
            if not feedback_list:
                return None
            
            total = len(feedback_list)
            positive = sum(1 for f in feedback_list if f["feedback_type"] == FeedbackType.POSITIVE)
            ratings = [f["rating"] for f in feedback_list if f["rating"] is not None]
            
            return {
                "total_feedback": total,
                "satisfaction_rate": positive / total if total > 0 else 0,
                "average_rating": sum(ratings) / len(ratings) if ratings else None
            }
        
        metrics_a = calculate_metrics(version_a_feedback)
        metrics_b = calculate_metrics(version_b_feedback)
        
        # Determine winner
        winner = None
        if metrics_a and metrics_b:
            if metrics_a["satisfaction_rate"] > metrics_b["satisfaction_rate"]:
                winner = "version_a"
            elif metrics_b["satisfaction_rate"] > metrics_a["satisfaction_rate"]:
                winner = "version_b"
        
        return {
            "agent_id": agent_id,
            "version_a": {
                "version": version_a,
                "metrics": metrics_a
            },
            "version_b": {
                "version": version_b,
                "metrics": metrics_b
            },
            "winner": winner,
            "confidence": "high" if metrics_a and metrics_b and abs(metrics_a["satisfaction_rate"] - metrics_b["satisfaction_rate"]) > 0.1 else "low"
        }
