"""
Cached Query Functions
자주 조회되는 데이터에 대한 캐싱된 쿼리 함수들
"""

from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.core.query_cache import cache_query, cache_query_list
from backend.db.models.agent_builder import Tool, AgentTemplate, PromptTemplate
from backend.db.models.user import User

logger = logging.getLogger(__name__)


@cache_query(ttl=3600, key_prefix="tool")
def get_tool_cached(db: Session, tool_id: str) -> Optional[Tool]:
    """
    Tool 조회 (1시간 캐싱)
    
    Tool은 거의 변경되지 않으므로 캐싱 효과가 큼
    """
    return db.query(Tool).filter(Tool.id == tool_id).first()


@cache_query_list(ttl=1800, key_prefix="tools")
def get_all_tools_cached(db: Session, category: Optional[str] = None) -> List[Tool]:
    """
    모든 Tool 조회 (30분 캐싱)
    
    Args:
        db: Database session
        category: Tool 카테고리 필터 (선택)
    """
    query = db.query(Tool)
    
    if category:
        query = query.filter(Tool.category == category)
    
    return query.all()


@cache_query_list(ttl=3600, key_prefix="builtin_tools")
def get_builtin_tools_cached(db: Session) -> List[Tool]:
    """
    내장 Tool 조회 (1시간 캐싱)
    
    내장 Tool은 변경되지 않으므로 긴 TTL 사용
    """
    return db.query(Tool).filter(Tool.is_builtin == True).all()


@cache_query(ttl=1800, key_prefix="agent_template")
def get_agent_template_cached(db: Session, template_id: str) -> Optional[AgentTemplate]:
    """
    AgentTemplate 조회 (30분 캐싱)
    """
    return db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()


@cache_query_list(ttl=1800, key_prefix="agent_templates")
def get_published_templates_cached(db: Session) -> List[AgentTemplate]:
    """
    공개된 AgentTemplate 조회 (30분 캐싱)
    """
    return db.query(AgentTemplate)\
        .filter(AgentTemplate.is_published == True)\
        .order_by(AgentTemplate.rating.desc())\
        .all()


@cache_query(ttl=1800, key_prefix="prompt_template")
def get_prompt_template_cached(db: Session, template_id: str) -> Optional[PromptTemplate]:
    """
    PromptTemplate 조회 (30분 캐싱)
    """
    return db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()


@cache_query_list(ttl=1800, key_prefix="system_prompts")
def get_system_prompt_templates_cached(db: Session) -> List[PromptTemplate]:
    """
    시스템 PromptTemplate 조회 (30분 캐싱)
    
    시스템 템플릿은 거의 변경되지 않음
    """
    return db.query(PromptTemplate)\
        .filter(PromptTemplate.is_system == True)\
        .all()


@cache_query(ttl=300, key_prefix="user")
def get_user_cached(db: Session, user_id: str) -> Optional[User]:
    """
    User 조회 (5분 캐싱)
    
    사용자 정보는 자주 변경될 수 있으므로 짧은 TTL
    """
    return db.query(User).filter(User.id == user_id).first()


# 캐시 무효화 헬퍼 함수들

def invalidate_tool_cache(tool_id: str = None):
    """Tool 캐시 무효화"""
    from backend.core.query_cache import invalidate_cache_pattern
    
    if tool_id:
        # 특정 Tool 캐시만 무효화
        invalidate_cache_pattern(f"tool:get_tool_cached:*{tool_id}*")
    else:
        # 모든 Tool 캐시 무효화
        invalidate_cache_pattern("tool:*")
        invalidate_cache_pattern("tools:*")
        invalidate_cache_pattern("builtin_tools:*")


def invalidate_template_cache(template_id: str = None):
    """Template 캐시 무효화"""
    from backend.core.query_cache import invalidate_cache_pattern
    
    if template_id:
        invalidate_cache_pattern(f"*template*:*{template_id}*")
    else:
        invalidate_cache_pattern("agent_template:*")
        invalidate_cache_pattern("agent_templates:*")
        invalidate_cache_pattern("prompt_template:*")
        invalidate_cache_pattern("system_prompts:*")


def invalidate_user_cache(user_id: str):
    """User 캐시 무효화"""
    from backend.core.query_cache import invalidate_cache_pattern
    invalidate_cache_pattern(f"user:*{user_id}*")
