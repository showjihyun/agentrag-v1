"""
Insights Service

Provides analytics and insights for workflows, agents, and executions.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from backend.db.models.flows import (
    Chatflow, Agentflow, FlowExecution, FlowTemplate
)

logger = logging.getLogger(__name__)


class InsightsService:
    """Service for generating analytics and insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_insights(
        self,
        user_id: int,
        time_range: Optional[int] = 30  # days
    ) -> Dict[str, Any]:
        """
        Get comprehensive insights for a user
        
        Args:
            user_id: User ID
            time_range: Number of days to analyze
            
        Returns:
            Dictionary with insights
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=time_range)
            
            # Get workflow statistics
            workflow_stats = await self._get_workflow_stats(user_id, cutoff_date)
            
            # Get execution statistics
            execution_stats = await self._get_execution_stats(user_id, cutoff_date)
            
            # Get performance metrics
            performance = await self._get_performance_metrics(user_id, cutoff_date)
            
            # Get usage patterns
            patterns = await self._get_usage_patterns(user_id, cutoff_date)
            
            # Get recommendations
            recommendations = await self._generate_recommendations(
                user_id, workflow_stats, execution_stats, performance
            )
            
            return {
                "user_id": user_id,
                "time_range_days": time_range,
                "generated_at": datetime.utcnow().isoformat(),
                "workflows": workflow_stats,
                "executions": execution_stats,
                "performance": performance,
                "patterns": patterns,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to generate user insights: {e}", exc_info=True)
            raise
    
    async def _get_workflow_stats(
        self,
        user_id: int,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Get workflow statistics"""
        
        # Count chatflows
        chatflow_count = self.db.query(func.count(Chatflow.id)).filter(
            Chatflow.user_id == user_id,
            Chatflow.created_at >= cutoff_date
        ).scalar() or 0
        
        # Count agentflows
        agentflow_count = self.db.query(func.count(Agentflow.id)).filter(
            Agentflow.user_id == user_id,
            Agentflow.created_at >= cutoff_date
        ).scalar() or 0
        
        # Get most used workflows
        most_used = self.db.query(
            FlowExecution.agentflow_id,
            FlowExecution.chatflow_id,
            FlowExecution.flow_type,
            func.count(FlowExecution.id).label('execution_count')
        ).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.started_at >= cutoff_date
        ).group_by(
            FlowExecution.agentflow_id,
            FlowExecution.chatflow_id,
            FlowExecution.flow_type
        ).order_by(
            func.count(FlowExecution.id).desc()
        ).limit(5).all()
        
        return {
            "total_chatflows": chatflow_count,
            "total_agentflows": agentflow_count,
            "total_workflows": chatflow_count + agentflow_count,
            "most_used": [
                {
                    "flow_id": str(agentflow_id or chatflow_id),
                    "flow_type": flow_type,
                    "execution_count": count
                }
                for agentflow_id, chatflow_id, flow_type, count in most_used
            ]
        }
    
    async def _get_execution_stats(
        self,
        user_id: int,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Get execution statistics"""
        
        # Total executions
        total = self.db.query(func.count(FlowExecution.id)).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.started_at >= cutoff_date
        ).scalar() or 0
        
        # Success/failure counts
        success_count = self.db.query(func.count(FlowExecution.id)).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.status == 'completed',
            FlowExecution.started_at >= cutoff_date
        ).scalar() or 0
        
        failed_count = self.db.query(func.count(FlowExecution.id)).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.status == 'failed',
            FlowExecution.started_at >= cutoff_date
        ).scalar() or 0
        
        # Calculate success rate
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        # Get executions by day
        daily_executions = self.db.query(
            func.date(FlowExecution.started_at).label('date'),
            func.count(FlowExecution.id).label('count')
        ).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.started_at >= cutoff_date
        ).group_by(
            func.date(FlowExecution.started_at)
        ).order_by(
            func.date(FlowExecution.started_at)
        ).all()
        
        return {
            "total_executions": total,
            "successful": success_count,
            "failed": failed_count,
            "success_rate": round(success_rate, 2),
            "daily_executions": [
                {
                    "date": date.isoformat(),
                    "count": count
                }
                for date, count in daily_executions
            ]
        }
    
    async def _get_performance_metrics(
        self,
        user_id: int,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Get performance metrics"""
        
        # Get execution durations
        executions = self.db.query(
            FlowExecution.duration_ms,
            FlowExecution.flow_type
        ).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.status == 'completed',
            FlowExecution.duration_ms.isnot(None),
            FlowExecution.started_at >= cutoff_date
        ).all()
        
        if not executions:
            return {
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "by_type": {}
            }
        
        durations = [e.duration_ms for e in executions]
        
        # Calculate by type
        by_type = defaultdict(list)
        for execution in executions:
            by_type[execution.flow_type].append(execution.duration_ms)
        
        type_stats = {}
        for flow_type, type_durations in by_type.items():
            type_stats[flow_type] = {
                "avg_duration_ms": round(sum(type_durations) / len(type_durations), 2),
                "min_duration_ms": min(type_durations),
                "max_duration_ms": max(type_durations),
                "count": len(type_durations)
            }
        
        return {
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "min_duration_ms": min(durations),
            "max_duration_ms": max(durations),
            "by_type": type_stats
        }
    
    async def _get_usage_patterns(
        self,
        user_id: int,
        cutoff_date: datetime
    ) -> Dict[str, Any]:
        """Analyze usage patterns"""
        
        # Get executions with timestamps
        executions = self.db.query(
            FlowExecution.started_at,
            FlowExecution.flow_type
        ).filter(
            FlowExecution.user_id == user_id,
            FlowExecution.started_at >= cutoff_date
        ).all()
        
        if not executions:
            return {
                "peak_hours": [],
                "peak_days": [],
                "most_active_day": None
            }
        
        # Analyze by hour
        hour_counts = Counter(e.started_at.hour for e in executions)
        peak_hours = [
            {"hour": hour, "count": count}
            for hour, count in hour_counts.most_common(3)
        ]
        
        # Analyze by day of week
        day_counts = Counter(e.started_at.strftime('%A') for e in executions)
        peak_days = [
            {"day": day, "count": count}
            for day, count in day_counts.most_common(3)
        ]
        
        # Most active day
        most_active = day_counts.most_common(1)[0] if day_counts else None
        
        return {
            "peak_hours": peak_hours,
            "peak_days": peak_days,
            "most_active_day": most_active[0] if most_active else None
        }
    
    async def _generate_recommendations(
        self,
        user_id: int,
        workflow_stats: Dict,
        execution_stats: Dict,
        performance: Dict
    ) -> List[Dict[str, str]]:
        """Generate personalized recommendations"""
        
        recommendations = []
        
        # Check workflow count
        total_workflows = workflow_stats["total_workflows"]
        if total_workflows == 0:
            recommendations.append({
                "type": "getting_started",
                "priority": "high",
                "message": "Create your first workflow to get started",
                "action": "Visit the marketplace for templates"
            })
        elif total_workflows < 3:
            recommendations.append({
                "type": "exploration",
                "priority": "medium",
                "message": "Explore more workflow types",
                "action": "Try creating both chatflows and agentflows"
            })
        
        # Check success rate
        success_rate = execution_stats["success_rate"]
        if success_rate < 80 and execution_stats["total_executions"] > 10:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "message": f"Success rate is {success_rate}%, consider adding error handling",
                "action": "Review failed executions and add try-catch blocks"
            })
        
        # Check performance
        avg_duration = performance["avg_duration_ms"]
        if avg_duration > 5000:  # 5 seconds
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "message": "Average execution time is high",
                "action": "Consider optimizing workflows or adding caching"
            })
        
        # Check usage patterns
        if execution_stats["total_executions"] == 0:
            recommendations.append({
                "type": "activation",
                "priority": "high",
                "message": "No executions yet",
                "action": "Test your workflows to ensure they work correctly"
            })
        
        return recommendations
    
    async def get_workflow_insights(
        self,
        flow_id: int,
        flow_type: str,
        user_id: int
    ) -> Dict[str, Any]:
        """Get insights for a specific workflow"""
        
        try:
            # Get execution history
            filter_condition = and_(
                FlowExecution.user_id == user_id,
                FlowExecution.flow_type == flow_type
            )
            
            # Add flow_id filter based on type
            if flow_type == "chatflow":
                filter_condition = and_(filter_condition, FlowExecution.chatflow_id == flow_id)
            else:
                filter_condition = and_(filter_condition, FlowExecution.agentflow_id == flow_id)
            
            executions = self.db.query(FlowExecution).filter(
                filter_condition
            ).order_by(FlowExecution.started_at.desc()).limit(100).all()
            
            if not executions:
                return {
                    "flow_id": flow_id,
                    "flow_type": flow_type,
                    "message": "No execution history available"
                }
            
            # Calculate statistics
            total = len(executions)
            successful = sum(1 for e in executions if e.status == 'completed')
            failed = sum(1 for e in executions if e.status == 'failed')
            
            durations = [e.duration_ms for e in executions if e.duration_ms]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Identify common errors
            error_messages = [
                e.error_message for e in executions
                if e.status == 'failed' and e.error_message
            ]
            common_errors = Counter(error_messages).most_common(3)
            
            return {
                "flow_id": flow_id,
                "flow_type": flow_type,
                "total_executions": total,
                "success_rate": round(successful / total * 100, 2) if total > 0 else 0,
                "avg_duration_ms": round(avg_duration, 2),
                "common_errors": [
                    {"message": msg, "count": count}
                    for msg, count in common_errors
                ],
                "recent_executions": [
                    {
                        "id": str(e.id),
                        "status": e.status,
                        "duration": e.duration_ms,
                        "created_at": e.started_at.isoformat()
                    }
                    for e in executions[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow insights: {e}", exc_info=True)
            raise
    
    async def get_system_insights(self) -> Dict[str, Any]:
        """Get system-wide insights (admin only)"""
        
        try:
            # Total users with workflows
            total_users = self.db.query(
                func.count(func.distinct(Chatflow.user_id))
            ).scalar() or 0
            
            # Total workflows
            total_chatflows = self.db.query(func.count(Chatflow.id)).scalar() or 0
            total_agentflows = self.db.query(func.count(Agentflow.id)).scalar() or 0
            
            # Total executions
            total_executions = self.db.query(func.count(FlowExecution.id)).scalar() or 0
            
            # Most popular templates
            popular_templates = self.db.query(
                FlowTemplate.name,
                func.count(FlowTemplate.id).label('usage_count')
            ).group_by(
                FlowTemplate.name
            ).order_by(
                func.count(FlowTemplate.id).desc()
            ).limit(5).all()
            
            return {
                "total_users": total_users,
                "total_workflows": total_chatflows + total_agentflows,
                "total_chatflows": total_chatflows,
                "total_agentflows": total_agentflows,
                "total_executions": total_executions,
                "popular_templates": [
                    {"name": name, "usage_count": count}
                    for name, count in popular_templates
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get system insights: {e}", exc_info=True)
            raise
