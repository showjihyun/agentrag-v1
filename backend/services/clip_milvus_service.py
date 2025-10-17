"""
CLIP Milvus Service for Cross-Modal Search

CLIP 임베딩을 Milvus에 저장하고 크로스 모달 검색 수행
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pymilvus import Collection, connections, utility, FieldSchema, CollectionSchema, DataType
import uuid

logger = logging.getLogger(__name__)


class CLIPMilvusService:
    """
    CLIP + Milvus 통합 서비스
    
    Features:
    - CLIP 임베딩 저장
    - 크로스 모달 검색
    - 텍스트-이미지 통합 검색
    - 메타데이터 관리
    """
    
    def __init__(
        self,
        collection_name: str = "clip_embeddings",
        host: str = "localhost",
        port: str = "19530",
        embedding_dim: int = 512  # CLIP ViT-B/32 dimension
    ):
        """
        초기화
        
        Args:
            collection_name: Milvus 컬렉션 이름
            host: Milvus 호스트
            port: Milvus 포트
            embedding_dim: 임베딩 차원
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.embedding_dim = embedding_dim
        self.collection = None
        
        # 연결 및 컬렉션 초기화
        self._connect()
        self._init_collection()
        
        logger.info(f"CLIPMilvusService initialized: {collection_name}")
    
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
            # 컬렉션이 이미 존재하는지 확인
            if utility.has_collection(self.collection_name):
                self.collection = Collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
                return
            
            # 새 컬렉션 생성
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="content_type", dtype=DataType.VARCHAR, max_length=50),  # 'text' or 'image'
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=5000),  # 텍스트 내용 또는 이미지 경로
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="CLIP embeddings for cross-modal search"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # 인덱스 생성
            index_params = {
                "metric_type": "IP",  # Inner Product (cosine similarity for normalized vectors)
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            logger.info(f"Created new collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def insert_text(
        self,
        text: str,
        embedding: np.ndarray,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        텍스트 임베딩 삽입
        
        Args:
            text: 텍스트 내용
            embedding: CLIP 텍스트 임베딩 (D,)
            document_id: 문서 ID
            metadata: 메타데이터
        
        Returns:
            content_id: 콘텐츠 ID
        """
        try:
            content_id = str(uuid.uuid4())
            
            # 임베딩이 1D인 경우 처리
            if len(embedding.shape) == 2:
                embedding = embedding[0]
            
            # 삽입
            entities = [
                [content_id],  # id
                [embedding.tolist()],  # embedding
                ["text"],  # content_type
                [text[:5000]],  # content (truncate)
                [document_id],  # document_id
                [metadata or {}]  # metadata
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.debug(f"Inserted text: {content_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to insert text: {e}")
            raise
    
    def insert_image(
        self,
        image_path: str,
        embedding: np.ndarray,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        이미지 임베딩 삽입
        
        Args:
            image_path: 이미지 파일 경로
            embedding: CLIP 이미지 임베딩 (D,)
            document_id: 문서 ID
            metadata: 메타데이터
        
        Returns:
            content_id: 콘텐츠 ID
        """
        try:
            content_id = str(uuid.uuid4())
            
            # 임베딩이 1D인 경우 처리
            if len(embedding.shape) == 2:
                embedding = embedding[0]
            
            # 삽입
            entities = [
                [content_id],  # id
                [embedding.tolist()],  # embedding
                ["image"],  # content_type
                [image_path],  # content
                [document_id],  # document_id
                [metadata or {}]  # metadata
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.debug(f"Inserted image: {content_id}")
            
            return content_id
            
        except Exception as e:
            logger.error(f"Failed to insert image: {e}")
            raise
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        content_type: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        크로스 모달 검색
        
        Args:
            query_embedding: 쿼리 임베딩 (D,)
            top_k: 반환할 결과 수
            content_type: 콘텐츠 타입 필터 ('text', 'image', None)
            filter_expr: 추가 필터 표현식
        
        Returns:
            검색 결과 리스트
        """
        try:
            # 컬렉션 로드
            self.collection.load()
            
            # 임베딩이 1D인 경우 처리
            if len(query_embedding.shape) == 2:
                query_embedding = query_embedding[0]
            
            # 필터 표현식 구성
            expr = filter_expr
            if content_type:
                type_filter = f'content_type == "{content_type}"'
                expr = f"{expr} and {type_filter}" if expr else type_filter
            
            # 검색
            search_params = {
                "metric_type": "IP",
                "params": {"nprobe": 10}
            }
            
            results = self.collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                expr=expr,
                output_fields=["content_type", "content", "document_id", "metadata"]
            )
            
            # 결과 포맷팅
            formatted_results = []
            
            for result in results[0]:
                formatted_results.append({
                    "id": result.id,
                    "content_type": result.entity.get("content_type"),
                    "content": result.entity.get("content"),
                    "document_id": result.entity.get("document_id"),
                    "metadata": result.entity.get("metadata", {}),
                    "score": result.distance
                })
            
            logger.info(f"Search completed: {len(formatted_results)} results")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def search_images_with_text(
        self,
        text_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        텍스트 쿼리로 이미지 검색
        
        Args:
            text_embedding: 텍스트 임베딩
            top_k: 반환할 결과 수
        
        Returns:
            이미지 검색 결과
        """
        return self.search(
            query_embedding=text_embedding,
            top_k=top_k,
            content_type="image"
        )
    
    def search_text_with_image(
        self,
        image_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        이미지 쿼리로 텍스트 검색
        
        Args:
            image_embedding: 이미지 임베딩
            top_k: 반환할 결과 수
        
        Returns:
            텍스트 검색 결과
        """
        return self.search(
            query_embedding=image_embedding,
            top_k=top_k,
            content_type="text"
        )
    
    def delete_document(self, document_id: str):
        """문서의 모든 콘텐츠 삭제"""
        try:
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted document contents: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계"""
        try:
            self.collection.load()
            
            stats = {
                "name": self.collection_name,
                "num_entities": self.collection.num_entities,
                "embedding_dim": self.embedding_dim
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Global instance
_clip_milvus_service: Optional[CLIPMilvusService] = None


def get_clip_milvus_service(
    collection_name: str = "clip_embeddings",
    host: str = "localhost",
    port: str = "19530",
    embedding_dim: int = 512
) -> CLIPMilvusService:
    """Get global CLIP Milvus service instance"""
    global _clip_milvus_service
    
    if _clip_milvus_service is None:
        _clip_milvus_service = CLIPMilvusService(
            collection_name=collection_name,
            host=host,
            port=port,
            embedding_dim=embedding_dim
        )
    
    return _clip_milvus_service
