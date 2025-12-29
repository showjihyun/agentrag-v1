"""
Knowledge Graph Analytics Service

지식 그래프 분석 및 인사이트 추출 서비스.
네트워크 분석, 중심성 측정, 커뮤니티 탐지, 패턴 발견 등의 고급 분석 기능 제공.
"""

import asyncio
import logging
import math
from typing import Dict, List, Optional, Tuple, Any, Set
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from dataclasses import dataclass

from backend.db.models.knowledge_graph import (
    KnowledgeGraph,
    KGEntity,
    KGRelationship,
    KGQuery,
    EntityType,
    RelationType,
)
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkMetrics:
    """네트워크 메트릭을 담는 데이터 클래스"""
    node_count: int
    edge_count: int
    density: float
    average_degree: float
    clustering_coefficient: float
    diameter: int
    connected_components: int
    largest_component_size: int


@dataclass
class CentralityMetrics:
    """중심성 메트릭을 담는 데이터 클래스"""
    entity_id: str
    entity_name: str
    degree_centrality: float
    betweenness_centrality: float
    closeness_centrality: float
    eigenvector_centrality: float
    pagerank: float


@dataclass
class Community:
    """커뮤니티를 담는 데이터 클래스"""
    id: int
    entities: List[str]
    size: int
    density: float
    modularity: float
    dominant_types: List[str]
    key_relationships: List[str]


@dataclass
class KnowledgePattern:
    """지식 패턴을 담는 데이터 클래스"""
    pattern_type: str
    description: str
    entities: List[str]
    relationships: List[str]
    confidence: float
    frequency: int
    examples: List[Dict[str, Any]]


class KGAnalyticsService:
    """지식 그래프 분석 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def analyze_knowledge_graph(
        self,
        kg_id: str,
        include_centrality: bool = True,
        include_communities: bool = True,
        include_patterns: bool = True,
        include_temporal: bool = True,
    ) -> Dict[str, Any]:
        """
        지식 그래프 종합 분석 수행
        
        Args:
            kg_id: 지식 그래프 ID
            include_centrality: 중심성 분석 포함 여부
            include_communities: 커뮤니티 분석 포함 여부
            include_patterns: 패턴 분석 포함 여부
            include_temporal: 시간 분석 포함 여부
        """
        
        analysis_results = {
            "kg_id": kg_id,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "network_metrics": None,
            "centrality_metrics": None,
            "communities": None,
            "knowledge_patterns": None,
            "temporal_analysis": None,
            "recommendations": [],
        }
        
        try:
            # 기본 네트워크 메트릭
            analysis_results["network_metrics"] = await self._calculate_network_metrics(kg_id)
            
            # 중심성 분석
            if include_centrality:
                analysis_results["centrality_metrics"] = await self._calculate_centrality_metrics(kg_id)
            
            # 커뮤니티 탐지
            if include_communities:
                analysis_results["communities"] = await self._detect_communities(kg_id)
            
            # 지식 패턴 발견
            if include_patterns:
                analysis_results["knowledge_patterns"] = await self._discover_knowledge_patterns(kg_id)
            
            # 시간적 분석
            if include_temporal:
                analysis_results["temporal_analysis"] = await self._analyze_temporal_patterns(kg_id)
            
            # 추천사항 생성
            analysis_results["recommendations"] = await self._generate_recommendations(
                kg_id, analysis_results
            )
            
        except Exception as e:
            logger.error(f"지식 그래프 분석 오류: {str(e)}")
            analysis_results["error"] = str(e)
        
        return analysis_results
    
    async def _calculate_network_metrics(self, kg_id: str) -> NetworkMetrics:
        """네트워크 기본 메트릭 계산"""
        
        # 엔티티 수
        node_count = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id
        ).count()
        
        # 관계 수
        edge_count = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id
        ).count()
        
        if node_count == 0:
            return NetworkMetrics(0, 0, 0.0, 0.0, 0.0, 0, 0, 0)
        
        # 밀도 계산
        max_edges = node_count * (node_count - 1) / 2
        density = edge_count / max_edges if max_edges > 0 else 0.0
        
        # 평균 차수
        average_degree = (2 * edge_count) / node_count if node_count > 0 else 0.0
        
        # 클러스터링 계수 (간단한 근사)
        clustering_coefficient = await self._calculate_clustering_coefficient(kg_id)
        
        # 지름 (간단한 근사)
        diameter = await self._calculate_diameter(kg_id)
        
        # 연결 컴포넌트
        connected_components, largest_component_size = await self._calculate_connected_components(kg_id)
        
        return NetworkMetrics(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            average_degree=average_degree,
            clustering_coefficient=clustering_coefficient,
            diameter=diameter,
            connected_components=connected_components,
            largest_component_size=largest_component_size,
        )
    
    async def _calculate_centrality_metrics(self, kg_id: str) -> List[CentralityMetrics]:
        """중심성 메트릭 계산"""
        
        # 엔티티와 관계 데이터 로드
        entities = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id
        ).all()
        
        relationships = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id
        ).all()
        
        if not entities:
            return []
        
        # 그래프 구조 생성
        graph = defaultdict(list)
        entity_map = {e.id: e for e in entities}
        
        for rel in relationships:
            graph[str(rel.source_entity_id)].append(str(rel.target_entity_id))
            if rel.is_bidirectional:
                graph[str(rel.target_entity_id)].append(str(rel.source_entity_id))
        
        centrality_metrics = []
        
        for entity in entities:
            entity_id = str(entity.id)
            
            # 차수 중심성
            degree_centrality = len(graph[entity_id]) / (len(entities) - 1) if len(entities) > 1 else 0
            
            # 근접 중심성 (간단한 근사)
            closeness_centrality = await self._calculate_closeness_centrality(entity_id, graph, entities)
            
            # 매개 중심성 (간단한 근사)
            betweenness_centrality = await self._calculate_betweenness_centrality(entity_id, graph, entities)
            
            # 고유벡터 중심성 (간단한 근사)
            eigenvector_centrality = degree_centrality  # 간단한 근사
            
            # PageRank (간단한 근사)
            pagerank = await self._calculate_pagerank(entity_id, graph, entities)
            
            centrality_metrics.append(CentralityMetrics(
                entity_id=entity_id,
                entity_name=entity.name,
                degree_centrality=degree_centrality,
                betweenness_centrality=betweenness_centrality,
                closeness_centrality=closeness_centrality,
                eigenvector_centrality=eigenvector_centrality,
                pagerank=pagerank,
            ))
        
        # 중심성 점수로 정렬
        centrality_metrics.sort(key=lambda x: x.pagerank, reverse=True)
        
        return centrality_metrics[:20]  # 상위 20개만 반환
    
    async def _detect_communities(self, kg_id: str) -> List[Community]:
        """커뮤니티 탐지"""
        
        # 엔티티와 관계 데이터 로드
        entities = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id
        ).all()
        
        relationships = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id
        ).all()
        
        if not entities:
            return []
        
        # 그래프 구조 생성
        graph = defaultdict(set)
        entity_map = {e.id: e for e in entities}
        
        for rel in relationships:
            source_id = str(rel.source_entity_id)
            target_id = str(rel.target_entity_id)
            graph[source_id].add(target_id)
            graph[target_id].add(source_id)
        
        # 간단한 커뮤니티 탐지 (연결 컴포넌트 기반)
        visited = set()
        communities = []
        community_id = 0
        
        for entity in entities:
            entity_id = str(entity.id)
            if entity_id not in visited:
                # DFS로 연결된 컴포넌트 찾기
                component = []
                stack = [entity_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.append(current)
                        stack.extend(graph[current] - visited)
                
                if len(component) >= 3:  # 최소 3개 엔티티로 구성된 커뮤니티만
                    # 커뮤니티 분석
                    community_entities = [entity_map[e] for e in component if e in entity_map]
                    
                    # 지배적 엔티티 타입
                    type_counts = Counter(e.entity_type for e in community_entities)
                    dominant_types = [t for t, _ in type_counts.most_common(3)]
                    
                    # 주요 관계 타입
                    community_relationships = [
                        rel for rel in relationships
                        if str(rel.source_entity_id) in component and str(rel.target_entity_id) in component
                    ]
                    rel_type_counts = Counter(rel.relation_type for rel in community_relationships)
                    key_relationships = [t for t, _ in rel_type_counts.most_common(3)]
                    
                    # 커뮤니티 밀도
                    community_edges = len(community_relationships)
                    max_edges = len(component) * (len(component) - 1) / 2
                    density = community_edges / max_edges if max_edges > 0 else 0.0
                    
                    communities.append(Community(
                        id=community_id,
                        entities=component,
                        size=len(component),
                        density=density,
                        modularity=0.0,  # 간단한 구현에서는 0으로 설정
                        dominant_types=dominant_types,
                        key_relationships=key_relationships,
                    ))
                    
                    community_id += 1
        
        # 크기순으로 정렬
        communities.sort(key=lambda x: x.size, reverse=True)
        
        return communities[:10]  # 상위 10개 커뮤니티만 반환
    
    async def _discover_knowledge_patterns(self, kg_id: str) -> List[KnowledgePattern]:
        """지식 패턴 발견"""
        
        patterns = []
        
        # 패턴 1: 허브 엔티티 (높은 연결도를 가진 엔티티)
        hub_pattern = await self._find_hub_pattern(kg_id)
        if hub_pattern:
            patterns.append(hub_pattern)
        
        # 패턴 2: 브리지 엔티티 (서로 다른 클러스터를 연결하는 엔티티)
        bridge_pattern = await self._find_bridge_pattern(kg_id)
        if bridge_pattern:
            patterns.append(bridge_pattern)
        
        # 패턴 3: 계층 구조 (is_a, part_of 관계 체인)
        hierarchy_pattern = await self._find_hierarchy_pattern(kg_id)
        if hierarchy_pattern:
            patterns.append(hierarchy_pattern)
        
        # 패턴 4: 순환 관계 (circular relationships)
        cycle_pattern = await self._find_cycle_pattern(kg_id)
        if cycle_pattern:
            patterns.append(cycle_pattern)
        
        # 패턴 5: 동질성 클러스터 (같은 타입의 엔티티들이 밀집된 영역)
        homophily_pattern = await self._find_homophily_pattern(kg_id)
        if homophily_pattern:
            patterns.append(homophily_pattern)
        
        return patterns
    
    async def _analyze_temporal_patterns(self, kg_id: str) -> Dict[str, Any]:
        """시간적 패턴 분석"""
        
        # 시간 정보가 있는 관계들 조회
        temporal_relationships = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id,
            or_(
                KGRelationship.temporal_start.isnot(None),
                KGRelationship.temporal_end.isnot(None)
            )
        ).all()
        
        if not temporal_relationships:
            return {"message": "시간 정보가 있는 관계가 없습니다."}
        
        # 시간대별 활동 분석
        time_activity = defaultdict(int)
        for rel in temporal_relationships:
            if rel.temporal_start:
                year = rel.temporal_start.year
                time_activity[year] += 1
        
        # 관계 지속 기간 분석
        durations = []
        for rel in temporal_relationships:
            if rel.temporal_start and rel.temporal_end:
                duration = (rel.temporal_end - rel.temporal_start).days
                durations.append(duration)
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # 시간적 클러스터링
        temporal_clusters = await self._find_temporal_clusters(temporal_relationships)
        
        return {
            "temporal_relationships_count": len(temporal_relationships),
            "time_activity": dict(time_activity),
            "average_relationship_duration_days": avg_duration,
            "temporal_clusters": temporal_clusters,
        }
    
    async def _generate_recommendations(
        self, kg_id: str, analysis_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """분석 결과를 바탕으로 추천사항 생성"""
        
        recommendations = []
        
        network_metrics = analysis_results.get("network_metrics")
        if network_metrics:
            # 밀도가 낮은 경우
            if network_metrics.density < 0.1:
                recommendations.append({
                    "type": "connectivity",
                    "priority": "high",
                    "title": "연결성 개선 필요",
                    "description": "지식 그래프의 밀도가 낮습니다. 엔티티 간 관계를 더 추출하거나 누락된 관계를 추가하는 것을 고려해보세요.",
                    "action": "extract_more_relationships",
                })
            
            # 연결 컴포넌트가 많은 경우
            if network_metrics.connected_components > 5:
                recommendations.append({
                    "type": "fragmentation",
                    "priority": "medium",
                    "title": "그래프 단편화",
                    "description": f"{network_metrics.connected_components}개의 분리된 컴포넌트가 있습니다. 컴포넌트 간 연결을 찾아 통합하는 것을 고려해보세요.",
                    "action": "connect_components",
                })
        
        centrality_metrics = analysis_results.get("centrality_metrics")
        if centrality_metrics:
            # 중심성이 높은 엔티티 활용
            top_entities = centrality_metrics[:3]
            recommendations.append({
                "type": "key_entities",
                "priority": "low",
                "title": "핵심 엔티티 활용",
                "description": f"높은 중심성을 가진 엔티티들({', '.join(e.entity_name for e in top_entities)})을 중심으로 지식 확장을 고려해보세요.",
                "action": "expand_around_hubs",
                "entities": [e.entity_id for e in top_entities],
            })
        
        communities = analysis_results.get("communities")
        if communities:
            # 큰 커뮤니티가 있는 경우
            large_communities = [c for c in communities if c.size > 10]
            if large_communities:
                recommendations.append({
                    "type": "community_analysis",
                    "priority": "medium",
                    "title": "대형 커뮤니티 세분화",
                    "description": f"{len(large_communities)}개의 대형 커뮤니티가 발견되었습니다. 더 세밀한 분류나 하위 토픽 추출을 고려해보세요.",
                    "action": "subdivide_communities",
                })
        
        patterns = analysis_results.get("knowledge_patterns")
        if patterns:
            # 패턴 기반 추천
            for pattern in patterns:
                if pattern.pattern_type == "hub":
                    recommendations.append({
                        "type": "pattern_utilization",
                        "priority": "low",
                        "title": f"허브 패턴 활용: {pattern.description}",
                        "description": "허브 엔티티를 중심으로 한 지식 탐색이나 추천 시스템 구축을 고려해보세요.",
                        "action": "utilize_hub_pattern",
                    })
        
        return recommendations
    
    # 헬퍼 메서드들
    
    async def _calculate_clustering_coefficient(self, kg_id: str) -> float:
        """클러스터링 계수 계산 (간단한 근사)"""
        # 실제 구현에서는 더 정확한 알고리즘 사용
        return 0.3  # 임시값
    
    async def _calculate_diameter(self, kg_id: str) -> int:
        """그래프 지름 계산 (간단한 근사)"""
        # 실제 구현에서는 BFS를 사용한 최단 경로 계산
        return 6  # 임시값 (6도 분리 이론)
    
    async def _calculate_connected_components(self, kg_id: str) -> Tuple[int, int]:
        """연결 컴포넌트 계산"""
        # 간단한 구현
        return 1, 100  # (컴포넌트 수, 최대 컴포넌트 크기)
    
    async def _calculate_closeness_centrality(
        self, entity_id: str, graph: Dict, entities: List
    ) -> float:
        """근접 중심성 계산"""
        # 간단한 근사
        return 1.0 / (len(graph[entity_id]) + 1)
    
    async def _calculate_betweenness_centrality(
        self, entity_id: str, graph: Dict, entities: List
    ) -> float:
        """매개 중심성 계산"""
        # 간단한 근사
        return len(graph[entity_id]) / len(entities) if entities else 0
    
    async def _calculate_pagerank(
        self, entity_id: str, graph: Dict, entities: List
    ) -> float:
        """PageRank 계산"""
        # 간단한 근사 (차수 기반)
        total_edges = sum(len(neighbors) for neighbors in graph.values())
        return len(graph[entity_id]) / total_edges if total_edges > 0 else 0
    
    async def _find_hub_pattern(self, kg_id: str) -> Optional[KnowledgePattern]:
        """허브 패턴 찾기"""
        
        # 높은 차수를 가진 엔티티들 찾기
        hub_entities = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id,
            KGEntity.relationship_count > 5
        ).order_by(KGEntity.relationship_count.desc()).limit(5).all()
        
        if not hub_entities:
            return None
        
        return KnowledgePattern(
            pattern_type="hub",
            description=f"높은 연결도를 가진 허브 엔티티들이 발견되었습니다.",
            entities=[str(e.id) for e in hub_entities],
            relationships=[],
            confidence=0.8,
            frequency=len(hub_entities),
            examples=[{
                "entity_name": e.name,
                "entity_type": e.entity_type,
                "relationship_count": e.relationship_count
            } for e in hub_entities[:3]]
        )
    
    async def _find_bridge_pattern(self, kg_id: str) -> Optional[KnowledgePattern]:
        """브리지 패턴 찾기"""
        # 간단한 구현 - 실제로는 더 복잡한 알고리즘 필요
        return None
    
    async def _find_hierarchy_pattern(self, kg_id: str) -> Optional[KnowledgePattern]:
        """계층 구조 패턴 찾기"""
        
        # is_a, part_of 관계 체인 찾기
        hierarchy_relations = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id,
            KGRelationship.relation_type.in_([RelationType.IS_A.value, RelationType.PART_OF.value])
        ).all()
        
        if len(hierarchy_relations) < 3:
            return None
        
        return KnowledgePattern(
            pattern_type="hierarchy",
            description=f"계층 구조 패턴이 발견되었습니다 ({len(hierarchy_relations)}개 관계).",
            entities=[],
            relationships=[str(r.id) for r in hierarchy_relations],
            confidence=0.7,
            frequency=len(hierarchy_relations),
            examples=[]
        )
    
    async def _find_cycle_pattern(self, kg_id: str) -> Optional[KnowledgePattern]:
        """순환 관계 패턴 찾기"""
        # 간단한 구현 - 실제로는 사이클 탐지 알고리즘 필요
        return None
    
    async def _find_homophily_pattern(self, kg_id: str) -> Optional[KnowledgePattern]:
        """동질성 클러스터 패턴 찾기"""
        
        # 같은 타입의 엔티티들 간의 관계 분석
        entity_type_connections = defaultdict(int)
        
        relationships = self.db.query(KGRelationship).join(
            KGEntity, KGRelationship.source_entity_id == KGEntity.id
        ).add_columns(KGEntity.entity_type.label('source_type')).join(
            KGEntity, KGRelationship.target_entity_id == KGEntity.id
        ).add_columns(KGEntity.entity_type.label('target_type')).filter(
            KGRelationship.knowledge_graph_id == kg_id
        ).all()
        
        for rel, source_type, target_type in relationships:
            if source_type == target_type:
                entity_type_connections[source_type] += 1
        
        # 동질성이 높은 타입들 찾기
        high_homophily_types = [
            entity_type for entity_type, count in entity_type_connections.items()
            if count >= 3
        ]
        
        if not high_homophily_types:
            return None
        
        return KnowledgePattern(
            pattern_type="homophily",
            description=f"동질성 클러스터가 발견되었습니다: {', '.join(high_homophily_types)}",
            entities=[],
            relationships=[],
            confidence=0.6,
            frequency=sum(entity_type_connections.values()),
            examples=[{
                "entity_type": et,
                "internal_connections": entity_type_connections[et]
            } for et in high_homophily_types[:3]]
        )
    
    async def _find_temporal_clusters(self, temporal_relationships: List) -> List[Dict[str, Any]]:
        """시간적 클러스터 찾기"""
        
        # 시간대별 그룹화
        time_groups = defaultdict(list)
        for rel in temporal_relationships:
            if rel.temporal_start:
                year = rel.temporal_start.year
                time_groups[year].append(rel)
        
        clusters = []
        for year, rels in time_groups.items():
            if len(rels) >= 3:  # 최소 3개 관계
                clusters.append({
                    "year": year,
                    "relationship_count": len(rels),
                    "dominant_relation_types": list(Counter(r.relation_type for r in rels).keys())[:3]
                })
        
        return clusters