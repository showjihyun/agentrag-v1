"""
NLP Generator API

Endpoints for natural language workflow generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.services.agent_builder.nlp_generator import NLPWorkflowGenerator, WorkflowIntent
from backend.db.models.user import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/nlp", tags=["NLP Generator"])


class GenerateRequest(BaseModel):
    """Request to generate workflow from text"""
    description: str = Field(..., min_length=10, max_length=1000)
    workflow_type: Optional[str] = Field(None, description="Force specific type: chatflow or agentflow")
    context: Optional[dict] = Field(None, description="Additional context")


class GenerateResponse(BaseModel):
    """Generated workflow response"""
    workflow: WorkflowIntent
    suggestions: List[str] = Field(default_factory=list)


class ImprovementRequest(BaseModel):
    """Request workflow improvement suggestions"""
    workflow: dict
    execution_history: Optional[List[dict]] = None


class ExampleResponse(BaseModel):
    """Example prompts"""
    examples: List[dict]


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate Workflow from Text",
    description="Convert natural language description into executable workflow"
)
async def generate_workflow(
    request: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a workflow from natural language description.
    
    The system will:
    1. Parse the intent from the description
    2. Identify required nodes and connections
    3. Generate a complete workflow structure
    4. Provide confidence score and suggestions
    
    Example descriptions:
    - "Create a chatbot that answers questions about products"
    - "Build a workflow that fetches weather data and sends email alerts"
    - "Make an agent that summarizes documents and saves to database"
    """
    try:
        generator = NLPWorkflowGenerator()
        
        # Generate workflow
        workflow = await generator.generate_from_text(
            description=request.description,
            user_id=current_user.id,
            context=request.context
        )
        
        # Override type if specified
        if request.workflow_type:
            workflow.workflow_type = request.workflow_type
        
        # Get improvement suggestions
        suggestions = await generator.suggest_improvements(
            workflow=workflow.dict()
        )
        
        logger.info(
            f"Generated workflow for user {current_user.id}: "
            f"{workflow.name} (confidence: {workflow.confidence})"
        )
        
        return GenerateResponse(
            workflow=workflow,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Failed to generate workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workflow: {str(e)}"
        )


@router.post(
    "/improve",
    response_model=List[str],
    summary="Get Workflow Improvements",
    description="Analyze workflow and suggest improvements"
)
async def suggest_improvements(
    request: ImprovementRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Analyze an existing workflow and suggest improvements.
    
    Analyzes:
    - Error handling coverage
    - Performance optimization opportunities
    - Best practice violations
    - Execution history patterns
    """
    try:
        generator = NLPWorkflowGenerator()
        
        suggestions = await generator.suggest_improvements(
            workflow=request.workflow,
            execution_history=request.execution_history
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


@router.get(
    "/examples",
    response_model=ExampleResponse,
    summary="Get Example Prompts",
    description="Get example natural language prompts for workflow generation"
)
async def get_examples():
    """
    Get example prompts showing what kinds of workflows can be generated.
    
    Useful for:
    - Onboarding new users
    - Showing capabilities
    - Providing templates
    """
    try:
        generator = NLPWorkflowGenerator()
        examples = generator.generate_examples()
        
        return ExampleResponse(examples=examples)
        
    except Exception as e:
        logger.error(f"Failed to get examples: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get examples: {str(e)}"
        )


class RefineRequest(BaseModel):
    """Request model for workflow refinement"""
    workflow: dict = Field(..., description="Existing workflow to refine")
    refinement: str = Field(..., description="Refinement instructions")


@router.post(
    "/refine",
    response_model=GenerateResponse,
    summary="Refine Generated Workflow",
    description="Refine a generated workflow with additional instructions"
)
async def refine_workflow(
    request: RefineRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Refine an existing generated workflow with additional instructions.
    
    Example refinements:
    - "Add error handling"
    - "Make it faster"
    - "Add logging"
    - "Include email notifications"
    """
    try:
        generator = NLPWorkflowGenerator()
        
        # Create refinement context
        context = {
            "existing_workflow": request.workflow,
            "refinement_request": request.refinement
        }
        
        # Generate refined workflow
        refined = await generator.generate_from_text(
            description=f"Refine this workflow: {request.refinement}",
            user_id=current_user.id,
            context=context
        )
        
        suggestions = await generator.suggest_improvements(
            workflow=refined.dict()
        )
        
        return GenerateResponse(
            workflow=refined,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Failed to refine workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refine workflow: {str(e)}"
        )
