"""
Database Query Helpers
N+1 쿼리 문제 해결을 위한 헬퍼 함수들
"""

from sqlalchemy.orm import Session, joinedload, selectinload
from typing import Optional, List
from backend.db.models.agent_builder import (
    Workflow, Agent, Block, Knowledgebase,
    WorkflowExecution, AgentExecution
)


def get_workflow_with_relations(db: Session, workflow_id: str) -> Optional[Workflow]:
    """
    워크플로우를 모든 관계와 함께 조회 (N+1 쿼리 방지)
    
    Args:
        db: Database session
        workflow_id: Workflow ID
        
    Returns:
        Workflow with all relations loaded
    """
    return db.query(Workflow)\
        .options(
            joinedload(Workflow.nodes),
            joinedload(Workflow.edges),
            selectinload(Workflow.blocks).joinedload(AgentBlock.source_edges),
            selectinload(Workflow.blocks).joinedload(AgentBlock.target_edges),
            selectinload(Workflow.schedules),
            selectinload(Workflow.webhooks)
        )\
        .filter(Workflow.id == workflow_id)\
        .first()


def get_agent_with_relations(db: Session, agent_id: str) -> Optional[Agent]:
    """
    에이전트를 모든 관계와 함께 조회 (N+1 쿼리 방지)
    
    Args:
        db: Database session
        agent_id: Agent ID
        
    Returns:
        Agent with all relations loaded
    """
    return db.query(Agent)\
        .options(
            selectinload(Agent.tools).joinedload(AgentTool.tool),
            selectinload(Agent.knowledgebases).joinedload(AgentKnowledgebase.knowledgebase),
            selectinload(Agent.versions)
        )\
        .filter(Agent.id == agent_id)\
        .first()


def get_workflow_executions_optimized(
    db: Session,
    workflow_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[WorkflowExecution]:
    """
    워크플로우 실행 이력 최적화 조회
    
    Args:
        db: Database session
        workflow_id: Workflow ID
        limit: Maximum results
        offset: Offset for pagination
        
    Returns:
        List of workflow executions
    """
    return db.query(WorkflowExecution)\
        .filter(WorkflowExecution.workflow_id == workflow_id)\
        .order_by(WorkflowExecution.started_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()


def get_agent_executions_with_metrics(
    db: Session,
    agent_id: str,
    limit: int = 50
) -> List[AgentExecution]:
    """
    에이전트 실행 이력을 메트릭과 함께 조회
    
    Args:
        db: Database session
        agent_id: Agent ID
        limit: Maximum results
        
    Returns:
        List of agent executions with metrics
    """
    return db.query(AgentExecution)\
        .options(
            joinedload(AgentExecution.metrics),
            selectinload(AgentExecution.steps)
        )\
        .filter(AgentExecution.agent_id == agent_id)\
        .order_by(AgentExecution.started_at.desc())\
        .limit(limit)\
        .all()


def get_user_workflows_optimized(
    db: Session,
    user_id: str,
    include_public: bool = False
) -> List[Workflow]:
    """
    사용자 워크플로우 최적화 조회
    
    Args:
        db: Database session
        user_id: User ID
        include_public: Include public workflows
        
    Returns:
        List of workflows
    """
    query = db.query(Workflow)
    
    if include_public:
        query = query.filter(
            (Workflow.user_id == user_id) | (Workflow.is_public == True)
        )
    else:
        query = query.filter(Workflow.user_id == user_id)
    
    return query\
        .order_by(Workflow.created_at.desc())\
        .all()


def get_knowledgebase_with_documents(
    db: Session,
    kb_id: str
) -> Optional[Knowledgebase]:
    """
    지식베이스를 문서와 함께 조회
    
    Args:
        db: Database session
        kb_id: Knowledgebase ID
        
    Returns:
        Knowledgebase with documents
    """
    return db.query(Knowledgebase)\
        .options(
            selectinload(Knowledgebase.documents),
            selectinload(Knowledgebase.agent_links)
        )\
        .filter(Knowledgebase.id == kb_id)\
        .first()


def get_dashboard_executions_optimized(
    db: Session,
    user_id: str,
    limit: int = 50
) -> List[AgentExecution]:
    """
    대시보드용 실행 이력 최적화 조회 (N+1 쿼리 방지)
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum results
        
    Returns:
        List of agent executions with agent info preloaded
    """
    return db.query(AgentExecution)\
        .options(
            joinedload(AgentExecution.agent),
            joinedload(AgentExecution.metrics)
        )\
        .filter(AgentExecution.user_id == user_id)\
        .order_by(AgentExecution.started_at.desc())\
        .limit(limit)\
        .all()


# Import AgentBlock and AgentTool for type hints
from backend.db.models.agent_builder import AgentBlock, AgentTool, AgentKnowledgebase
