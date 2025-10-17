"""
ColPali Milvus Service for Multimodal RAG

ColPali 멀티벡터 임베딩을 Milvus에 저장하고 Late Interaction 검색 수행
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pymilvus import Collection, connections, utility, FieldSchema, CollectionSchema, DataType
import uuid

logger = logging.getLogger(__name__)


class ColPaliMilvusService:
    """
    ColPali + Milvus 통합 서비스
    
    Features:
    - 멀티벡터 임베딩 저장
    - Late Interaction 검색 (MaxSim)
    - 효율적인 인덱싱
    - 하이브리드 검색 (텍스트 + 이미지)
    """
    
    def __init__(
        self,
        collection_name: str = "colpali_images",
        host: str = "localhost",
        port: str = "19530"
    ):
        """
        초기화
        
        Args:
            collection_name: Milvus 컬렉션 이름
            host: Milvus 호스트
            port: Milvus 포트
        """
        self.collection_name = collection_name
        self.host = host
        self.port = port
        self.collection = None
        
        # 연결 및 컬렉션 초기화
        self._connect()
        self._init_collection()
        
        logger.info(f"ColPaliMilvusService initialized: {collection_name}")
    
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
            # ColPali는 멀티벡터이므로 각 패치를 별도 레코드로 저장
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
                FieldSchema(name="image_id", dtype=DataType.VARCHAR, max_length=100),  # 이미지 그룹 ID
                FieldSchema(name="patch_index", dtype=DataType.INT64),  # 패치 인덱스
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),  # 패치 임베딩
                FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=500),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=100),
                FieldSchema(name="user_id", dtype=DataType.VARCHAR, max_length=100),  # 사용자 격리
                # Phase 2: Text-Image Linking
                FieldSchema(name="page_number", dtype=DataType.INT64),  # 페이지 번호
                FieldSchema(name="position_x", dtype=DataType.INT64),  # X 좌표
                FieldSchema(name="position_y", dtype=DataType.INT64),  # Y 좌표
                FieldSchema(name="associated_text", dtype=DataType.VARCHAR, max_length=5000),  # 관련 텍스트
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]
            
            schema = CollectionSchema(
                fields=fields,
                description="ColPali multi-vector embeddings for images with user isolation"
            )
            
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )
            
            # 벡터 인덱스 생성 (HNSW for better performance)
            index_params = {
                "metric_type": "IP",  # Inner Product (cosine similarity)
                "index_type": "HNSW",  # Upgraded from IVF_FLAT
                "params": {
                    "M": 16,  # Number of connections
                    "efConstruction": 200  # Build time quality
                }
            }
            
            self.collection.create_index(
                field_name="embedding",
                index_params=index_params
            )
            
            # 스칼라 인덱스 생성 (빠른 필터링)
            self.collection.create_index(
                field_name="user_id",
                index_name="user_id_index"
            )
            
            self.collection.create_index(
                field_name="document_id",
                index_name="document_id_index"
            )
            
            logger.info(f"Created new collection with HNSW index: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize collection: {e}")
            raise
    
    def insert_image(
        self,
        image_path: str,
        embeddings: np.ndarray,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict] = None,
        page_number: int = 0,  # Phase 2: Page info
        position: Optional[Dict[str, int]] = None,  # Phase 2: Position {x, y}
        associated_text: str = ""  # Phase 2: Related text
    ) -> str:
        """
        이미지 임베딩 삽입 with text-image linking
        
        Args:
            image_path: 이미지 경로
            embeddings: ColPali 패치 임베딩 (N, D)
            document_id: 문서 ID
            user_id: 사용자 ID (격리용)
            metadata: 메타데이터
            page_number: 페이지 번호 (PDF 등)
            position: 이미지 위치 {x, y}
            associated_text: 이미지와 관련된 텍스트 (캡션, 주변 텍스트 등)
        
        Returns:
            image_id: 이미지 그룹 ID
        """
        try:
            # 이미지 그룹 ID 생성
            image_id = str(uuid.uuid4())
            
            # 각 패치를 별도 레코드로 저장
            num_patches = embeddings.shape[0]
            
            # Position defaults
            pos_x = position.get("x", 0) if position else 0
            pos_y = position.get("y", 0) if position else 0
            
            ids = []
            image_ids = []
            patch_indices = []
            embedding_list = []
            image_paths = []
            document_ids = []
            user_ids = []
            page_numbers = []  # Phase 2
            positions_x = []  # Phase 2
            positions_y = []  # Phase 2
            associated_texts = []  # Phase 2
            metadata_list = []
            
            for i in range(num_patches):
                patch_id = f"{image_id}_patch_{i}"
                
                ids.append(patch_id)
                image_ids.append(image_id)
                patch_indices.append(i)
                embedding_list.append(embeddings[i].tolist())
                image_paths.append(image_path)
                document_ids.append(document_id)
                user_ids.append(user_id)
                page_numbers.append(page_number)
                positions_x.append(pos_x)
                positions_y.append(pos_y)
                associated_texts.append(associated_text[:5000])  # Truncate to max length
                metadata_list.append(metadata or {})
            
            # 삽입
            entities = [
                ids,
                image_ids,
                patch_indices,
                embedding_list,
                image_paths,
                document_ids,
                user_ids,
                page_numbers,  # Phase 2
                positions_x,  # Phase 2
                positions_y,  # Phase 2
                associated_texts,  # Phase 2
                metadata_list
            ]
            
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(
                f"Inserted image: {image_id} ({num_patches} patches) "
                f"for user: {user_id}, page: {page_number}, "
                f"text_length: {len(associated_text)}"
            )
            
            return image_id
            
        except Exception as e:
            logger.error(f"Failed to insert image: {e}")
            raise
    
    def search_images(
        self,
        query_embeddings: np.ndarray,
        top_k: int = 5,
        filter_expr: Optional[str] = None,
        user_id: Optional[str] = None  # NEW: User isolation
    ) -> List[Dict[str, Any]]:
        """
        Late Interaction 검색 (MaxSim) with optimizations
        
        Args:
            query_embeddings: 쿼리 패치 임베딩 (M, D)
            top_k: 반환할 이미지 수
            filter_expr: 필터 표현식
            user_id: 사용자 ID (격리용)
        
        Returns:
            검색 결과 리스트
        """
        try:
            # 컬렉션 로드
            self.collection.load()
            
            # User isolation filter
            if user_id:
                user_filter = f'user_id == "{user_id}"'
                filter_expr = f"({filter_expr}) and ({user_filter})" if filter_expr else user_filter
                logger.debug(f"Applied user filter: {user_filter}")
            
            # 1단계: 배치 검색으로 최적화
            num_query_patches = query_embeddings.shape[0]
            
            # Adaptive candidate size (더 효율적)
            candidate_multiplier = min(20, max(5, num_query_patches * 2))
            candidate_limit = top_k * candidate_multiplier
            
            # HNSW search params
            search_params = {
                "metric_type": "IP",
                "params": {"ef": 64}  # HNSW search quality
            }
            
            # 배치 검색 (모든 쿼리 패치 한번에)
            results = self.collection.search(
                data=query_embeddings.tolist(),  # All patches at once
                anns_field="embedding",
                param=search_params,
                limit=candidate_limit,
                expr=filter_expr,
                output_fields=[
                    "image_id", "patch_index", "image_path", "document_id", "user_id",
                    "page_number", "position_x", "position_y", "associated_text", "metadata"
                ]
            )
            
            # 2단계: 이미지별로 그룹화하고 MaxSim 계산
            image_scores = {}
            image_info = {}
            
            for query_idx, query_results in enumerate(results):
                for result in query_results:
                    image_id = result.entity.get("image_id")
                    score = result.distance
                    
                    if image_id not in image_scores:
                        image_scores[image_id] = []
                        image_info[image_id] = {
                            "image_path": result.entity.get("image_path"),
                            "document_id": result.entity.get("document_id"),
                            "user_id": result.entity.get("user_id"),
                            "page_number": result.entity.get("page_number", 0),
                            "position": {
                                "x": result.entity.get("position_x", 0),
                                "y": result.entity.get("position_y", 0)
                            },
                            "associated_text": result.entity.get("associated_text", ""),
                            "metadata": result.entity.get("metadata", {})
                        }
                    
                    image_scores[image_id].append(score)
            
            # 3단계: 각 이미지의 MaxSim 점수 계산
            final_results = []
            
            for image_id, scores in image_scores.items():
                # MaxSim: 각 쿼리 패치의 최대 유사도의 합
                # 상위 num_query_patches개의 점수만 사용
                max_sim_score = sum(sorted(scores, reverse=True)[:num_query_patches])
                
                final_results.append({
                    "image_id": image_id,
                    "score": max_sim_score,
                    **image_info[image_id]
                })
            
            # 점수로 정렬
            final_results.sort(key=lambda x: x["score"], reverse=True)
            
            # Top-K 반환
            top_results = final_results[:top_k]
            
            logger.info(f"Search completed: {len(top_results)} results (user: {user_id})")
            
            return top_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def delete_image(self, image_id: str):
        """이미지 삭제"""
        try:
            expr = f'image_id == "{image_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted image: {image_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete image: {e}")
            raise
    
    def delete_document(self, document_id: str):
        """문서의 모든 이미지 삭제"""
        try:
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()
            
            logger.info(f"Deleted document images: {document_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            raise
    
    def search_by_text(
        self,
        text_query: str,
        top_k: int = 5,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        텍스트 기반 이미지 검색 (associated_text 필드 사용)
        
        Args:
            text_query: 텍스트 검색 쿼리
            top_k: 반환할 이미지 수
            user_id: 사용자 ID
        
        Returns:
            검색 결과 리스트
        """
        try:
            self.collection.load()
            
            # Build filter expression for text search
            # Note: Milvus doesn't support full-text search on VARCHAR
            # This is a simple contains check
            filter_parts = []
            
            if user_id:
                filter_parts.append(f'user_id == "{user_id}"')
            
            # For better text search, consider using external search engine
            # or hybrid approach with text embeddings
            
            filter_expr = " and ".join(filter_parts) if filter_parts else None
            
            # Query all matching records
            results = self.collection.query(
                expr=filter_expr or "id != ''",
                output_fields=[
                    "image_id", "image_path", "document_id", "user_id",
                    "page_number", "associated_text", "metadata"
                ],
                limit=top_k * 100  # Get more candidates for filtering
            )
            
            # Filter by text content (simple substring match)
            text_query_lower = text_query.lower()
            matched_images = {}
            
            for result in results:
                associated_text = result.get("associated_text", "").lower()
                if text_query_lower in associated_text:
                    image_id = result.get("image_id")
                    if image_id not in matched_images:
                        # Calculate simple relevance score
                        score = associated_text.count(text_query_lower)
                        matched_images[image_id] = {
                            "image_id": image_id,
                            "image_path": result.get("image_path"),
                            "document_id": result.get("document_id"),
                            "user_id": result.get("user_id"),
                            "page_number": result.get("page_number"),
                            "associated_text": result.get("associated_text"),
                            "metadata": result.get("metadata", {}),
                            "score": score
                        }
            
            # Sort by score and return top_k
            sorted_results = sorted(
                matched_images.values(),
                key=lambda x: x["score"],
                reverse=True
            )
            
            logger.info(f"Text-based image search: {len(sorted_results[:top_k])} results")
            return sorted_results[:top_k]
            
        except Exception as e:
            logger.error(f"Text-based search failed: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계"""
        try:
            self.collection.load()
            
            stats = {
                "name": self.collection_name,
                "num_entities": self.collection.num_entities,
                "schema": str(self.collection.schema)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}


# Global instance
_colpali_milvus_service: Optional[ColPaliMilvusService] = None


def get_colpali_milvus_service(
    collection_name: str = "colpali_images",
    host: str = "localhost",
    port: str = "19530"
) -> ColPaliMilvusService:
    """Get global ColPali Milvus service instance"""
    global _colpali_milvus_service
    
    if _colpali_milvus_service is None:
        _colpali_milvus_service = ColPaliMilvusService(
            collection_name=collection_name,
            host=host,
            port=port
        )
    
    return _colpali_milvus_service
