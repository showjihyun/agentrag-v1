"""
Knowledge Graph Workflow Blocks

워크플로우에서 사용할 수 있는 지식 그래프 관련 블록들.
엔티티 검색, 관계 탐색, 경로 찾기 등의 기능 제공.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.blocks.base import BaseBlock, BlockRegistry, BlockCategory
from backend.services.agent_builder.knowledge_graph_service import KnowledgeGraphService
from backend.services.agent_builder.hybrid_search_service import HybridSearchService
from backend.core.dependencies import get_db


class KGEntitySearchInput(BaseModel):
    """지식 그래프 엔티티 검색 입력"""
    knowledge_graph_id: str = Field(..., description="지식 그래프 ID")
    query: str = Field(..., description="검색 쿼리")
    entity_types: Optional[List[str]] = Field(None, description="엔티티 타입 필터")
    limit: int = Field(default=10, description="결과 수 제한")


class KGEntitySearchOutput(BaseModel):
    """지식 그래프 엔티티 검색 출력"""
    entities: List[Dict[str, Any]] = Field(..., description="검색된 엔티티 목록")
    total_count: int = Field(..., description="총 결과 수")


@BlockRegistry.register(
    "kg_entity_search",
    category=BlockCategory.KNOWLEDGE,
    name="KG 엔티티 검색",
    description="지식 그래프에서 엔티티를 검색합니다",
    icon="🔍",
)
class KGEntitySearchBlock(BaseBlock):
    """지식 그래프 엔티티 검색 블록"""

    input_schema = KGEntitySearchInput
    output_schema = KGEntitySearchOutput

    async def execute(self, inputs: KGEntitySearchInput, context: Dict[str, Any]) -> KGEntitySearchOutput:
        """엔티티 검색 실행"""
        
        db = next(get_db())
        try:
            service = KnowledgeGraphService(db)
            
            entities = await service.search_entities(
                kg_id=inputs.knowledge_graph_id,
                query=inputs.query,
                entity_types=inputs.entity_types,
                limit=inputs.limit
            )
            
            return KGEntitySearchOutput(
                entities=entities,
                total_count=len(entities)
            )
            
        finally:
            db.close()


class KGRelationshipSearchInput(BaseModel):
    """지식 그래프 관계 검색 입력"""
    knowledge_graph_id: str = Field(..., description="지식 그래프 ID")
    entity_id: Optional[str] = Field(None, description="특정 엔티티의 관계 검색")
    relation_types: Optional[List[str]] = Field(None, description="관계 타입 필터")
    limit: int = Field(default=10, description="결과 수 제한")


class KGRelationshipSearchOutput(BaseModel):
    """지식 그래프 관계 검색 출력"""
    relationships: List[Dict[str, Any]] = Field(..., description="검색된 관계 목록")
    total_count: int = Field(..., description="총 결과 수")


@BlockRegistry.register(
    "kg_relationship_search",
    category=BlockCategory.KNOWLEDGE,
    name="KG 관계 검색",
    description="지식 그래프에서 관계를 검색합니다",
    icon="🔗",
)
class KGRelationshipSearchBlock(BaseBlock):
    """지식 그래프 관계 검색 블록"""

    input_schema = KGRelationshipSearchInput
    output_schema = KGRelationshipSearchOutput

    async def execute(self, inputs: KGRelationshipSearchInput, context: Dict[str, Any]) -> KGRelationshipSearchOutput:
        """관계 검색 실행"""
        
        db = next(get_db())
        try:
            service = KnowledgeGraphService(db)
            
            relationships = await service.find_relationships(
                kg_id=inputs.knowledge_graph_id,
                entity_id=inputs.entity_id,
                relation_types=inputs.relation_types,
                limit=inputs.limit
            )
            
            return KGRelationshipSearchOutput(
                relationships=relationships,
                total_count=len(relationships)
            )
            
        finally:
            db.close()


class KGPathFindingInput(BaseModel):
    """지식 그래프 경로 찾기 입력"""
    knowledge_graph_id: str = Field(..., description="지식 그래프 ID")
    source_entity_id: str = Field(..., description="시작 엔티티 ID")
    target_entity_id: str = Field(..., description="목표 엔티티 ID")
    max_depth: int = Field(default=3, description="최대 경로 깊이")


class KGPathFindingOutput(BaseModel):
    """지식 그래프 경로 찾기 출력"""
    paths: List[List[Dict[str, Any]]] = Field(..., description="발견된 경로들")
    path_count: int = Field(..., description="경로 수")


@BlockRegistry.register(
    "kg_path_finding",
    category=BlockCategory.KNOWLEDGE,
    name="KG 경로 찾기",
    description="두 엔티티 간의 경로를 찾습니다",
    icon="🛤️",
)
class KGPathFindingBlock(BaseBlock):
    """지식 그래프 경로 찾기 블록"""

    input_schema = KGPathFindingInput
    output_schema = KGPathFindingOutput

    async def execute(self, inputs: KGPathFindingInput, context: Dict[str, Any]) -> KGPathFindingOutput:
        """경로 찾기 실행"""
        
        db = next(get_db())
        try:
            service = KnowledgeGraphService(db)
            
            paths = await service.find_path(
                kg_id=inputs.knowledge_graph_id,
                source_entity_id=inputs.source_entity_id,
                target_entity_id=inputs.target_entity_id,
                max_depth=inputs.max_depth
            )
            
            return KGPathFindingOutput(
                paths=paths,
                path_count=len(paths)
            )
            
        finally:
            db.close()


class KGSubgraphInput(BaseModel):
    """지식 그래프 서브그래프 추출 입력"""
    knowledge_graph_id: str = Field(..., description="지식 그래프 ID")
    entity_ids: List[str] = Field(..., description="중심 엔티티 ID 목록")
    depth: int = Field(default=1, description="확장 깊이")


class KGSubgraphOutput(BaseModel):
    """지식 그래프 서브그래프 추출 출력"""
    entities: List[Dict[str, Any]] = Field(..., description="서브그래프 엔티티들")
    relationships: List[Dict[str, Any]] = Field(..., description="서브그래프 관계들")


@BlockRegistry.register(
    "kg_subgraph",
    category=BlockCategory.KNOWLEDGE,
    name="KG 서브그래프 추출",
    description="특정 엔티티 주변의 서브그래프를 추출합니다",
    icon="🕸️",
)
class KGSubgraphBlock(BaseBlock):
    """지식 그래프 서브그래프 추출 블록"""

    input_schema = KGSubgraphInput
    output_schema = KGSubgraphOutput

    async def execute(self, inputs: KGSubgraphInput, context: Dict[str, Any]) -> KGSubgraphOutput:
        """서브그래프 추출 실행"""
        
        db = next(get_db())
        try:
            service = KnowledgeGraphService(db)
            
            subgraph = await service.get_subgraph(
                kg_id=inputs.knowledge_graph_id,
                entity_ids=inputs.entity_ids,
                depth=inputs.depth
            )
            
            return KGSubgraphOutput(
                entities=subgraph["entities"],
                relationships=subgraph["relationships"]
            )
            
        finally:
            db.close()


class HybridSearchInput(BaseModel):
    """하이브리드 검색 입력"""
    knowledgebase_id: str = Field(..., description="지식베이스 ID")
    query: str = Field(..., description="검색 쿼리")
    search_strategy: str = Field(default="hybrid", description="검색 전략")
    vector_weight: float = Field(default=0.7, description="벡터 검색 가중치")
    graph_weight: float = Field(default=0.3, description="그래프 검색 가중치")
    limit: int = Field(default=10, description="결과 수 제한")


class HybridSearchOutput(BaseModel):
    """하이브리드 검색 출력"""
    documents: List[Dict[str, Any]] = Field(..., description="문서 검색 결과")
    entities: List[Dict[str, Any]] = Field(..., description="엔티티 검색 결과")
    relationships: List[Dict[str, Any]] = Field(..., description="관계 검색 결과")
    metadata: Dict[str, Any] = Field(..., description="검색 메타데이터")


@BlockRegistry.register(
    "hybrid_search",
    category=BlockCategory.SEARCH,
    name="하이브리드 검색",
    description="벡터 검색과 지식 그래프 검색을 결합합니다",
    icon="⚡",
)
class HybridSearchBlock(BaseBlock):
    """하이브리드 검색 블록"""

    input_schema = HybridSearchInput
    output_schema = HybridSearchOutput

    async def execute(self, inputs: HybridSearchInput, context: Dict[str, Any]) -> HybridSearchOutput:
        """하이브리드 검색 실행"""
        
        db = next(get_db())
        try:
            service = HybridSearchService(db)
            
            results = await service.search(
                knowledgebase_id=inputs.knowledgebase_id,
                query=inputs.query,
                search_strategy=inputs.search_strategy,
                vector_weight=inputs.vector_weight,
                graph_weight=inputs.graph_weight,
                limit=inputs.limit
            )
            
            return HybridSearchOutput(
                documents=results["documents"],
                entities=results["entities"],
                relationships=results["relationships"],
                metadata=results["metadata"]
            )
            
        finally:
            db.close()


class EntityContextInput(BaseModel):
    """엔티티 컨텍스트 조회 입력"""
    knowledgebase_id: str = Field(..., description="지식베이스 ID")
    entity_id: str = Field(..., description="엔티티 ID")
    context_depth: int = Field(default=2, description="컨텍스트 깊이")


class EntityContextOutput(BaseModel):
    """엔티티 컨텍스트 조회 출력"""
    entity_id: str = Field(..., description="엔티티 ID")
    context: Dict[str, Any] = Field(..., description="엔티티 컨텍스트")
    context_depth: int = Field(..., description="컨텍스트 깊이")


@BlockRegistry.register(
    "entity_context",
    category=BlockCategory.KNOWLEDGE,
    name="엔티티 컨텍스트",
    description="엔티티의 상세 컨텍스트를 조회합니다",
    icon="🎯",
)
class EntityContextBlock(BaseBlock):
    """엔티티 컨텍스트 조회 블록"""

    input_schema = EntityContextInput
    output_schema = EntityContextOutput

    async def execute(self, inputs: EntityContextInput, context: Dict[str, Any]) -> EntityContextOutput:
        """엔티티 컨텍스트 조회 실행"""
        
        db = next(get_db())
        try:
            service = HybridSearchService(db)
            
            entity_context = await service.get_entity_context(
                knowledgebase_id=inputs.knowledgebase_id,
                entity_id=inputs.entity_id,
                context_depth=inputs.context_depth
            )
            
            return EntityContextOutput(
                entity_id=inputs.entity_id,
                context=entity_context,
                context_depth=inputs.context_depth
            )
            
        finally:
            db.close()


# 블록 카테고리 확장
if not hasattr(BlockCategory, 'KNOWLEDGE'):
    BlockCategory.KNOWLEDGE = "knowledge"