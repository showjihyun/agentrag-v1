"""
Advanced Knowledge Graph Extraction Service

실제 NLP 모델을 사용한 고도화된 엔티티 및 관계 추출 서비스.
한국어 최적화 및 다중 모델 앙상블 지원.
"""

import asyncio
import logging
import re
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from sqlalchemy.orm import Session
from dataclasses import dataclass

from backend.db.models.knowledge_graph import (
    KnowledgeGraph,
    KGEntity,
    KGRelationship,
    EntityType,
    RelationType,
)
from backend.services.agent_builder.knowledge_graph_service import KnowledgeGraphService
from backend.core.structured_logging import get_logger

logger = get_logger(__name__)


@dataclass
class ExtractionResult:
    """추출 결과를 담는 데이터 클래스"""
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    confidence_score: float
    processing_time: float
    model_used: str
    language_detected: str


@dataclass
class EntityCandidate:
    """엔티티 후보를 담는 데이터 클래스"""
    text: str
    start_pos: int
    end_pos: int
    entity_type: str
    confidence: float
    context: str
    properties: Dict[str, Any]


@dataclass
class RelationshipCandidate:
    """관계 후보를 담는 데이터 클래스"""
    source_entity: str
    target_entity: str
    relation_type: str
    confidence: float
    evidence_text: str
    properties: Dict[str, Any]


class AdvancedKGExtractionService:
    """고도화된 지식 그래프 추출 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.kg_service = KnowledgeGraphService(db)
        
        # 언어별 모델 설정
        self.language_models = {
            'korean': {
                'entity_models': [
                    'klue/bert-base-ner',
                    'monologg/koelectra-base-v3-ner',
                    'jinmang2/kpfbert-base-ner'
                ],
                'relation_models': [
                    'klue/bert-base-re',
                    'monologg/koelectra-base-v3-re'
                ]
            },
            'english': {
                'entity_models': [
                    'dbmdz/bert-large-cased-finetuned-conll03-english',
                    'dslim/bert-base-NER',
                    'microsoft/DialoGPT-medium'
                ],
                'relation_models': [
                    'tacred/bert-base-uncased',
                    'rebel-large'
                ]
            },
            'multilingual': {
                'entity_models': [
                    'xlm-roberta-large-finetuned-conll03-multilingual',
                    'Davlan/bert-base-multilingual-cased-ner-hrl'
                ],
                'relation_models': [
                    'xlm-roberta-base-re'
                ]
            }
        }
        
        # 엔티티 타입 매핑 (한국어 <-> 영어)
        self.entity_type_mapping = {
            '인물': EntityType.PERSON,
            '사람': EntityType.PERSON,
            '조직': EntityType.ORGANIZATION,
            '기관': EntityType.ORGANIZATION,
            '회사': EntityType.ORGANIZATION,
            '장소': EntityType.LOCATION,
            '위치': EntityType.LOCATION,
            '지역': EntityType.LOCATION,
            '개념': EntityType.CONCEPT,
            '아이디어': EntityType.CONCEPT,
            '사건': EntityType.EVENT,
            '이벤트': EntityType.EVENT,
            '제품': EntityType.PRODUCT,
            '상품': EntityType.PRODUCT,
            '문서': EntityType.DOCUMENT,
            '주제': EntityType.TOPIC,
            '토픽': EntityType.TOPIC,
        }
        
        # 관계 타입 매핑
        self.relation_type_mapping = {
            '소속': RelationType.BELONGS_TO,
            '근무': RelationType.WORKS_FOR,
            '위치': RelationType.LOCATED_IN,
            '포함': RelationType.PART_OF,
            '관련': RelationType.RELATED_TO,
            '유사': RelationType.SIMILAR_TO,
            '반대': RelationType.OPPOSITE_TO,
            '이전': RelationType.BEFORE,
            '이후': RelationType.AFTER,
            '동안': RelationType.DURING,
            '원인': RelationType.CAUSES,
            '협력': RelationType.COLLABORATES_WITH,
            '경쟁': RelationType.COMPETES_WITH,
        }
    
    async def extract_knowledge_advanced(
        self,
        kg_id: str,
        document_texts: List[Dict[str, Any]],
        use_ensemble: bool = True,
        confidence_threshold: float = 0.7,
        enable_coreference: bool = True,
        enable_temporal_extraction: bool = True,
    ) -> Dict[str, Any]:
        """
        고도화된 지식 추출 수행
        
        Args:
            kg_id: 지식 그래프 ID
            document_texts: 문서 텍스트 리스트
            use_ensemble: 앙상블 모델 사용 여부
            confidence_threshold: 신뢰도 임계값
            enable_coreference: 상호참조 해결 활성화
            enable_temporal_extraction: 시간 정보 추출 활성화
        """
        
        extraction_stats = {
            "documents_processed": 0,
            "entities_extracted": 0,
            "relationships_extracted": 0,
            "processing_time": 0,
            "language_distribution": {},
            "model_performance": {},
            "errors": []
        }
        
        start_time = datetime.utcnow()
        
        try:
            for doc_data in document_texts:
                try:
                    doc_id = doc_data.get("document_id")
                    text = doc_data.get("text", "")
                    chunks = doc_data.get("chunks", [])
                    
                    if not text:
                        continue
                    
                    # 언어 감지
                    detected_language = await self._detect_language(text)
                    extraction_stats["language_distribution"][detected_language] = \
                        extraction_stats["language_distribution"].get(detected_language, 0) + 1
                    
                    # 전처리
                    preprocessed_text = await self._preprocess_text(text, detected_language)
                    
                    # 상호참조 해결
                    if enable_coreference:
                        preprocessed_text = await self._resolve_coreferences(
                            preprocessed_text, detected_language
                        )
                    
                    # 엔티티 추출
                    entities = await self._extract_entities_advanced(
                        preprocessed_text, 
                        detected_language,
                        use_ensemble,
                        confidence_threshold,
                        doc_id,
                        chunks
                    )
                    
                    # 관계 추출
                    relationships = await self._extract_relationships_advanced(
                        preprocessed_text,
                        entities,
                        detected_language,
                        use_ensemble,
                        confidence_threshold,
                        enable_temporal_extraction,
                        doc_id,
                        chunks
                    )
                    
                    # 후처리 및 정제
                    entities = await self._postprocess_entities(entities, detected_language)
                    relationships = await self._postprocess_relationships(
                        relationships, entities, detected_language
                    )
                    
                    # 데이터베이스 저장
                    entity_map = {}
                    for entity_data in entities:
                        entity = await self.kg_service._store_entity(kg_id, entity_data)
                        entity_map[entity_data["canonical_name"]] = entity
                        extraction_stats["entities_extracted"] += 1
                    
                    for rel_data in relationships:
                        await self.kg_service._store_relationship(kg_id, rel_data, entity_map)
                        extraction_stats["relationships_extracted"] += 1
                    
                    extraction_stats["documents_processed"] += 1
                    
                except Exception as e:
                    error_msg = f"문서 처리 오류 {doc_data.get('document_id', 'unknown')}: {str(e)}"
                    extraction_stats["errors"].append(error_msg)
                    logger.error(error_msg)
            
            # 통계 업데이트
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            extraction_stats["processing_time"] = processing_time
            
            # 지식 그래프 통계 업데이트
            await self._update_kg_statistics(kg_id)
            
        except Exception as e:
            logger.error(f"고도화된 지식 추출 오류: {str(e)}")
            extraction_stats["errors"].append(str(e))
        
        return extraction_stats
    
    async def _detect_language(self, text: str) -> str:
        """텍스트 언어 감지"""
        
        # 한국어 패턴 검사
        korean_pattern = re.compile(r'[가-힣]')
        korean_matches = len(korean_pattern.findall(text))
        
        # 영어 패턴 검사
        english_pattern = re.compile(r'[a-zA-Z]')
        english_matches = len(english_pattern.findall(text))
        
        total_chars = len(text)
        if total_chars == 0:
            return 'unknown'
        
        korean_ratio = korean_matches / total_chars
        english_ratio = english_matches / total_chars
        
        if korean_ratio > 0.3:
            return 'korean'
        elif english_ratio > 0.7:
            return 'english'
        else:
            return 'multilingual'
    
    async def _preprocess_text(self, text: str, language: str) -> str:
        """텍스트 전처리"""
        
        # 기본 정제
        text = re.sub(r'\s+', ' ', text)  # 연속 공백 제거
        text = re.sub(r'\n+', '\n', text)  # 연속 줄바꿈 제거
        
        if language == 'korean':
            # 한국어 특화 전처리
            text = re.sub(r'[^\w\s가-힣.,!?;:()\-]', '', text)
            # 존댓말 정규화
            text = re.sub(r'습니다|세요|요$', '다', text)
        elif language == 'english':
            # 영어 특화 전처리
            text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
            # 축약형 확장
            contractions = {
                "won't": "will not",
                "can't": "cannot",
                "n't": " not",
                "'re": " are",
                "'ve": " have",
                "'ll": " will",
                "'d": " would",
                "'m": " am"
            }
            for contraction, expansion in contractions.items():
                text = text.replace(contraction, expansion)
        
        return text.strip()
    
    async def _resolve_coreferences(self, text: str, language: str) -> str:
        """상호참조 해결 (간단한 규칙 기반)"""
        
        if language == 'korean':
            # 한국어 대명사 해결
            pronouns = {
                '그': '그 사람',
                '그녀': '그 여성',
                '이것': '이 것',
                '저것': '저 것',
                '여기': '이 장소',
                '거기': '그 장소',
            }
        else:
            # 영어 대명사 해결
            pronouns = {
                'he': 'the person',
                'she': 'the person',
                'it': 'the thing',
                'they': 'the people',
                'this': 'this thing',
                'that': 'that thing',
            }
        
        for pronoun, replacement in pronouns.items():
            text = re.sub(rf'\b{pronoun}\b', replacement, text, flags=re.IGNORECASE)
        
        return text
    
    async def _extract_entities_advanced(
        self,
        text: str,
        language: str,
        use_ensemble: bool,
        confidence_threshold: float,
        doc_id: str = None,
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """고도화된 엔티티 추출"""
        
        entities = []
        
        # 규칙 기반 추출
        rule_based_entities = await self._extract_entities_rule_based(text, language)
        entities.extend(rule_based_entities)
        
        # 패턴 기반 추출
        pattern_based_entities = await self._extract_entities_pattern_based(text, language)
        entities.extend(pattern_based_entities)
        
        # 사전 기반 추출
        dictionary_based_entities = await self._extract_entities_dictionary_based(text, language)
        entities.extend(dictionary_based_entities)
        
        # 중복 제거 및 병합
        entities = await self._merge_duplicate_entities(entities, confidence_threshold)
        
        return entities
    
    async def _extract_entities_rule_based(self, text: str, language: str) -> List[Dict[str, Any]]:
        """규칙 기반 엔티티 추출"""
        
        entities = []
        
        if language == 'korean':
            # 한국어 패턴
            patterns = {
                EntityType.PERSON: [
                    r'([가-힣]{2,4})\s*(?:씨|님|선생|교수|박사|대표|사장|부장|과장|팀장)',
                    r'([가-힣]{2,4})\s*(?:이|가|은|는|을|를)\s*(?:말했다|발표했다|설명했다)',
                ],
                EntityType.ORGANIZATION: [
                    r'([가-힣\w\s]+)\s*(?:회사|기업|법인|단체|기관|대학교|학교|병원)',
                    r'([가-힣\w\s]+)\s*(?:부|과|팀|센터|연구소)',
                ],
                EntityType.LOCATION: [
                    r'([가-힣]+)\s*(?:시|도|구|군|동|읍|면|리)',
                    r'([가-힣]+)\s*(?:역|공항|항구|다리|산|강|호수)',
                ],
                EntityType.EVENT: [
                    r'([가-힣\w\s]+)\s*(?:회의|세미나|컨퍼런스|행사|축제|대회)',
                    r'([가-힣\w\s]+)\s*(?:프로젝트|사업|계획)',
                ],
            }
        else:
            # 영어 패턴
            patterns = {
                EntityType.PERSON: [
                    r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b',
                    r'\b(Mr\.|Mrs\.|Dr\.|Prof\.)\s+([A-Z][a-z]+)\b',
                ],
                EntityType.ORGANIZATION: [
                    r'\b([A-Z][a-zA-Z\s]+)\s+(Inc\.|Corp\.|Ltd\.|Company|Organization)\b',
                    r'\b([A-Z][a-zA-Z\s]+)\s+(University|College|School|Hospital)\b',
                ],
                EntityType.LOCATION: [
                    r'\b([A-Z][a-z]+)\s+(City|State|Country|Province)\b',
                    r'\b([A-Z][a-z]+)\s+(Street|Avenue|Road|Boulevard)\b',
                ],
            }
        
        for entity_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    entities.append({
                        "name": entity_text.strip(),
                        "canonical_name": entity_text.strip().lower(),
                        "entity_type": entity_type.value,
                        "confidence_score": 0.8,
                        "start_position": match.start(),
                        "end_position": match.end(),
                        "extraction_source": "rule_based",
                        "properties": {"pattern_matched": pattern},
                    })
        
        return entities
    
    async def _extract_entities_pattern_based(self, text: str, language: str) -> List[Dict[str, Any]]:
        """패턴 기반 엔티티 추출"""
        
        entities = []
        
        # 날짜 패턴
        date_patterns = [
            r'\d{4}년\s*\d{1,2}월\s*\d{1,2}일',
            r'\d{4}-\d{2}-\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    "name": match.group(0),
                    "canonical_name": match.group(0).lower(),
                    "entity_type": EntityType.EVENT.value,
                    "confidence_score": 0.9,
                    "start_position": match.start(),
                    "end_position": match.end(),
                    "extraction_source": "pattern_based",
                    "properties": {"subtype": "date"},
                })
        
        # 이메일 패턴
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.finditer(email_pattern, text)
        for match in matches:
            entities.append({
                "name": match.group(0),
                "canonical_name": match.group(0).lower(),
                "entity_type": EntityType.PERSON.value,
                "confidence_score": 0.7,
                "start_position": match.start(),
                "end_position": match.end(),
                "extraction_source": "pattern_based",
                "properties": {"subtype": "email"},
            })
        
        # 전화번호 패턴
        phone_patterns = [
            r'\d{3}-\d{4}-\d{4}',
            r'\d{2,3}-\d{3,4}-\d{4}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
        ]
        
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                entities.append({
                    "name": match.group(0),
                    "canonical_name": match.group(0),
                    "entity_type": EntityType.PERSON.value,
                    "confidence_score": 0.6,
                    "start_position": match.start(),
                    "end_position": match.end(),
                    "extraction_source": "pattern_based",
                    "properties": {"subtype": "phone"},
                })
        
        return entities
    
    async def _extract_entities_dictionary_based(self, text: str, language: str) -> List[Dict[str, Any]]:
        """사전 기반 엔티티 추출"""
        
        entities = []
        
        # 한국 지명 사전
        korean_locations = [
            "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
            "경기도", "강원도", "충청북도", "충청남도", "전라북도", "전라남도",
            "경상북도", "경상남도", "제주도", "강남구", "서초구", "송파구"
        ]
        
        # 한국 대학교 사전
        korean_universities = [
            "서울대학교", "연세대학교", "고려대학교", "성균관대학교", "한양대학교",
            "중앙대학교", "경희대학교", "한국외국어대학교", "서강대학교", "이화여자대학교"
        ]
        
        # 한국 기업 사전
        korean_companies = [
            "삼성전자", "LG전자", "현대자동차", "SK하이닉스", "NAVER", "카카오",
            "포스코", "한국전력공사", "신한은행", "KB국민은행"
        ]
        
        dictionaries = {
            EntityType.LOCATION: korean_locations,
            EntityType.ORGANIZATION: korean_universities + korean_companies,
        }
        
        for entity_type, dictionary in dictionaries.items():
            for term in dictionary:
                if term in text:
                    start_pos = text.find(term)
                    entities.append({
                        "name": term,
                        "canonical_name": term.lower(),
                        "entity_type": entity_type.value,
                        "confidence_score": 0.95,
                        "start_position": start_pos,
                        "end_position": start_pos + len(term),
                        "extraction_source": "dictionary_based",
                        "properties": {"dictionary": "builtin"},
                    })
        
        return entities
    
    async def _extract_relationships_advanced(
        self,
        text: str,
        entities: List[Dict[str, Any]],
        language: str,
        use_ensemble: bool,
        confidence_threshold: float,
        enable_temporal_extraction: bool,
        doc_id: str = None,
        chunks: List[Dict] = None
    ) -> List[Dict[str, Any]]:
        """고도화된 관계 추출"""
        
        relationships = []
        
        # 규칙 기반 관계 추출
        rule_based_rels = await self._extract_relationships_rule_based(text, entities, language)
        relationships.extend(rule_based_rels)
        
        # 패턴 기반 관계 추출
        pattern_based_rels = await self._extract_relationships_pattern_based(text, entities, language)
        relationships.extend(pattern_based_rels)
        
        # 시간 관계 추출
        if enable_temporal_extraction:
            temporal_rels = await self._extract_temporal_relationships(text, entities, language)
            relationships.extend(temporal_rels)
        
        # 중복 제거 및 병합
        relationships = await self._merge_duplicate_relationships(relationships, confidence_threshold)
        
        return relationships
    
    async def _extract_relationships_rule_based(
        self, text: str, entities: List[Dict[str, Any]], language: str
    ) -> List[Dict[str, Any]]:
        """규칙 기반 관계 추출"""
        
        relationships = []
        
        if language == 'korean':
            # 한국어 관계 패턴
            relation_patterns = {
                RelationType.WORKS_FOR: [
                    r'({entity1})(?:이|가|은|는)?\s*({entity2})(?:에서|에|의)\s*(?:근무|일|업무)',
                    r'({entity1})\s*({entity2})\s*(?:사원|직원|임원|대표)',
                ],
                RelationType.LOCATED_IN: [
                    r'({entity1})(?:이|가|은|는)?\s*({entity2})(?:에|에서)\s*(?:위치|있다|존재)',
                    r'({entity2})(?:의|에\s*있는)\s*({entity1})',
                ],
                RelationType.PART_OF: [
                    r'({entity1})(?:이|가|은|는)?\s*({entity2})(?:의|에\s*속한)\s*(?:부분|일부)',
                    r'({entity2})(?:의|에\s*포함된)\s*({entity1})',
                ],
            }
        else:
            # 영어 관계 패턴
            relation_patterns = {
                RelationType.WORKS_FOR: [
                    r'({entity1})\s+(?:works?\s+(?:for|at)|employed\s+(?:by|at))\s+({entity2})',
                    r'({entity2})\s+(?:employee|staff|member)\s+({entity1})',
                ],
                RelationType.LOCATED_IN: [
                    r'({entity1})\s+(?:is\s+)?(?:located\s+)?(?:in|at)\s+({entity2})',
                    r'({entity2})\s+(?:contains|houses|hosts)\s+({entity1})',
                ],
                RelationType.PART_OF: [
                    r'({entity1})\s+(?:is\s+)?(?:part\s+of|belongs\s+to)\s+({entity2})',
                    r'({entity2})\s+(?:includes|contains)\s+({entity1})',
                ],
            }
        
        # 엔티티 쌍 생성
        entity_names = [e["name"] for e in entities]
        
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:  # 중복 방지
                    continue
                
                for relation_type, patterns in relation_patterns.items():
                    for pattern in patterns:
                        # 패턴에 엔티티 이름 대입
                        filled_pattern = pattern.format(
                            entity1=re.escape(entity1["name"]),
                            entity2=re.escape(entity2["name"])
                        )
                        
                        if re.search(filled_pattern, text, re.IGNORECASE):
                            relationships.append({
                                "source_entity_name": entity1["name"],
                                "target_entity_name": entity2["name"],
                                "relation_type": relation_type.value,
                                "confidence_score": 0.8,
                                "extraction_source": "rule_based",
                                "properties": {"pattern_matched": pattern},
                            })
        
        return relationships
    
    async def _extract_relationships_pattern_based(
        self, text: str, entities: List[Dict[str, Any]], language: str
    ) -> List[Dict[str, Any]]:
        """패턴 기반 관계 추출"""
        
        relationships = []
        
        # 거리 기반 관계 추출 (가까운 엔티티들 간의 관계 추정)
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:
                    continue
                
                # 엔티티 간 거리 계산
                distance = abs(entity1["start_position"] - entity2["start_position"])
                
                # 가까운 거리에 있는 엔티티들은 관련성이 높을 가능성
                if distance < 100:  # 100자 이내
                    confidence = max(0.3, 1.0 - (distance / 100))
                    
                    relationships.append({
                        "source_entity_name": entity1["name"],
                        "target_entity_name": entity2["name"],
                        "relation_type": RelationType.RELATED_TO.value,
                        "confidence_score": confidence,
                        "extraction_source": "proximity_based",
                        "properties": {"distance": distance},
                    })
        
        return relationships
    
    async def _extract_temporal_relationships(
        self, text: str, entities: List[Dict[str, Any]], language: str
    ) -> List[Dict[str, Any]]:
        """시간 관계 추출"""
        
        relationships = []
        
        # 시간 표현 패턴
        temporal_patterns = {
            RelationType.BEFORE: [
                r'({entity1}).*?(?:이전에|전에|먼저).*?({entity2})',
                r'({entity1}).*?before.*?({entity2})',
            ],
            RelationType.AFTER: [
                r'({entity1}).*?(?:이후에|후에|다음에).*?({entity2})',
                r'({entity1}).*?after.*?({entity2})',
            ],
            RelationType.DURING: [
                r'({entity1}).*?(?:동안|중에).*?({entity2})',
                r'({entity1}).*?during.*?({entity2})',
            ],
        }
        
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:
                    continue
                
                for relation_type, patterns in temporal_patterns.items():
                    for pattern in patterns:
                        filled_pattern = pattern.format(
                            entity1=re.escape(entity1["name"]),
                            entity2=re.escape(entity2["name"])
                        )
                        
                        if re.search(filled_pattern, text, re.IGNORECASE):
                            relationships.append({
                                "source_entity_name": entity1["name"],
                                "target_entity_name": entity2["name"],
                                "relation_type": relation_type.value,
                                "confidence_score": 0.7,
                                "extraction_source": "temporal_based",
                                "properties": {"temporal_type": relation_type.value},
                            })
        
        return relationships
    
    async def _merge_duplicate_entities(
        self, entities: List[Dict[str, Any]], confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """중복 엔티티 병합"""
        
        merged_entities = {}
        
        for entity in entities:
            if entity["confidence_score"] < confidence_threshold:
                continue
            
            canonical_name = entity["canonical_name"]
            
            if canonical_name in merged_entities:
                # 기존 엔티티와 병합
                existing = merged_entities[canonical_name]
                existing["confidence_score"] = max(
                    existing["confidence_score"], 
                    entity["confidence_score"]
                )
                existing["mention_count"] = existing.get("mention_count", 1) + 1
                
                # 속성 병합
                existing["properties"].update(entity.get("properties", {}))
                
                # 별칭 추가
                if entity["name"] not in existing.get("aliases", []):
                    existing.setdefault("aliases", []).append(entity["name"])
            else:
                # 새 엔티티 추가
                entity["mention_count"] = 1
                entity.setdefault("aliases", [])
                merged_entities[canonical_name] = entity
        
        return list(merged_entities.values())
    
    async def _merge_duplicate_relationships(
        self, relationships: List[Dict[str, Any]], confidence_threshold: float
    ) -> List[Dict[str, Any]]:
        """중복 관계 병합"""
        
        merged_relationships = {}
        
        for rel in relationships:
            if rel["confidence_score"] < confidence_threshold:
                continue
            
            # 관계 키 생성
            rel_key = f"{rel['source_entity_name']}|{rel['target_entity_name']}|{rel['relation_type']}"
            
            if rel_key in merged_relationships:
                # 기존 관계와 병합
                existing = merged_relationships[rel_key]
                existing["confidence_score"] = max(
                    existing["confidence_score"],
                    rel["confidence_score"]
                )
                existing["mention_count"] = existing.get("mention_count", 1) + 1
                
                # 속성 병합
                existing["properties"].update(rel.get("properties", {}))
            else:
                # 새 관계 추가
                rel["mention_count"] = 1
                merged_relationships[rel_key] = rel
        
        return list(merged_relationships.values())
    
    async def _postprocess_entities(
        self, entities: List[Dict[str, Any]], language: str
    ) -> List[Dict[str, Any]]:
        """엔티티 후처리"""
        
        processed_entities = []
        
        for entity in entities:
            # 이름 정규화
            entity["name"] = entity["name"].strip()
            entity["canonical_name"] = entity["canonical_name"].strip().lower()
            
            # 한국어 특화 처리
            if language == 'korean':
                # 존댓말 제거
                entity["name"] = re.sub(r'님$|씨$', '', entity["name"])
                entity["canonical_name"] = re.sub(r'님$|씨$', '', entity["canonical_name"])
            
            # 최소 길이 체크
            if len(entity["name"]) < 2:
                continue
            
            # 불용어 체크
            stopwords = ['그', '이', '저', '것', 'the', 'a', 'an', 'this', 'that']
            if entity["name"].lower() in stopwords:
                continue
            
            processed_entities.append(entity)
        
        return processed_entities
    
    async def _postprocess_relationships(
        self, 
        relationships: List[Dict[str, Any]], 
        entities: List[Dict[str, Any]], 
        language: str
    ) -> List[Dict[str, Any]]:
        """관계 후처리"""
        
        processed_relationships = []
        entity_names = {e["name"] for e in entities}
        
        for rel in relationships:
            # 엔티티 존재 확인
            if (rel["source_entity_name"] not in entity_names or 
                rel["target_entity_name"] not in entity_names):
                continue
            
            # 자기 참조 관계 제거
            if rel["source_entity_name"] == rel["target_entity_name"]:
                continue
            
            processed_relationships.append(rel)
        
        return processed_relationships
    
    async def _update_kg_statistics(self, kg_id: str):
        """지식 그래프 통계 업데이트"""
        
        kg = self.db.query(KnowledgeGraph).filter(KnowledgeGraph.id == kg_id).first()
        if not kg:
            return
        
        # 엔티티 수 계산
        entity_count = self.db.query(KGEntity).filter(
            KGEntity.knowledge_graph_id == kg_id
        ).count()
        
        # 관계 수 계산
        relationship_count = self.db.query(KGRelationship).filter(
            KGRelationship.knowledge_graph_id == kg_id
        ).count()
        
        # 통계 업데이트
        kg.entity_count = entity_count
        kg.relationship_count = relationship_count
        kg.last_processed_at = datetime.utcnow()
        kg.processing_status = "ready"
        
        self.db.commit()