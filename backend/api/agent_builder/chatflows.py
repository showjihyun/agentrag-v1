# Chatflow-specific API endpoints

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.services.agent_builder.facade import AgentBuilderFacade
from backend.db.models.flows import Chatflow, ChatflowTool as ChatflowToolModel

router = APIRouter(prefix="/api/agent-builder/chatflows", tags=["Chatflows"])


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatConfig(BaseModel):
    """Chat configuration for Chatflow."""
    llm_provider: str
    llm_model: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 2000
    streaming: bool = True
    welcome_message: Optional[str] = None
    suggested_questions: List[str] = []


class MemoryConfig(BaseModel):
    """Memory configuration for Chatflow."""
    type: str = "buffer"  # buffer, summary, vector, hybrid
    max_messages: int = 10
    summary_threshold: Optional[int] = None
    vector_store_id: Optional[str] = None


class RAGConfig(BaseModel):
    """RAG configuration for Chatflow."""
    enabled: bool = False
    knowledgebase_ids: List[str] = []
    retrieval_strategy: str = "similarity"  # similarity, mmr, hybrid
    top_k: int = 5
    score_threshold: float = 0.7
    reranking_enabled: bool = False
    reranking_model: Optional[str] = None


class ChatflowToolRequest(BaseModel):
    """Tool configuration in Chatflow."""
    tool_id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    configuration: Optional[dict] = None


class CreateChatflowRequest(BaseModel):
    """Request model for creating Chatflow."""
    name: str
    description: Optional[str] = None
    chat_config: ChatConfig
    memory_config: Optional[MemoryConfig] = None
    rag_config: Optional[RAGConfig] = None
    graph_definition: Optional[dict] = None
    tags: List[str] = []


class UpdateChatflowRequest(BaseModel):
    """Request model for updating Chatflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    chat_config: Optional[ChatConfig] = None
    memory_config: Optional[MemoryConfig] = None
    rag_config: Optional[RAGConfig] = None
    graph_definition: Optional[dict] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("")
async def create_chatflow(
    request: CreateChatflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Chatflow.
    
    Chatflow is a single-agent chat assistant with memory and RAG.
    """
    try:
        # Create Chatflow directly using the flows model
        chatflow = Chatflow(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            chat_config=request.chat_config.dict(),
            memory_config=request.memory_config.dict() if request.memory_config else {},
            rag_config=request.rag_config.dict() if request.rag_config else {},
            graph_definition=request.graph_definition or {},
            tags=request.tags,
        )
        
        db.add(chatflow)
        db.flush()
        
        # Return as dict for consistency
        result = {
            "id": str(chatflow.id),
            "name": chatflow.name,
            "description": chatflow.description,
            "chat_config": chatflow.chat_config,
            "memory_config": chatflow.memory_config,
            "rag_config": chatflow.rag_config,
            "graph_definition": chatflow.graph_definition,
            "tags": chatflow.tags,
            "is_active": chatflow.is_active,
            "created_at": chatflow.created_at.isoformat(),
            "updated_at": chatflow.updated_at.isoformat(),
        }
        
        db.commit()
        return result
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("")
async def get_chatflows(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of Chatflows.
    """
    try:
        # Query Chatflows directly
        query = db.query(Chatflow).filter(
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        )
        
        # Apply filters
        if search:
            search_lower = f"%{search.lower()}%"
            query = query.filter(
                (Chatflow.name.ilike(search_lower)) |
                (Chatflow.description.ilike(search_lower))
            )
        
        if category:
            query = query.filter(Chatflow.category == category)
        
        if is_active is not None:
            query = query.filter(Chatflow.is_active == is_active)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and get results
        chatflows = query.order_by(Chatflow.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # Convert to dict format
        flows = []
        for flow in chatflows:
            flow_dict = {
                "id": str(flow.id),
                "name": flow.name,
                "description": flow.description,
                "chat_config": flow.chat_config,
                "memory_config": flow.memory_config,
                "rag_config": flow.rag_config,
                "graph_definition": flow.graph_definition,
                "tags": flow.tags,
                "category": flow.category,
                "is_active": flow.is_active,
                "execution_count": flow.execution_count,
                "last_execution_status": flow.last_execution_status,
                "last_execution_at": flow.last_execution_at.isoformat() if flow.last_execution_at else None,
                "created_at": flow.created_at.isoformat(),
                "updated_at": flow.updated_at.isoformat(),
                "tools": [
                    {
                        "id": str(tool.id),
                        "tool_id": tool.tool_id,
                        "name": tool.name,
                        "description": tool.description,
                        "enabled": tool.enabled,
                        "configuration": tool.configuration,
                    }
                    for tool in flow.tools
                ]
            }
            
            # Apply tag filter if specified
            if tags:
                if any(tag in flow_dict.get('tags', []) for tag in tags):
                    flows.append(flow_dict)
            else:
                flows.append(flow_dict)
        
        return {
            "flows": flows,
            "total": total,
            "page": page,
            "page_size": page_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chatflow_id}")
async def get_chatflow(
    chatflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific Chatflow by ID.
    """
    try:
        # Query Chatflow directly
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == chatflow_id,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Convert to dict format
        result = {
            "id": str(chatflow.id),
            "name": chatflow.name,
            "description": chatflow.description,
            "chat_config": chatflow.chat_config,
            "memory_config": chatflow.memory_config,
            "rag_config": chatflow.rag_config,
            "graph_definition": chatflow.graph_definition,
            "tags": chatflow.tags,
            "category": chatflow.category,
            "is_active": chatflow.is_active,
            "execution_count": chatflow.execution_count,
            "last_execution_status": chatflow.last_execution_status,
            "last_execution_at": chatflow.last_execution_at.isoformat() if chatflow.last_execution_at else None,
            "created_at": chatflow.created_at.isoformat(),
            "updated_at": chatflow.updated_at.isoformat(),
            "tools": [
                {
                    "id": str(tool.id),
                    "tool_id": tool.tool_id,
                    "name": tool.name,
                    "description": tool.description,
                    "enabled": tool.enabled,
                    "configuration": tool.configuration,
                }
                for tool in chatflow.tools
            ]
        }
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{chatflow_id}")
async def update_chatflow(
    chatflow_id: str,
    request: UpdateChatflowRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a Chatflow.
    """
    try:
        # Get existing Chatflow
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == chatflow_id,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Update fields
        if request.name is not None:
            chatflow.name = request.name
        if request.description is not None:
            chatflow.description = request.description
        if request.chat_config is not None:
            chatflow.chat_config = request.chat_config.dict()
        if request.memory_config is not None:
            chatflow.memory_config = request.memory_config.dict()
        if request.rag_config is not None:
            chatflow.rag_config = request.rag_config.dict()
        if request.graph_definition is not None:
            chatflow.graph_definition = request.graph_definition
        if request.is_active is not None:
            chatflow.is_active = request.is_active
        if request.tags is not None:
            chatflow.tags = request.tags
        
        # Update timestamp
        from datetime import datetime
        chatflow.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(chatflow)
        
        # Return updated data
        result = {
            "id": str(chatflow.id),
            "name": chatflow.name,
            "description": chatflow.description,
            "chat_config": chatflow.chat_config,
            "memory_config": chatflow.memory_config,
            "rag_config": chatflow.rag_config,
            "graph_definition": chatflow.graph_definition,
            "tags": chatflow.tags,
            "category": chatflow.category,
            "is_active": chatflow.is_active,
            "execution_count": chatflow.execution_count,
            "last_execution_status": chatflow.last_execution_status,
            "last_execution_at": chatflow.last_execution_at.isoformat() if chatflow.last_execution_at else None,
            "created_at": chatflow.created_at.isoformat(),
            "updated_at": chatflow.updated_at.isoformat(),
        }
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chatflow_id}")
async def delete_chatflow(
    chatflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a Chatflow.
    """
    try:
        # Get existing Chatflow
        chatflow = db.query(Chatflow).filter(
            Chatflow.id == chatflow_id,
            Chatflow.user_id == current_user.id,
            Chatflow.deleted_at.is_(None)
        ).first()
        
        if not chatflow:
            raise HTTPException(status_code=404, detail="Chatflow not found")
        
        # Soft delete
        from datetime import datetime
        chatflow.deleted_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Chatflow deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chatflow ID")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
