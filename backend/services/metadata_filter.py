"""
Metadata Filter Service for Multimodal RAG

메타데이터 기반 필터링 및 하이브리드 검색
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataFilter:
    """
    메타데이터 필터 서비스
    
    Features:
    - 날짜 범위 필터
    - 콘텐츠 타입 필터
    - 화자/작성자 필터
    - 언어 필터
    - 커스텀 메타데이터 필터
    - Milvus 표현식 생성
    """
    
    def __init__(self):
        """초기화"""
        logger.info("MetadataFilter initialized")
    
    def build_filter_expression(
        self,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Tuple[str, str]] = None,
        content_types: Optional[List[str]] = None,
        speaker: Optional[str] = None,
        author: Optional[str] = None,
        language: Optional[str] = None,
        document_ids: Optional[List[str]] = None
    ) -> str:
        """
        Milvus 필터 표현식 생성
        
        Args:
            filters: 커스텀 필터 딕셔너리
            date_range: 날짜 범위 (start, end)
            content_types: 콘텐츠 타입 리스트 ['text', 'image', 'audio']
            speaker: 화자 이름
            author: 작성자 이름
            language: 언어 코드 (e.g., 'ko', 'en')
            document_ids: 문서 ID 리스트
        
        Returns:
            Milvus 필터 표현식
        """
        expressions = []
        
        # 1. 날짜 범위 필터
        if date_range:
            start_date, end_date = date_range
            if start_date:
                expressions.append(f'created_at >= "{start_date}"')
            if end_date:
                expressions.append(f'created_at <= "{end_date}"')
        
        # 2. 콘텐츠 타입 필터
        if content_types:
            # 여러 타입을 OR로 연결
            type_expr = " or ".join([f'content_type == "{ct}"' for ct in content_types])
            expressions.append(f'({type_expr})')
        
        # 3. 화자 필터
        if speaker:
            expressions.append(f'speaker == "{speaker}"')
        
        # 4. 작성자 필터
        if author:
            expressions.append(f'author == "{author}"')
        
        # 5. 언어 필터
        if language:
            expressions.append(f'language == "{language}"')
        
        # 6. 문서 ID 필터
        if document_ids:
            # 여러 ID를 OR로 연결
            id_expr = " or ".join([f'document_id == "{doc_id}"' for doc_id in document_ids])
            expressions.append(f'({id_expr})')
        
        # 7. 커스텀 필터
        if filters:
            for key, value in filters.items():
                if isinstance(value, str):
                    expressions.append(f'{key} == "{value}"')
                elif isinstance(value, (int, float)):
                    expressions.append(f'{key} == {value}')
                elif isinstance(value, list):
                    # 리스트는 IN 연산자로 변환
                    list_expr = " or ".join([f'{key} == "{v}"' for v in value])
                    expressions.append(f'({list_expr})')
        
        # 모든 표현식을 AND로 연결
        if expressions:
            return " and ".join(expressions)
        else:
            return ""  # 필터 없음
    
    def validate_filters(
        self,
        filters: Optional[Dict[str, Any]] = None,
        date_range: Optional[Tuple[str, str]] = None,
        content_types: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        필터 유효성 검증
        
        Args:
            filters: 커스텀 필터
            date_range: 날짜 범위
            content_types: 콘텐츠 타입
        
        Returns:
            (유효 여부, 에러 메시지)
        """
        # 날짜 범위 검증
        if date_range:
            start_date, end_date = date_range
            try:
                if start_date:
                    datetime.fromisoformat(start_date)
                if end_date:
                    datetime.fromisoformat(end_date)
                
                # 시작일이 종료일보다 늦으면 에러
                if start_date and end_date:
                    if start_date > end_date:
                        return False, "Start date must be before end date"
            except ValueError as e:
                return False, f"Invalid date format: {e}"
        
        # 콘텐츠 타입 검증
        if content_types:
            valid_types = ['text', 'image', 'audio']
            for ct in content_types:
                if ct not in valid_types:
                    return False, f"Invalid content type: {ct}. Must be one of {valid_types}"
        
        return True, None
    
    def apply_filters_to_results(
        self,
        results: List[Dict[str, Any]],
        filters: Optional[Dict[str, Any]] = None,
        min_score: Optional[float] = None,
        max_results: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        검색 결과에 추가 필터 적용 (후처리)
        
        Args:
            results: 검색 결과
            filters: 추가 필터
            min_score: 최소 점수
            max_results: 최대 결과 수
        
        Returns:
            필터링된 결과
        """
        filtered = results.copy()
        
        # 최소 점수 필터
        if min_score is not None:
            filtered = [r for r in filtered if r.get('score', 0.0) >= min_score]
        
        # 커스텀 필터 적용
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    # 리스트는 IN 연산
                    filtered = [
                        r for r in filtered
                        if r.get('metadata', {}).get(key) in value
                    ]
                else:
                    # 단일 값은 동등 비교
                    filtered = [
                        r for r in filtered
                        if r.get('metadata', {}).get(key) == value
                    ]
        
        # 최대 결과 수 제한
        if max_results is not None:
            filtered = filtered[:max_results]
        
        return filtered
    
    def get_facets(
        self,
        results: List[Dict[str, Any]],
        facet_fields: List[str]
    ) -> Dict[str, Dict[str, int]]:
        """
        패싯 검색 (결과 통계)
        
        Args:
            results: 검색 결과
            facet_fields: 패싯 필드 리스트
        
        Returns:
            패싯 통계
        """
        facets = {}
        
        for field in facet_fields:
            facets[field] = {}
            
            for result in results:
                value = result.get('metadata', {}).get(field)
                if value:
                    facets[field][value] = facets[field].get(value, 0) + 1
        
        return facets


# Global instance
_metadata_filter: Optional[MetadataFilter] = None


def get_metadata_filter() -> MetadataFilter:
    """Get global metadata filter instance"""
    global _metadata_filter
    
    if _metadata_filter is None:
        _metadata_filter = MetadataFilter()
    
    return _metadata_filter
