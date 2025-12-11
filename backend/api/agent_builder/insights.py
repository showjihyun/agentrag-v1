"""
Insights API

Endpoints for analytics and insights.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.services.agent_builder.insights_service import InsightsService
from backend.db.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/insights", tags=["Insights"])


class UserInsightsResponse(BaseModel):
    """User insights response"""
    user_id: int
    time_range_days: int
    generated_at: str
    workflows: dict
    executions: dict
    performance: dict
    patterns: dict
    recommendations: list


class WorkflowInsightsResponse(BaseModel):
    """Workflow-specific insights"""
    flow_id: int
    flow_type: str
    total_executions: int
    success_rate: float
    avg_duration_ms: float
    common_errors: list
    recent_executions: list


class SystemInsightsResponse(BaseModel):
    """System-wide insights"""
    total_users: int
    total_workflows: int
    total_chatflows: int
    total_agentflows: int
    total_executions: int
    popular_templates: list


@router.get(
    "/user",
    response_model=UserInsightsResponse,
    summary="Get User Insights",
    description="Get comprehensive analytics for the current user"
)
async def get_user_insights(
    time_range: int = Query(30, ge=1, le=365, description="Days to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive insights for the current user.
    
    Includes:
    - Workflow statistics (counts, most used)
    - Execution statistics (success rate, trends)
    - Performance metrics (duration, by type)
    - Usage patterns (peak hours, days)
    - Personalized recommendations
    
    Args:
        time_range: Number of days to analyze (1-365)
    """
    try:
        service = InsightsService(db)
        
        insights = await service.get_user_insights(
            user_id=current_user.id,
            time_range=time_range
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get user insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get insights: {str(e)}"
        )


@router.get(
    "/workflow/{flow_type}/{flow_id}",
    response_model=WorkflowInsightsResponse,
    summary="Get Workflow Insights",
    description="Get detailed analytics for a specific workflow"
)
async def get_workflow_insights(
    flow_type: str,
    flow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed insights for a specific workflow.
    
    Includes:
    - Execution history and trends
    - Success rate
    - Performance metrics
    - Common errors
    - Recent executions
    
    Args:
        flow_id: Workflow ID
        flow_type: Type of workflow (chatflow or agentflow)
    """
    try:
        service = InsightsService(db)
        
        insights = await service.get_workflow_insights(
            flow_id=flow_id,
            flow_type=flow_type,
            user_id=current_user.id
        )
        
        return insights
        
    except Exception as e:
        logger.error(f"Failed to get workflow insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow insights: {str(e)}"
        )


@router.get(
    "/system",
    response_model=SystemInsightsResponse,
    summary="Get System Insights",
    description="Get system-wide analytics (admin only)"
)
async def get_system_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get system-wide insights.
    
    Includes:
    - Total users, workflows, executions
    - Popular templates
    - System-wide trends
    
    Note: This endpoint requires admin privileges.
    """
    try:
        # Check if user is admin
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        service = InsightsService(db)
        
        insights = await service.get_system_insights()
        
        return insights
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get system insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system insights: {str(e)}"
        )


@router.get(
    "/recommendations",
    response_model=list,
    summary="Get Recommendations",
    description="Get personalized recommendations for improving workflows"
)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations based on usage patterns.
    
    Recommendations may include:
    - Getting started tips
    - Performance optimization suggestions
    - Reliability improvements
    - Feature exploration
    """
    try:
        service = InsightsService(db)
        
        # Get full insights
        insights = await service.get_user_insights(
            user_id=current_user.id,
            time_range=30
        )
        
        # Return just recommendations
        return insights.get("recommendations", [])
        
    except Exception as e:
        logger.error(f"Failed to get recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )


@router.get(
    "/export",
    summary="Export Insights",
    description="Export insights data in various formats"
)
async def export_insights(
    format: str = Query("json", regex="^(json|csv)$"),
    time_range: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export insights data for external analysis.
    
    Supports:
    - JSON format (default)
    - CSV format
    
    Args:
        format: Export format (json or csv)
        time_range: Days to include in export
    """
    try:
        service = InsightsService(db)
        
        insights = await service.get_user_insights(
            user_id=current_user.id,
            time_range=time_range
        )
        
        if format == "json":
            return insights
        elif format == "csv":
            # Convert to CSV format
            import csv
            from io import StringIO
            from fastapi.responses import StreamingResponse
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(["Metric", "Value"])
            
            # Write workflow stats
            writer.writerow(["Total Workflows", insights["workflows"]["total_workflows"]])
            writer.writerow(["Total Chatflows", insights["workflows"]["total_chatflows"]])
            writer.writerow(["Total Agentflows", insights["workflows"]["total_agentflows"]])
            
            # Write execution stats
            writer.writerow(["Total Executions", insights["executions"]["total_executions"]])
            writer.writerow(["Success Rate", insights["executions"]["success_rate"]])
            
            # Write performance
            writer.writerow(["Avg Duration (ms)", insights["performance"]["avg_duration_ms"]])
            
            output.seek(0)
            
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=insights_{current_user.id}.csv"
                }
            )
        
    except Exception as e:
        logger.error(f"Failed to export insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export insights: {str(e)}"
        )
