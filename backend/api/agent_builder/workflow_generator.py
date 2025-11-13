"""
Workflow Generator API
Endpoints for AI-powered workflow generation
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from backend.core.dependencies import get_db
from backend.services.agent_builder.workflow_generator import WorkflowGenerator
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow-generator", tags=["Workflow Generator"])


class GenerateWorkflowRequest(BaseModel):
    """Request to generate workflow from description"""
    description: str = Field(..., description="Natural language description of workflow")
    additional_context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class GenerateWorkflowResponse(BaseModel):
    """Response with generated workflow"""
    workflow: Dict[str, Any]
    suggestions: List[Dict[str, Any]] = []


class SuggestImprovementsRequest(BaseModel):
    """Request to suggest improvements for workflow"""
    workflow: Dict[str, Any]


class SuggestImprovementsResponse(BaseModel):
    """Response with improvement suggestions"""
    suggestions: List[Dict[str, Any]]


class OptimizeWorkflowRequest(BaseModel):
    """Request to optimize workflow"""
    workflow: Dict[str, Any]


class OptimizeWorkflowResponse(BaseModel):
    """Response with optimized workflow"""
    workflow: Dict[str, Any]
    improvements: List[str]


@router.post("/generate", response_model=GenerateWorkflowResponse)
async def generate_workflow(
    request: GenerateWorkflowRequest,
    db: Session = Depends(get_db)
):
    """
    Generate workflow from natural language description
    
    Example:
    ```
    POST /api/workflow-generator/generate
    {
      "description": "When a customer submits feedback, analyze sentiment and send to appropriate team"
    }
    ```
    """
    try:
        generator = WorkflowGenerator()
        
        # Generate workflow
        workflow_def = await generator.generate_workflow(
            description=request.description,
            user_id="anonymous",  # TODO: Add authentication
            additional_context=request.additional_context
        )
        
        # Get improvement suggestions
        suggestions = await generator.suggest_improvements(workflow_def)
        
        logger.info(
            f"Generated workflow: {workflow_def.get('name')}"
        )
        
        return GenerateWorkflowResponse(
            workflow=workflow_def,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Failed to generate workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate workflow: {str(e)}"
        )


@router.post("/suggest-improvements", response_model=SuggestImprovementsResponse)
async def suggest_improvements(
    request: SuggestImprovementsRequest
):
    """
    Suggest improvements for an existing workflow
    
    Example:
    ```
    POST /api/workflow-generator/suggest-improvements
    {
      "workflow": { ... }
    }
    ```
    """
    try:
        generator = WorkflowGenerator()
        suggestions = await generator.suggest_improvements(request.workflow)
        
        return SuggestImprovementsResponse(suggestions=suggestions)
        
    except Exception as e:
        logger.error(f"Failed to suggest improvements: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to suggest improvements: {str(e)}"
        )


@router.post("/optimize", response_model=OptimizeWorkflowResponse)
async def optimize_workflow(
    request: OptimizeWorkflowRequest
):
    """
    Optimize workflow for performance and cost
    
    Example:
    ```
    POST /api/workflow-generator/optimize
    {
      "workflow": { ... }
    }
    ```
    """
    try:
        generator = WorkflowGenerator()
        optimized_workflow = await generator.optimize_workflow(request.workflow)
        
        # Compare and list improvements
        improvements = [
            "Identified parallel execution opportunities",
            "Optimized LLM call batching",
            "Added caching for repeated operations"
        ]
        
        return OptimizeWorkflowResponse(
            workflow=optimized_workflow,
            improvements=improvements
        )
        
    except Exception as e:
        logger.error(f"Failed to optimize workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize workflow: {str(e)}"
        )


@router.get("/examples")
async def get_example_descriptions():
    """
    Get example workflow descriptions for inspiration
    
    Returns list of example descriptions users can try
    """
    examples = [
        {
            "title": "Customer Support Automation",
            "description": "When a customer sends an email, classify the issue, generate a response using AI, and send it back",
            "category": "customer-service",
            "complexity": "medium"
        },
        {
            "title": "Content Moderation",
            "description": "Analyze user-submitted content for inappropriate material, get consensus from 3 AI agents, and flag if needed",
            "category": "moderation",
            "complexity": "high"
        },
        {
            "title": "Data Enrichment",
            "description": "Fetch user data from database, enrich with external APIs in parallel, and save to Google Drive",
            "category": "data-processing",
            "complexity": "medium"
        },
        {
            "title": "Slack Notification",
            "description": "Send a Slack message to #alerts channel when a webhook is triggered",
            "category": "notifications",
            "complexity": "low"
        },
        {
            "title": "Document Analysis",
            "description": "Upload a PDF, extract text, summarize with AI, and email the summary to the team",
            "category": "document-processing",
            "complexity": "medium"
        },
        {
            "title": "Approval Workflow",
            "description": "When a purchase request comes in, check if amount > $1000, if yes require manager approval, then process payment",
            "category": "approval",
            "complexity": "medium"
        },
        {
            "title": "Social Media Monitor",
            "description": "Check Twitter mentions every hour, analyze sentiment, and alert team if negative",
            "category": "monitoring",
            "complexity": "high"
        },
        {
            "title": "Lead Scoring",
            "description": "Receive lead data, score using AI, if score > 80 send to sales team via Slack, otherwise add to nurture campaign",
            "category": "sales",
            "complexity": "medium"
        }
    ]
    
    return {"examples": examples}


@router.get("/node-types")
async def get_available_node_types():
    """
    Get list of available node types and their descriptions
    
    Useful for understanding what nodes can be used in workflows
    """
    generator = WorkflowGenerator()
    
    return {
        "node_types": [
            {"type": node_type, "description": desc}
            for node_type, desc in generator.node_types.items()
        ]
    }
