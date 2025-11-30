"""Agent Builder API endpoints for Workflow Templates."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/workflow-templates",
    tags=["agent-builder-workflow-templates"],
)


# Predefined workflow templates
WORKFLOW_TEMPLATES = {
    "web_scraper": {
        "id": "web_scraper",
        "name": "웹 스크래퍼",
        "description": "웹 페이지에서 데이터를 추출하고 처리하는 워크플로우",
        "category": "data",
        "icon": "🌐",
        "tags": ["scraping", "data", "automation"],
        "difficulty": "beginner",
        "estimated_time": "5분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "manual_trigger", "position": {"x": 100, "y": 100}, "data": {"label": "시작"}},
                {"id": "http_1", "type": "http_request", "position": {"x": 100, "y": 200}, "data": {"label": "웹 페이지 요청", "method": "GET", "url": ""}},
                {"id": "transform_1", "type": "transform", "position": {"x": 100, "y": 300}, "data": {"label": "데이터 추출"}},
                {"id": "output_1", "type": "end", "position": {"x": 100, "y": 400}, "data": {"label": "결과"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "http_1"},
                {"id": "e2", "source": "http_1", "target": "transform_1"},
                {"id": "e3", "source": "transform_1", "target": "output_1"},
            ],
        },
    },
    "ai_chatbot": {
        "id": "ai_chatbot",
        "name": "AI 챗봇",
        "description": "사용자 질문에 AI가 응답하는 챗봇 워크플로우",
        "category": "ai",
        "icon": "🤖",
        "tags": ["ai", "chatbot", "llm"],
        "difficulty": "beginner",
        "estimated_time": "10분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "webhook_trigger", "position": {"x": 100, "y": 100}, "data": {"label": "웹훅 수신"}},
                {"id": "ai_1", "type": "openai_chat", "position": {"x": 100, "y": 200}, "data": {"label": "AI 응답 생성", "model": "gpt-4o-mini"}},
                {"id": "webhook_resp", "type": "webhook_response", "position": {"x": 100, "y": 300}, "data": {"label": "응답 반환"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "ai_1"},
                {"id": "e2", "source": "ai_1", "target": "webhook_resp"},
            ],
        },
    },
    "data_pipeline": {
        "id": "data_pipeline",
        "name": "데이터 파이프라인",
        "description": "데이터베이스에서 데이터를 읽고 변환하여 저장하는 파이프라인",
        "category": "data",
        "icon": "📊",
        "tags": ["database", "etl", "data"],
        "difficulty": "intermediate",
        "estimated_time": "15분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "schedule_trigger", "position": {"x": 100, "y": 100}, "data": {"label": "스케줄 트리거", "cron": "0 * * * *"}},
                {"id": "db_read", "type": "postgresql_query", "position": {"x": 100, "y": 200}, "data": {"label": "데이터 읽기"}},
                {"id": "transform_1", "type": "transform", "position": {"x": 100, "y": 300}, "data": {"label": "데이터 변환"}},
                {"id": "condition_1", "type": "condition", "position": {"x": 100, "y": 400}, "data": {"label": "조건 분기"}},
                {"id": "db_write", "type": "postgresql_query", "position": {"x": 0, "y": 500}, "data": {"label": "데이터 저장"}},
                {"id": "slack_1", "type": "slack", "position": {"x": 200, "y": 500}, "data": {"label": "알림 전송"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "db_read"},
                {"id": "e2", "source": "db_read", "target": "transform_1"},
                {"id": "e3", "source": "transform_1", "target": "condition_1"},
                {"id": "e4", "source": "condition_1", "target": "db_write", "sourceHandle": "true"},
                {"id": "e5", "source": "condition_1", "target": "slack_1", "sourceHandle": "false"},
            ],
        },
    },
    "content_generator": {
        "id": "content_generator",
        "name": "콘텐츠 생성기",
        "description": "AI를 활용한 블로그 포스트 자동 생성 워크플로우",
        "category": "ai",
        "icon": "✍️",
        "tags": ["ai", "content", "writing"],
        "difficulty": "intermediate",
        "estimated_time": "20분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "manual_trigger", "position": {"x": 200, "y": 100}, "data": {"label": "시작"}},
                {"id": "search_1", "type": "tavily_search", "position": {"x": 200, "y": 200}, "data": {"label": "주제 리서치"}},
                {"id": "ai_outline", "type": "openai_chat", "position": {"x": 200, "y": 300}, "data": {"label": "아웃라인 생성"}},
                {"id": "ai_content", "type": "openai_chat", "position": {"x": 200, "y": 400}, "data": {"label": "본문 작성"}},
                {"id": "ai_edit", "type": "openai_chat", "position": {"x": 200, "y": 500}, "data": {"label": "편집 및 교정"}},
                {"id": "output_1", "type": "end", "position": {"x": 200, "y": 600}, "data": {"label": "완성된 콘텐츠"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "search_1"},
                {"id": "e2", "source": "search_1", "target": "ai_outline"},
                {"id": "e3", "source": "ai_outline", "target": "ai_content"},
                {"id": "e4", "source": "ai_content", "target": "ai_edit"},
                {"id": "e5", "source": "ai_edit", "target": "output_1"},
            ],
        },
    },
    "slack_bot": {
        "id": "slack_bot",
        "name": "Slack 봇",
        "description": "Slack 메시지에 자동으로 응답하는 봇",
        "category": "communication",
        "icon": "💬",
        "tags": ["slack", "bot", "automation"],
        "difficulty": "beginner",
        "estimated_time": "10분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "slack_trigger", "position": {"x": 100, "y": 100}, "data": {"label": "Slack 메시지 수신"}},
                {"id": "ai_1", "type": "openai_chat", "position": {"x": 100, "y": 200}, "data": {"label": "응답 생성"}},
                {"id": "slack_1", "type": "slack", "position": {"x": 100, "y": 300}, "data": {"label": "응답 전송"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "ai_1"},
                {"id": "e2", "source": "ai_1", "target": "slack_1"},
            ],
        },
    },
    "email_automation": {
        "id": "email_automation",
        "name": "이메일 자동화",
        "description": "조건에 따라 자동으로 이메일을 발송하는 워크플로우",
        "category": "communication",
        "icon": "📧",
        "tags": ["email", "automation", "notification"],
        "difficulty": "intermediate",
        "estimated_time": "15분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "schedule_trigger", "position": {"x": 100, "y": 100}, "data": {"label": "매일 오전 9시"}},
                {"id": "db_1", "type": "postgresql_query", "position": {"x": 100, "y": 200}, "data": {"label": "대상자 조회"}},
                {"id": "loop_1", "type": "loop", "position": {"x": 100, "y": 300}, "data": {"label": "각 대상자에 대해"}},
                {"id": "ai_1", "type": "openai_chat", "position": {"x": 100, "y": 400}, "data": {"label": "개인화 메시지 생성"}},
                {"id": "email_1", "type": "sendgrid", "position": {"x": 100, "y": 500}, "data": {"label": "이메일 발송"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "db_1"},
                {"id": "e2", "source": "db_1", "target": "loop_1"},
                {"id": "e3", "source": "loop_1", "target": "ai_1"},
                {"id": "e4", "source": "ai_1", "target": "email_1"},
            ],
        },
    },
    "rag_assistant": {
        "id": "rag_assistant",
        "name": "RAG 어시스턴트",
        "description": "문서 기반 질의응답 AI 어시스턴트",
        "category": "ai",
        "icon": "📚",
        "tags": ["rag", "ai", "knowledge"],
        "difficulty": "advanced",
        "estimated_time": "30분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "webhook_trigger", "position": {"x": 200, "y": 100}, "data": {"label": "질문 수신"}},
                {"id": "vector_1", "type": "vector_search", "position": {"x": 200, "y": 200}, "data": {"label": "관련 문서 검색"}},
                {"id": "transform_1", "type": "transform", "position": {"x": 200, "y": 300}, "data": {"label": "컨텍스트 구성"}},
                {"id": "ai_1", "type": "openai_chat", "position": {"x": 200, "y": 400}, "data": {"label": "답변 생성"}},
                {"id": "webhook_resp", "type": "webhook_response", "position": {"x": 200, "y": 500}, "data": {"label": "응답 반환"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "vector_1"},
                {"id": "e2", "source": "vector_1", "target": "transform_1"},
                {"id": "e3", "source": "transform_1", "target": "ai_1"},
                {"id": "e4", "source": "ai_1", "target": "webhook_resp"},
            ],
        },
    },
    "multi_agent_research": {
        "id": "multi_agent_research",
        "name": "멀티 에이전트 리서치",
        "description": "여러 AI 에이전트가 협업하여 리서치를 수행하는 워크플로우",
        "category": "ai",
        "icon": "🔬",
        "tags": ["multi-agent", "research", "ai"],
        "difficulty": "advanced",
        "estimated_time": "45분",
        "graph_definition": {
            "nodes": [
                {"id": "trigger_1", "type": "manual_trigger", "position": {"x": 200, "y": 100}, "data": {"label": "리서치 시작"}},
                {"id": "parallel_1", "type": "parallel", "position": {"x": 200, "y": 200}, "data": {"label": "병렬 검색"}},
                {"id": "search_web", "type": "tavily_search", "position": {"x": 50, "y": 300}, "data": {"label": "웹 검색"}},
                {"id": "search_arxiv", "type": "arxiv_search", "position": {"x": 200, "y": 300}, "data": {"label": "논문 검색"}},
                {"id": "search_wiki", "type": "wikipedia_search", "position": {"x": 350, "y": 300}, "data": {"label": "위키 검색"}},
                {"id": "merge_1", "type": "merge", "position": {"x": 200, "y": 400}, "data": {"label": "결과 병합"}},
                {"id": "ai_analyze", "type": "ai_agent", "position": {"x": 200, "y": 500}, "data": {"label": "분석 에이전트"}},
                {"id": "ai_summarize", "type": "ai_agent", "position": {"x": 200, "y": 600}, "data": {"label": "요약 에이전트"}},
                {"id": "output_1", "type": "end", "position": {"x": 200, "y": 700}, "data": {"label": "리서치 결과"}},
            ],
            "edges": [
                {"id": "e1", "source": "trigger_1", "target": "parallel_1"},
                {"id": "e2", "source": "parallel_1", "target": "search_web"},
                {"id": "e3", "source": "parallel_1", "target": "search_arxiv"},
                {"id": "e4", "source": "parallel_1", "target": "search_wiki"},
                {"id": "e5", "source": "search_web", "target": "merge_1"},
                {"id": "e6", "source": "search_arxiv", "target": "merge_1"},
                {"id": "e7", "source": "search_wiki", "target": "merge_1"},
                {"id": "e8", "source": "merge_1", "target": "ai_analyze"},
                {"id": "e9", "source": "ai_analyze", "target": "ai_summarize"},
                {"id": "e10", "source": "ai_summarize", "target": "output_1"},
            ],
        },
    },
}

# Categories
TEMPLATE_CATEGORIES = [
    {"id": "ai", "name": "AI & ML", "icon": "🤖", "description": "AI 및 머신러닝 워크플로우"},
    {"id": "data", "name": "데이터", "icon": "📊", "description": "데이터 처리 및 ETL"},
    {"id": "communication", "name": "커뮤니케이션", "icon": "💬", "description": "메시징 및 알림"},
    {"id": "automation", "name": "자동화", "icon": "⚡", "description": "업무 자동화"},
]


class TemplateResponse(BaseModel):
    """Template response model."""
    id: str
    name: str
    description: str
    category: str
    icon: str
    tags: List[str]
    difficulty: str
    estimated_time: str


class TemplateDetailResponse(TemplateResponse):
    """Detailed template response with graph definition."""
    graph_definition: Dict[str, Any]


class CreateFromTemplateRequest(BaseModel):
    """Request to create workflow from template."""
    template_id: str
    name: str = Field(..., min_length=1)
    description: str = Field(default="")


# User-created templates storage (in-memory, replace with DB)
_user_templates: Dict[str, Dict[str, Any]] = {}


@router.get("/categories")
async def get_template_categories(
    current_user: User = Depends(get_current_user),
):
    """Get template categories."""
    return {"categories": TEMPLATE_CATEGORIES}


@router.get("")
async def list_templates(
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    include_user: bool = Query(True, description="Include user-created templates"),
    current_user: User = Depends(get_current_user),
):
    """
    List available workflow templates.
    
    Returns both system templates and user-created templates.
    """
    templates = []
    
    # System templates
    for template_id, template in WORKFLOW_TEMPLATES.items():
        if category and template["category"] != category:
            continue
        if difficulty and template["difficulty"] != difficulty:
            continue
        if search:
            search_lower = search.lower()
            if search_lower not in template["name"].lower() and \
               search_lower not in template["description"].lower():
                continue
        
        templates.append(TemplateResponse(
            id=template["id"],
            name=template["name"],
            description=template["description"],
            category=template["category"],
            icon=template["icon"],
            tags=template["tags"],
            difficulty=template["difficulty"],
            estimated_time=template["estimated_time"],
        ))
    
    # User templates
    if include_user:
        user_id = str(current_user.id)
        for template_id, template in _user_templates.items():
            if template.get("user_id") != user_id and not template.get("is_public"):
                continue
            if category and template.get("category") != category:
                continue
            if difficulty and template.get("difficulty") != difficulty:
                continue
            if search:
                search_lower = search.lower()
                if search_lower not in template["name"].lower() and \
                   search_lower not in template.get("description", "").lower():
                    continue
            
            templates.append(TemplateResponse(
                id=template["id"],
                name=template["name"],
                description=template.get("description", ""),
                category=template.get("category", "custom"),
                icon=template.get("icon", "📋"),
                tags=template.get("tags", []),
                difficulty=template.get("difficulty", "intermediate"),
                estimated_time=template.get("estimated_time", "Unknown"),
            ))
    
    return {
        "templates": templates,
        "total": len(templates),
    }


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get template details including graph definition."""
    # Check system templates
    if template_id in WORKFLOW_TEMPLATES:
        template = WORKFLOW_TEMPLATES[template_id]
        return TemplateDetailResponse(
            id=template["id"],
            name=template["name"],
            description=template["description"],
            category=template["category"],
            icon=template["icon"],
            tags=template["tags"],
            difficulty=template["difficulty"],
            estimated_time=template["estimated_time"],
            graph_definition=template["graph_definition"],
        )
    
    # Check user templates
    if template_id in _user_templates:
        template = _user_templates[template_id]
        user_id = str(current_user.id)
        
        if template.get("user_id") != user_id and not template.get("is_public"):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return TemplateDetailResponse(
            id=template["id"],
            name=template["name"],
            description=template.get("description", ""),
            category=template.get("category", "custom"),
            icon=template.get("icon", "📋"),
            tags=template.get("tags", []),
            difficulty=template.get("difficulty", "intermediate"),
            estimated_time=template.get("estimated_time", "Unknown"),
            graph_definition=template["graph_definition"],
        )
    
    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/create-workflow")
async def create_workflow_from_template(
    request: CreateFromTemplateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new workflow from a template.
    
    Copies the template's graph definition to a new workflow.
    """
    # Get template
    template = None
    if request.template_id in WORKFLOW_TEMPLATES:
        template = WORKFLOW_TEMPLATES[request.template_id]
    elif request.template_id in _user_templates:
        template = _user_templates[request.template_id]
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        from backend.services.agent_builder.workflow_service import WorkflowService
        from backend.models.agent_builder import WorkflowCreate
        
        workflow_service = WorkflowService(db)
        
        # Create workflow from template
        workflow_data = WorkflowCreate(
            name=request.name,
            description=request.description or template.get("description", ""),
            graph_definition=template["graph_definition"],
            is_public=False,
        )
        
        workflow = workflow_service.create_workflow(
            user_id=str(current_user.id),
            workflow_data=workflow_data,
        )
        
        return {
            "workflow_id": str(workflow.id),
            "name": workflow.name,
            "message": f"Workflow created from template '{template['name']}'",
        }
        
    except Exception as e:
        logger.error(f"Failed to create workflow from template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_as_template(
    workflow_id: str = Query(..., description="Workflow ID to save as template"),
    name: str = Query(..., description="Template name"),
    description: str = Query("", description="Template description"),
    category: str = Query("custom", description="Template category"),
    is_public: bool = Query(False, description="Make template public"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save an existing workflow as a template.
    """
    try:
        from backend.services.agent_builder.workflow_service import WorkflowService
        
        workflow_service = WorkflowService(db)
        workflow = workflow_service.get_workflow(workflow_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if str(workflow.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        template_id = str(uuid.uuid4())
        
        _user_templates[template_id] = {
            "id": template_id,
            "name": name,
            "description": description,
            "category": category,
            "icon": "📋",
            "tags": [],
            "difficulty": "intermediate",
            "estimated_time": "Unknown",
            "graph_definition": workflow.graph_definition,
            "user_id": str(current_user.id),
            "is_public": is_public,
            "created_at": datetime.utcnow().isoformat(),
            "source_workflow_id": workflow_id,
        }
        
        return {
            "template_id": template_id,
            "name": name,
            "message": "Template saved successfully",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save template: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
):
    """Delete a user-created template."""
    if template_id in WORKFLOW_TEMPLATES:
        raise HTTPException(status_code=400, detail="Cannot delete system templates")
    
    if template_id not in _user_templates:
        raise HTTPException(status_code=404, detail="Template not found")
    
    template = _user_templates[template_id]
    if template.get("user_id") != str(current_user.id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    del _user_templates[template_id]
    
    return {"message": "Template deleted", "id": template_id}
