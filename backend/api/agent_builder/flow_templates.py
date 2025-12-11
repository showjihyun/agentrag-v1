"""
Flow Templates API

Provides endpoints for managing flow templates (Agentflow and Chatflow).
Templates are stored in the database and can be system-provided or user-created.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from backend.db.database import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.flows import FlowTemplate, Agentflow, Chatflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agent-builder/flow-templates", tags=["Flow Templates"])


# ============ Pydantic Models ============

class FlowTemplateResponse(BaseModel):
    """Flow template response model."""
    id: str
    name: str
    description: Optional[str]
    flow_type: str
    category: Optional[str]
    icon: Optional[str]
    tags: List[str]
    use_case_examples: List[str]
    requirements: List[str]
    is_system: bool
    is_published: bool
    usage_count: int
    rating: float
    rating_count: int
    author_id: Optional[str]
    author_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateFlowTemplateRequest(BaseModel):
    """Request to create a flow template."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    flow_type: str = Field(..., pattern="^(agentflow|chatflow)$")
    category: Optional[str] = None
    icon: Optional[str] = None
    configuration: dict
    tags: List[str] = []
    use_case_examples: List[str] = []
    requirements: List[str] = []


class CreateFromTemplateRequest(BaseModel):
    """Request to create a flow from a template."""
    name: str = Field(..., min_length=1, max_length=255)


# ============ Helper Functions ============

def template_to_response(template: FlowTemplate, author_name: str = None) -> dict:
    """Convert FlowTemplate to response dict."""
    return {
        "id": str(template.id),
        "name": template.name,
        "description": template.description,
        "flow_type": template.flow_type,
        "category": template.category,
        "icon": template.icon,
        "tags": template.tags or [],
        "use_case_examples": template.use_case_examples or [],
        "requirements": template.requirements or [],
        "is_system": template.is_system,
        "is_published": template.is_published,
        "usage_count": template.usage_count or 0,
        "rating": template.rating or 0.0,
        "rating_count": template.rating_count or 0,
        "author_id": str(template.author_id) if template.author_id else None,
        "author_name": author_name,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
    }


def ensure_default_templates(db: Session):
    """Ensure default system templates exist in the database."""
    default_templates = [
        {
            "name": "리서치 에이전트 팀",
            "description": "여러 에이전트가 협력하여 정보를 수집하고 분석합니다",
            "flow_type": "agentflow",
            "category": "research",
            "icon": "🔬",
            "tags": ["research", "multi-agent", "analysis"],
            "use_case_examples": ["시장 조사", "경쟁사 분석", "트렌드 리서치"],
            "requirements": ["web_search", "vector_search"],
            "configuration": {
                "orchestration_type": "hierarchical",
                "supervisor_config": {
                    "enabled": True,
                    "llm_provider": "ollama",
                    "llm_model": "llama3.1",
                    "max_iterations": 10,
                    "decision_strategy": "llm_based",
                },
                "graph_definition": {"nodes": [], "edges": []},
            },
        },
        {
            "name": "RAG 챗봇",
            "description": "문서 기반 질의응답 챗봇",
            "flow_type": "chatflow",
            "category": "knowledge",
            "icon": "📚",
            "tags": ["rag", "chatbot", "knowledge-base"],
            "use_case_examples": ["문서 Q&A", "지식 검색", "FAQ 봇"],
            "requirements": ["knowledgebase"],
            "configuration": {
                "chat_config": {
                    "llm_provider": "ollama",
                    "llm_model": "llama3.1",
                    "system_prompt": "You are a helpful assistant that answers questions based on the provided documents.",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "streaming": True,
                    "welcome_message": "안녕하세요! 문서에 대해 질문해 주세요.",
                },
                "memory_config": {"type": "buffer", "max_messages": 20},
                "rag_config": {
                    "enabled": True,
                    "knowledgebase_ids": [],
                    "retrieval_strategy": "hybrid",
                    "top_k": 5,
                    "score_threshold": 0.7,
                    "reranking_enabled": True,
                },
                "graph_definition": {"nodes": [], "edges": []},
            },
        },
        {
            "name": "고객 지원 챗봇",
            "description": "FAQ 및 티켓 생성 기능이 포함된 지원 봇",
            "flow_type": "chatflow",
            "category": "customer-service",
            "icon": "🎧",
            "tags": ["support", "faq", "tickets"],
            "use_case_examples": ["고객 문의 응대", "FAQ 자동 응답", "티켓 생성"],
            "requirements": [],
            "configuration": {
                "chat_config": {
                    "llm_provider": "ollama",
                    "llm_model": "llama3.1",
                    "system_prompt": "You are a customer support assistant. Help users with their questions and create support tickets when needed.",
                    "temperature": 0.5,
                    "max_tokens": 1024,
                    "streaming": True,
                    "welcome_message": "안녕하세요! 무엇을 도와드릴까요?",
                    "suggested_questions": ["주문 상태 확인", "반품 요청", "기술 지원"],
                },
                "memory_config": {"type": "buffer", "max_messages": 30},
                "rag_config": {
                    "enabled": True,
                    "knowledgebase_ids": [],
                    "retrieval_strategy": "similarity",
                    "top_k": 3,
                    "score_threshold": 0.8,
                    "reranking_enabled": False,
                },
                "graph_definition": {"nodes": [], "edges": []},
            },
        },
        {
            "name": "코드 리뷰 에이전트",
            "description": "코드 품질 분석 및 개선 제안을 제공하는 에이전트",
            "flow_type": "agentflow",
            "category": "development",
            "icon": "💻",
            "tags": ["code", "review", "development"],
            "use_case_examples": ["코드 리뷰", "버그 탐지", "리팩토링 제안"],
            "requirements": ["code_execution"],
            "configuration": {
                "orchestration_type": "sequential",
                "supervisor_config": {
                    "enabled": True,
                    "llm_provider": "ollama",
                    "llm_model": "llama3.1",
                    "max_iterations": 5,
                    "decision_strategy": "rule_based",
                },
                "graph_definition": {"nodes": [], "edges": []},
            },
        },
        {
            "name": "데이터 분석 에이전트",
            "description": "데이터를 분석하고 인사이트를 도출하는 에이전트",
            "flow_type": "agentflow",
            "category": "analytics",
            "icon": "📊",
            "tags": ["data", "analytics", "visualization"],
            "use_case_examples": ["데이터 분석", "리포트 생성", "트렌드 분석"],
            "requirements": ["database", "calculator"],
            "configuration": {
                "orchestration_type": "parallel",
                "supervisor_config": {
                    "enabled": True,
                    "llm_provider": "ollama",
                    "llm_model": "llama3.1",
                    "max_iterations": 8,
                    "decision_strategy": "llm_based",
                },
                "graph_definition": {"nodes": [], "edges": []},
            },
        },
    ]
    
    for template_data in default_templates:
        existing = db.query(FlowTemplate).filter(
            FlowTemplate.name == template_data["name"],
            FlowTemplate.is_system == True
        ).first()
        
        if not existing:
            template = FlowTemplate(
                name=template_data["name"],
                description=template_data["description"],
                flow_type=template_data["flow_type"],
                category=template_data["category"],
                icon=template_data["icon"],
                configuration=template_data["configuration"],
                tags=template_data["tags"],
                use_case_examples=template_data["use_case_examples"],
                requirements=template_data["requirements"],
                is_system=True,
                is_published=True,
            )
            db.add(template)
    
    db.commit()


# ============ Endpoints ============

@router.get("", response_model=List[FlowTemplateResponse])
async def list_templates(
    flow_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    include_user_templates: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List available flow templates."""
    try:
        # Ensure default templates exist
        ensure_default_templates(db)
        
        # Build query
        query = db.query(FlowTemplate).filter(FlowTemplate.is_published == True)
        
        if include_user_templates:
            query = query.filter(
                or_(
                    FlowTemplate.is_system == True,
                    FlowTemplate.author_id == current_user.id
                )
            )
        else:
            query = query.filter(FlowTemplate.is_system == True)
        
        if flow_type:
            query = query.filter(FlowTemplate.flow_type == flow_type)
        
        if category:
            query = query.filter(FlowTemplate.category == category)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    FlowTemplate.name.ilike(search_pattern),
                    FlowTemplate.description.ilike(search_pattern),
                )
            )
        
        # Order by usage count and system templates first
        query = query.order_by(
            FlowTemplate.is_system.desc(),
            FlowTemplate.usage_count.desc()
        )
        
        # Pagination
        templates = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # Get author names
        author_ids = [t.author_id for t in templates if t.author_id]
        authors = db.query(User).filter(User.id.in_(author_ids)).all() if author_ids else []
        author_map = {str(a.id): a.username or a.email for a in authors}
        
        return [
            FlowTemplateResponse(**template_to_response(
                t,
                author_map.get(str(t.author_id)) if t.author_id else "AgenticRAG Team"
            ))
            for t in templates
        ]
        
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}", response_model=FlowTemplateResponse)
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    template = db.query(FlowTemplate).filter(
        FlowTemplate.id == template_uuid,
        FlowTemplate.is_published == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    author_name = None
    if template.author_id:
        author = db.query(User).filter(User.id == template.author_id).first()
        author_name = author.username or author.email if author else None
    else:
        author_name = "AgenticRAG Team"
    
    return FlowTemplateResponse(**template_to_response(template, author_name))


@router.post("/{template_id}/create")
async def create_from_template(
    template_id: str,
    request: CreateFromTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new flow from a template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    template = db.query(FlowTemplate).filter(
        FlowTemplate.id == template_uuid,
        FlowTemplate.is_published == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        config = template.configuration or {}
        
        if template.flow_type == "agentflow":
            flow = Agentflow(
                user_id=current_user.id,
                name=request.name,
                description=template.description,
                orchestration_type=config.get("orchestration_type", "sequential"),
                supervisor_config=config.get("supervisor_config"),
                graph_definition=config.get("graph_definition", {"nodes": [], "edges": []}),
                tags=template.tags,
                category=template.category,
                is_public=False,
                is_active=True,
                version="1.0.0",
                execution_count=0,
            )
            db.add(flow)
            flow_type = "agentflow"
        else:
            flow = Chatflow(
                user_id=current_user.id,
                name=request.name,
                description=template.description,
                chat_config=config.get("chat_config", {}),
                memory_config=config.get("memory_config", {"type": "buffer", "max_messages": 20}),
                rag_config=config.get("rag_config", {"enabled": False}),
                graph_definition=config.get("graph_definition", {"nodes": [], "edges": []}),
                tags=template.tags,
                category=template.category,
                is_public=False,
                is_active=True,
                version="1.0.0",
                execution_count=0,
            )
            db.add(flow)
            flow_type = "chatflow"
        
        # Update template usage count
        template.usage_count = (template.usage_count or 0) + 1
        
        db.commit()
        db.refresh(flow)
        
        return {
            "success": True,
            "flow_id": str(flow.id),
            "flow_type": flow_type,
            "name": flow.name,
            "message": f"Created {flow_type} from template",
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=FlowTemplateResponse)
async def create_template(
    request: CreateFlowTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user template."""
    try:
        template = FlowTemplate(
            author_id=current_user.id,
            name=request.name,
            description=request.description,
            flow_type=request.flow_type,
            category=request.category,
            icon=request.icon,
            configuration=request.configuration,
            tags=request.tags,
            use_case_examples=request.use_case_examples,
            requirements=request.requirements,
            is_system=False,
            is_published=True,
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return FlowTemplateResponse(**template_to_response(
            template,
            current_user.username or current_user.email
        ))
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a user template."""
    try:
        template_uuid = uuid.UUID(template_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid template ID format")
    
    template = db.query(FlowTemplate).filter(
        FlowTemplate.id == template_uuid,
        FlowTemplate.author_id == current_user.id,
        FlowTemplate.is_system == False
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found or cannot be deleted")
    
    try:
        db.delete(template)
        db.commit()
        return {"success": True, "message": "Template deleted"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories/list")
async def list_categories(
    flow_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List available template categories."""
    categories = [
        {"id": "research", "name": "리서치", "icon": "🔬"},
        {"id": "knowledge", "name": "지식 관리", "icon": "📚"},
        {"id": "customer-service", "name": "고객 서비스", "icon": "🎧"},
        {"id": "development", "name": "개발", "icon": "💻"},
        {"id": "analytics", "name": "분석", "icon": "📊"},
        {"id": "automation", "name": "자동화", "icon": "⚙️"},
        {"id": "content", "name": "콘텐츠", "icon": "✍️"},
        {"id": "other", "name": "기타", "icon": "📦"},
    ]
    
    return {"categories": categories}
