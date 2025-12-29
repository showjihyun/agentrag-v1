"""
Knowledge Graph Analytics API endpoints.

지식 그래프 분석 및 인사이트 추출을 위한 REST API 제공.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.core.dependencies import get_db
from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.models.knowledge_graph import KnowledgeGraph
from backend.services.agent_builder.kg_analytics_service import KGAnalyticsService
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/agent-builder/kg-analytics", tags=["Knowledge Graph Analytics"])


class AnalysisRequest(BaseModel):
    """지식 그래프 분석 요청 스키마"""
    
    include_centrality: bool = Field(default=True, description="중심성 분석 포함")
    include_communities: bool = Field(default=True, description="커뮤니티 분석 포함")
    include_patterns: bool = Field(default=True, description="패턴 분석 포함")
    include_temporal: bool = Field(default=True, description="시간 분석 포함")


class NetworkMetricsResponse(BaseModel):
    """네트워크 메트릭 응답 스키마"""
    
    node_count: int
    edge_count: int
    density: float
    average_degree: float
    clustering_coefficient: float
    diameter: int
    connected_components: int
    largest_component_size: int


class CentralityMetricsResponse(BaseModel):
    """중심성 메트릭 응답 스키마"""
    
    entity_id: str
    entity_name: str
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    eigenvector_centrality: float
    pagerank: float


class CommunityResponse(BaseModel):
    """커뮤니티 응답 스키마"""
    
    id: int
    entities: List[str]
    size: int
    density: float
    modularity: float
    dominant_types: List[str]
    key_relationships: List[str]


class KnowledgePatternResponse(BaseModel):
    """지식 패턴 응답 스키마"""
    
    pattern_type: str
    description: str
    entities: List[str]
    relationships: List[str]
    confidence: float
    frequency: int
    examples: List[Dict[str, Any]]


class AnalysisResponse(BaseModel):
    """종합 분석 응답 스키마"""
    
    kg_id: str
    analysis_timestamp: str
    network_metrics: Optional[NetworkMetricsResponse]
    centrality_metrics: Optional[List[CentralityMetricsResponse]]
    communities: Optional[List[CommunityResponse]]
    knowledge_patterns: Optional[List[KnowledgePatternResponse]]
    temporal_analysis: Optional[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


@router.post("/{kg_id}/analyze", response_model=AnalysisResponse)
async def analyze_knowledge_graph(
    kg_id: str,
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """지식 그래프 종합 분석 수행"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        
        # 분석 수행
        analysis_results = await service.analyze_knowledge_graph(
            kg_id=kg_id,
            include_centrality=request.include_centrality,
            include_communities=request.include_communities,
            include_patterns=request.include_patterns,
            include_temporal=request.include_temporal,
        )
        
        # 백그라운드에서 분석 결과 저장
        background_tasks.add_task(
            _save_analysis_results,
            db,
            kg_id,
            analysis_results
        )
        
        return AnalysisResponse(**analysis_results)
        
    except Exception as e:
        logger.error(f"Error analyzing knowledge graph {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")


@router.get("/{kg_id}/network-metrics", response_model=NetworkMetricsResponse)
async def get_network_metrics(
    kg_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """네트워크 기본 메트릭 조회"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        metrics = await service._calculate_network_metrics(kg_id)
        
        return NetworkMetricsResponse(
            node_count=metrics.node_count,
            edge_count=metrics.edge_count,
            density=metrics.density,
            average_degree=metrics.average_degree,
            clustering_coefficient=metrics.clustering_coefficient,
            diameter=metrics.diameter,
            connected_components=metrics.connected_components,
            largest_component_size=metrics.largest_component_size,
        )
        
    except Exception as e:
        logger.error(f"Error calculating network metrics for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate network metrics")


@router.get("/{kg_id}/centrality", response_model=List[CentralityMetricsResponse])
async def get_centrality_metrics(
    kg_id: str,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """중심성 메트릭 조회"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        centrality_metrics = await service._calculate_centrality_metrics(kg_id)
        
        return [
            CentralityMetricsResponse(
                entity_id=metric.entity_id,
                entity_name=metric.entity_name,
                degree_centrality=metric.degree_centrality,
                betweenness_centrality=metric.betweenness_centrality,
                closeness_centrality=metric.closeness_centrality,
                eigenvector_centrality=metric.eigenvector_centrality,
                pagerank=metric.pagerank,
            )
            for metric in centrality_metrics[:limit]
        ]
        
    except Exception as e:
        logger.error(f"Error calculating centrality metrics for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to calculate centrality metrics")


@router.get("/{kg_id}/communities", response_model=List[CommunityResponse])
async def get_communities(
    kg_id: str,
    min_size: int = Query(default=3, ge=2),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """커뮤니티 탐지 결과 조회"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        communities = await service._detect_communities(kg_id)
        
        # 최소 크기 필터링
        filtered_communities = [c for c in communities if c.size >= min_size]
        
        return [
            CommunityResponse(
                id=community.id,
                entities=community.entities,
                size=community.size,
                density=community.density,
                modularity=community.modularity,
                dominant_types=community.dominant_types,
                key_relationships=community.key_relationships,
            )
            for community in filtered_communities[:limit]
        ]
        
    except Exception as e:
        logger.error(f"Error detecting communities for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to detect communities")


@router.get("/{kg_id}/patterns", response_model=List[KnowledgePatternResponse])
async def get_knowledge_patterns(
    kg_id: str,
    pattern_type: Optional[str] = Query(default=None),
    min_confidence: float = Query(default=0.5, ge=0.0, le=1.0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """지식 패턴 조회"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        patterns = await service._discover_knowledge_patterns(kg_id)
        
        # 필터링
        filtered_patterns = [
            p for p in patterns 
            if p.confidence >= min_confidence and 
            (pattern_type is None or p.pattern_type == pattern_type)
        ]
        
        return [
            KnowledgePatternResponse(
                pattern_type=pattern.pattern_type,
                description=pattern.description,
                entities=pattern.entities,
                relationships=pattern.relationships,
                confidence=pattern.confidence,
                frequency=pattern.frequency,
                examples=pattern.examples,
            )
            for pattern in filtered_patterns
        ]
        
    except Exception as e:
        logger.error(f"Error discovering patterns for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to discover patterns")


@router.get("/{kg_id}/temporal-analysis")
async def get_temporal_analysis(
    kg_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """시간적 패턴 분석 조회"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        temporal_analysis = await service._analyze_temporal_patterns(kg_id)
        
        return temporal_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing temporal patterns for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze temporal patterns")


@router.get("/{kg_id}/recommendations")
async def get_recommendations(
    kg_id: str,
    priority: Optional[str] = Query(default=None, regex="^(high|medium|low)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """분석 기반 추천사항 조회"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        
        # 간단한 분석 수행 (캐시된 결과 사용 가능)
        analysis_results = await service.analyze_knowledge_graph(
            kg_id=kg_id,
            include_centrality=False,
            include_communities=False,
            include_patterns=False,
            include_temporal=False,
        )
        
        recommendations = analysis_results.get("recommendations", [])
        
        # 우선순위 필터링
        if priority:
            recommendations = [r for r in recommendations if r.get("priority") == priority]
        
        return {"recommendations": recommendations}
        
    except Exception as e:
        logger.error(f"Error generating recommendations for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/{kg_id}/insights")
async def get_insights_summary(
    kg_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """지식 그래프 인사이트 요약"""
    
    # 권한 확인
    kg = db.query(KnowledgeGraph).filter(
        KnowledgeGraph.id == kg_id,
        KnowledgeGraph.user_id == current_user.id
    ).first()
    
    if not kg:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")
    
    try:
        service = KGAnalyticsService(db)
        
        # 기본 메트릭
        network_metrics = await service._calculate_network_metrics(kg_id)
        
        # 중심성 상위 3개
        centrality_metrics = await service._calculate_centrality_metrics(kg_id)
        top_entities = centrality_metrics[:3] if centrality_metrics else []
        
        # 커뮤니티 수
        communities = await service._detect_communities(kg_id)
        
        # 패턴 수
        patterns = await service._discover_knowledge_patterns(kg_id)
        
        return {
            "summary": {
                "total_entities": network_metrics.node_count,
                "total_relationships": network_metrics.edge_count,
                "network_density": round(network_metrics.density, 3),
                "connected_components": network_metrics.connected_components,
                "communities_found": len(communities),
                "patterns_discovered": len(patterns),
            },
            "key_entities": [
                {
                    "name": entity.entity_name,
                    "pagerank": round(entity.pagerank, 3),
                    "degree_centrality": round(entity.degree_centrality, 3),
                }
                for entity in top_entities
            ],
            "largest_communities": [
                {
                    "id": community.id,
                    "size": community.size,
                    "dominant_types": community.dominant_types[:2],
                }
                for community in communities[:3]
            ],
            "discovered_patterns": [
                {
                    "type": pattern.pattern_type,
                    "description": pattern.description,
                    "confidence": round(pattern.confidence, 2),
                }
                for pattern in patterns
            ],
        }
        
    except Exception as e:
        logger.error(f"Error generating insights for {kg_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")


async def _save_analysis_results(
    db: Session,
    kg_id: str,
    analysis_results: Dict[str, Any]
):
    """분석 결과를 데이터베이스에 저장 (백그라운드 작업)"""
    
    try:
        # 실제 구현에서는 분석 결과를 별도 테이블에 저장
        # 여기서는 로그만 남김
        logger.info(f"Analysis results saved for KG {kg_id}")
        
    except Exception as e:
        logger.error(f"Error saving analysis results for {kg_id}: {str(e)}")


@router.get("/pattern-types")
async def get_pattern_types():
    """사용 가능한 패턴 타입 목록 조회"""
    
    return {
        "pattern_types": [
            {
                "value": "hub",
                "label": "허브 패턴",
                "description": "높은 연결도를 가진 중심 엔티티들"
            },
            {
                "value": "bridge",
                "label": "브리지 패턴", 
                "description": "서로 다른 클러스터를 연결하는 엔티티들"
            },
            {
                "value": "hierarchy",
                "label": "계층 구조",
                "description": "is_a, part_of 관계로 형성된 계층"
            },
            {
                "value": "cycle",
                "label": "순환 관계",
                "description": "순환적 관계 구조"
            },
            {
                "value": "homophily",
                "label": "동질성 클러스터",
                "description": "같은 타입 엔티티들의 밀집 영역"
            },
        ]
    }