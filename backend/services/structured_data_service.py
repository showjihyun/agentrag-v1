"""
Structured Data Service for Tables

표 데이터를 Milvus에 저장하고 검색하는 서비스
"""

import logging
from typing import List, Dict, Any, Optional
from pymilvus import Collection, connections, utility, FieldSchema, CollectionSchema, DataType
import json

logger = logging.getLogger(__name__)


class StructuredDataService:
    """
    구조화된 데이터 (표) 관리 서비스
    
    Features:
    - 표 데이터 저장
    - 텍스트 기반 표 검색
    - 사용자 격리
    - 메타데이터 관리
    """
    
    def __init__(
        self,
        collection_name: str = "structured_tables",
        host: str = "localhost",
        port: str = "19530"
    ):
        """초기화"""
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.collection = None
        
        self._connect()
        self._init_collection()
        
        logger.info(f"StructuredDataService initialized: {collection_name}")
    
    def _connect(self):
        """Milvus 연결"""
        try:
            connections.connect(
                alias="default",
                host=self.host,
                port=self.port
            )
            logger.info(f"Connected to Milvus: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            raise
    
    def _init_collection(self):
        """컬렉션 초기화"""
        try:
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
                return
            
            # 새 컬렉션 생성
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="table_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="page_number", dtype=DataType.INT64),
                FieldSchema(name="caption", dtype=DataType.VARCHAR, max_length=1000),
                FieldSchema(name="searchable_text", dtype=DataType.VARCHAR, max_length=10000),
                FieldSchema(name="table_data", dtype=DataType.JSON),  # 구조화된 데이터
                FieldSchema(name="bbox", dtype=DataType.JSON),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="Structured table data with user isolation"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # 인덱스 생성
            self.collection.create_index(
                field_name="user_id",
                index_name="user_id_index"
            )
            
            self.collection.create_index(
                field_name="document_id",
                index_name="document_id_index"
            )
            
            logger.info(f"Created new collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def insert_table(
        self,
        table_id: str,
        document_id: str,
        user_id: str,
        page_number: int,
        caption: str,
        searchable_text: str,
        table_data: Dict,
        bbox: Optional[List[float]] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        표 데이터 삽입
        
        Args:
            table_id: 표 ID
            document_id: 문서 ID
            user_id: 사용자 ID
            page_number: 페이지 번호
            caption: 표 캡션
            searchable_text: 검색 가능한 텍스트
            table_data: 구조화된 표 데이터
            bbox: 위치 정보
            metadata: 메타데이터
        
        Returns:
            table_id
        """
        try:
            entities = [
                [table_id],
                [table_id],
                [document_id],
                [user_id],
                [page_number],
                [caption[:1000]],
                [searchable_text[:10000]],
                [table_data],
                [bbox or []],
                [metadata or {}]
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Inserted table: {table_id} (user: {user_id})")
            
            return table_id
            
        except Exception as e:
            logger.error(f"Failed to insert table: {e}")
            raise
    
    def search_tables(
        self,
        query: str,
        user_id: Optional[str] = None,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        표 검색 (텍스트 기반)
        
        Args:
            query: 검색 쿼리
            user_id: 사용자 ID (격리)
            document_id: 문서 ID (필터)
            top_k: 반환 개수
        
        Returns:
            검색 결과 리스트
        """
        try:
            self.collection.load()
            
            # 필터 구성
            filter_parts = []
            
            if user_id:
                filter_parts.append(f'user_id == "{user_id}"')
            
            if document_id:
                filter_parts.append(f'document_id == "{document_id}"')
            
            filter_expr = " and ".join(filter_parts) if filter_parts else None
            
            # 쿼리 실행 (전체 스캔)
            results = self.collection.query(
                expr=filter_expr or "id != ''",
                output_fields=[
                    "table_id", "document_id", "user_id", "page_number",
                    "caption", "searchable_text", "table_data", "bbox", "metadata"
                ],
                limit=top_k * 100  # 더 많이 가져와서 필터링
            )
            
            # 텍스트 매칭 (간단한 substring 검색)
            query_lower = query.lower()
            matched_tables = []
            
            for result in results:
                searchable_text = result.get("searchable_text", "").lower()
                caption = result.get("caption", "").lower()
                
                # 점수 계산
                score = 0
                if query_lower in searchable_text:
                    score += searchable_text.count(query_lower) * 2
                if query_lower in caption:
                    score += 5
                
                if score > 0:
                    matched_tables.append({
                        'table_id': result.get('table_id'),
                        'document_id': result.get('document_id'),
                        'user_id': result.get('user_id'),
                        'page_number': result.get('page_number'),
                        'caption': result.get('caption'),
                        'searchable_text': result.get('searchable_text'),
                        'table_data': result.get('table_data'),
                        'bbox': result.get('bbox'),
                        'metadata': result.get('metadata'),
                        'score': score
                    })
            
            # 점수로 정렬
            matched_tables.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Table search: {len(matched_tables[:top_k])} results")
            
            return matched_tables[:top_k]
            
        except Exception as e:
            logger.error(f"Table search failed: {e}")
            return []
    
    def delete_table(self, table_id: str):
        """표 삭제"""
        try:
            expr = f'table_id == "{table_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted table: {table_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete table: {e}")
            raise
    
    def delete_document_tables(self, document_id: str):
        """문서의 모든 표 삭제"""
        try:
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted document tables: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document tables: {e}")
            raise


# Global instance
_structured_data_service: Optional[StructuredDataService] = None


def get_structured_data_service(
    collection_name: str = "structured_tables",
    host: str = "localhost",
    port: str = "19530"
) -> StructuredDataService:
    """Get global structured data service instance"""
    global _structured_data_service
    
    if _structured_data_service is None:
        _structured_data_service = StructuredDataService(
            collection_name=collection_name,
            host=host,
            port=port
        )
    
    return _structured_data_service
