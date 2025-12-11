"""
Knowledgebase User Settings Service.

사용자별 Knowledgebase 개인화 설정:
- 선호 언어 (한글/영어)
- 검색 모드 (vector/keyword/hybrid)
- 청킹 설정
- 검색 설정
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

logger = logging.getLogger(__name__)


class PreferredLanguage(str, Enum):
    """선호 언어"""
    KOREAN = "ko"
    ENGLISH = "en"
    AUTO = "auto"


class DefaultSearchMode(str, Enum):
    """기본 검색 모드"""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


@dataclass
class KnowledgebaseUserSettings:
    """사용자별 Knowledgebase 설정"""
    
    # 언어 설정
    preferred_language: PreferredLanguage = PreferredLanguage.AUTO
    
    # 검색 설정
    default_search_mode: DefaultSearchMode = DefaultSearchMode.HYBRID
    default_top_k: int = 10
    expand_query_by_default: bool = True
    min_score_threshold: float = 0.3
    
    # 청킹 설정
    default_chunk_size: int = 500
    default_chunk_overlap: int = 50
    preserve_structure: bool = True
    
    # 하이브리드 검색 가중치
    vector_weight: float = 0.6
    bm25_weight: float = 0.4
    
    # 리랭킹 설정
    enable_reranking: bool = True
    reranking_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    # 임베딩 모델 설정
    embedding_model: str = "jhgan/ko-sroberta-multitask"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "preferred_language": self.preferred_language.value,
            "default_search_mode": self.default_search_mode.value,
            "default_top_k": self.default_top_k,
            "expand_query_by_default": self.expand_query_by_default,
            "min_score_threshold": self.min_score_threshold,
            "default_chunk_size": self.default_chunk_size,
            "default_chunk_overlap": self.default_chunk_overlap,
            "preserve_structure": self.preserve_structure,
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight,
            "enable_reranking": self.enable_reranking,
            "reranking_model": self.reranking_model,
            "embedding_model": self.embedding_model,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgebaseUserSettings":
        """딕셔너리에서 생성"""
        return cls(
            preferred_language=PreferredLanguage(data.get("preferred_language", "auto")),
            default_search_mode=DefaultSearchMode(data.get("default_search_mode", "hybrid")),
            default_top_k=data.get("default_top_k", 10),
            expand_query_by_default=data.get("expand_query_by_default", True),
            min_score_threshold=data.get("min_score_threshold", 0.3),
            default_chunk_size=data.get("default_chunk_size", 500),
            default_chunk_overlap=data.get("default_chunk_overlap", 50),
            preserve_structure=data.get("preserve_structure", True),
            vector_weight=data.get("vector_weight", 0.6),
            bm25_weight=data.get("bm25_weight", 0.4),
            enable_reranking=data.get("enable_reranking", True),
            reranking_model=data.get("reranking_model", "cross-encoder/ms-marco-MiniLM-L-6-v2"),
            embedding_model=data.get("embedding_model", "jhgan/ko-sroberta-multitask"),
        )


class KnowledgebaseUserSettingsService:
    """
    사용자별 Knowledgebase 설정 관리 서비스.
    
    Features:
    - 사용자별 설정 저장/조회
    - 기본값 관리
    - 설정 검증
    """
    
    def __init__(self, db: Session):
        """
        Initialize service.
        
        Args:
            db: Database session
        """
        self.db = db
        self._cache: Dict[str, KnowledgebaseUserSettings] = {}
    
    def get_user_settings(self, user_id: str) -> KnowledgebaseUserSettings:
        """
        사용자 설정 조회.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용자 설정 (없으면 기본값)
        """
        # 캐시 확인
        if user_id in self._cache:
            return self._cache[user_id]
        
        try:
            # DB에서 조회
            from backend.db.models.user_settings import UserSettings
            
            user_settings = self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id,
                UserSettings.category == "knowledgebase"
            ).first()
            
            if user_settings and user_settings.settings:
                settings = KnowledgebaseUserSettings.from_dict(user_settings.settings)
            else:
                settings = KnowledgebaseUserSettings()
            
            # 캐시에 저장
            self._cache[user_id] = settings
            
            return settings
            
        except Exception as e:
            logger.warning(f"Failed to get user settings: {e}")
            return KnowledgebaseUserSettings()
    
    def update_user_settings(
        self,
        user_id: str,
        settings: KnowledgebaseUserSettings
    ) -> KnowledgebaseUserSettings:
        """
        사용자 설정 업데이트.
        
        Args:
            user_id: 사용자 ID
            settings: 새 설정
            
        Returns:
            업데이트된 설정
        """
        try:
            from backend.db.models.user_settings import UserSettings
            
            # 기존 설정 조회
            user_settings = self.db.query(UserSettings).filter(
                UserSettings.user_id == user_id,
                UserSettings.category == "knowledgebase"
            ).first()
            
            if user_settings:
                # 업데이트
                user_settings.settings = settings.to_dict()
                user_settings.updated_at = datetime.utcnow()
            else:
                # 새로 생성
                import uuid
                user_settings = UserSettings(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    category="knowledgebase",
                    settings=settings.to_dict()
                )
                self.db.add(user_settings)
            
            self.db.commit()
            
            # 캐시 업데이트
            self._cache[user_id] = settings
            
            logger.info(f"Updated knowledgebase settings for user {user_id}")
            
            return settings
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update user settings: {e}", exc_info=True)
            raise
    
    def reset_user_settings(self, user_id: str) -> KnowledgebaseUserSettings:
        """
        사용자 설정 초기화.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            기본 설정
        """
        default_settings = KnowledgebaseUserSettings()
        return self.update_user_settings(user_id, default_settings)
    
    def validate_settings(self, settings: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        설정 검증.
        
        Args:
            settings: 검증할 설정
            
        Returns:
            (유효 여부, 오류 메시지)
        """
        try:
            # 언어 검증
            if "preferred_language" in settings:
                PreferredLanguage(settings["preferred_language"])
            
            # 검색 모드 검증
            if "default_search_mode" in settings:
                DefaultSearchMode(settings["default_search_mode"])
            
            # 숫자 범위 검증
            if "default_top_k" in settings:
                top_k = settings["default_top_k"]
                if not (1 <= top_k <= 100):
                    return False, "default_top_k must be between 1 and 100"
            
            if "min_score_threshold" in settings:
                threshold = settings["min_score_threshold"]
                if not (0.0 <= threshold <= 1.0):
                    return False, "min_score_threshold must be between 0.0 and 1.0"
            
            if "default_chunk_size" in settings:
                chunk_size = settings["default_chunk_size"]
                if not (100 <= chunk_size <= 2000):
                    return False, "default_chunk_size must be between 100 and 2000"
            
            if "vector_weight" in settings or "bm25_weight" in settings:
                vector_w = settings.get("vector_weight", 0.6)
                bm25_w = settings.get("bm25_weight", 0.4)
                if abs((vector_w + bm25_w) - 1.0) > 0.01:
                    return False, "vector_weight + bm25_weight must equal 1.0"
            
            return True, None
            
        except ValueError as e:
            return False, str(e)


def get_knowledgebase_user_settings_service(db: Session) -> KnowledgebaseUserSettingsService:
    """서비스 인스턴스 반환"""
    return KnowledgebaseUserSettingsService(db)
