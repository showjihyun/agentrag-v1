"""
Audio Milvus Service for Audio RAG

오디오 임베딩을 Milvus에 저장하고 검색
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional
from pymilvus import Collection, connections, utility, FieldSchema, CollectionSchema, DataType
import uuid

logger = logging.getLogger(__name__)


class AudioMilvusService:
    """
    Audio + Milvus 통합 서비스
    
    Features:
    - 오디오 임베딩 저장
    - 음성 유사도 검색
    - 메타데이터 관리
    - 효율적인 인덱싱
    """
    
    def __init__(
        self,
        collection_name: str = "audio_embeddings",
        host: str = "localhost",
        port: str = "19530",
        embedding_dim: int = 1280  # Whisper large-v3 dimension
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
        
        logger.info(f"AudioMilvusService initialized: {collection_name}")
    
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
                FieldSchema(name="audio_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.embedding_dim),
                FieldSchema(name="audio_path", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="transcription", dtype=DataType.VARCHAR, max_length=5000),
                FieldSchema(name="duration", dtype=DataType.FLOAT),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="Audio embeddings for audio RAG"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # 인덱스 생성
            index_params = {
                "metric_type": "IP",  # Inner Product (cosine similarity)
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
    
    def insert_audio(
        self,
        audio_path: str,
        embedding: np.ndarray,
        document_id: str,
        transcription: str = "",
        duration: float = 0.0,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        오디오 임베딩 삽입
        
        Args:
            audio_path: 오디오 파일 경로
            embedding: 오디오 임베딩 (D,)
            document_id: 문서 ID
            transcription: 텍스트 변환 (선택)
            duration: 오디오 길이 (초)
            metadata: 메타데이터
        
        Returns:
            audio_id: 오디오 ID
        """
        try:
            # 오디오 ID 생성
            audio_id = str(uuid.uuid4())
            
            # 임베딩이 1D인 경우 처리
            if len(embedding.shape) == 2:
                embedding = embedding[0]
            
            # 삽입
            entities = [
                [audio_id],  # id
                [audio_id],  # audio_id
                [embedding.tolist()],  # embedding
                [audio_path],  # audio_path
                [transcription],  # transcription
                [duration],  # duration
                [document_id],  # document_id
                [metadata or {}]  # metadata
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"Inserted audio: {audio_id} ({duration:.2f}s)")
            
            return audio_id
            
        except Exception as e:
            logger.error(f"Failed to insert audio: {e}")
            raise
    
    def search_audio(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        오디오 검색
        
        Args:
            query_embedding: 쿼리 임베딩 (D,)
            top_k: 반환할 결과 수
            filter_expr: 필터 표현식
        
        Returns:
            검색 결과 리스트
        """
        try:
            # 컬렉션 로드
            self.collection.load()
            
            # 임베딩이 1D인 경우 처리
            if len(query_embedding.shape) == 2:
                query_embedding = query_embedding[0]
            
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
                expr=filter_expr,
                output_fields=["audio_id", "audio_path", "transcription", "duration", "document_id", "metadata"]
            )
            
            # 결과 포맷팅
            formatted_results = []
            
            for result in results[0]:
                formatted_results.append({
                    "audio_id": result.entity.get("audio_id"),
                    "audio_path": result.entity.get("audio_path"),
                    "transcription": result.entity.get("transcription"),
                    "duration": result.entity.get("duration"),
                    "document_id": result.entity.get("document_id"),
                    "metadata": result.entity.get("metadata", {}),
                    "score": result.distance
                })
            
            logger.info(f"Search completed: {len(formatted_results)} results")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def delete_audio(self, audio_id: str):
        """오디오 삭제"""
        try:
            expr = f'audio_id == "{audio_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted audio: {audio_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete audio: {e}")
            raise
    
    def delete_document(self, document_id: str):
        """문서의 모든 오디오 삭제"""
        try:
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted document audios: {document_id}")
            
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
_audio_milvus_service: Optional[AudioMilvusService] = None


def get_audio_milvus_service(
    collection_name: str = "audio_embeddings",
    host: str = "localhost",
    port: str = "19530",
    embedding_dim: int = 1280
) -> AudioMilvusService:
    """Get global audio Milvus service instance"""
    global _audio_milvus_service
    
    if _audio_milvus_service is None:
        _audio_milvus_service = AudioMilvusService(
            collection_name=collection_name,
            host=host,
            port=port,
            embedding_dim=embedding_dim
        )
    
    return _audio_milvus_service
