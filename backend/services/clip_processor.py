"""
CLIP Processor for Cross-Modal Search

CLIP (Contrastive Language-Image Pre-training) 기반 크로스 모달 검색:
- 텍스트 → 이미지 검색
- 이미지 → 텍스트 검색
- 통합 임베딩 공간
- 한국어 최적화 (multilingual-clip)
"""

import logging
import torch
import numpy as np
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class CLIPProcessor:
    """
    CLIP 기반 크로스 모달 프로세서
    
    Features:
    - 텍스트-이미지 통합 임베딩
    - 크로스 모달 검색
    - 배치 처리
    - GPU 가속
    - 한국어 지원
    """
    
    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        use_gpu: bool = True,
        embedding_dim: int = 512
    ):
        """
        초기화
        
        Args:
            model_name: CLIP 모델 이름
            use_gpu: GPU 사용 여부
            embedding_dim: 임베딩 차원
        """
        self.model_name = model_name
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.embedding_dim = embedding_dim
        
        self.model = None
        self.processor = None
        self.device = None
        
        # Lazy loading
        self._init_model()
        
        logger.info(
            f"CLIPProcessor initialized: model={model_name}, "
            f"gpu={self.use_gpu}, dim={embedding_dim}"
        )
    
    def _init_model(self):
        """모델 초기화"""
        try:
            from transformers import CLIPProcessor as HFCLIPProcessor, CLIPModel
            
            # 디바이스 설정
            self.device = torch.device("cuda" if self.use_gpu else "cpu")
            
            logger.info(f"Loading CLIP model: {self.model_name}")
            
            # CLIP 모델 로드
            self.model = CLIPModel.from_pretrained(self.model_name).to(self.device)
            self.processor = HFCLIPProcessor.from_pretrained(self.model_name)
            self.model.eval()
            
            logger.info(f"CLIP model loaded successfully on {self.device}")
            
        except ImportError:
            logger.error(
                "Transformers not installed. Install with: "
                "pip install transformers"
            )
            raise ImportError(
                "Transformers not installed. Please install: pip install transformers"
            )
        except Exception as e:
            logger.error(f"Failed to initialize CLIP model: {e}")
            raise
    
    def encode_text(
        self,
        texts: Union[str, List[str]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        텍스트 임베딩 생성
        
        Args:
            texts: 텍스트 또는 텍스트 리스트
            normalize: L2 정규화 여부
        
        Returns:
            텍스트 임베딩 (N, D)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            # 전처리
            inputs = self.processor(
                text=texts,
                return_tensors="pt",
                padding=True,
                truncation=True
            ).to(self.device)
            
            # 임베딩 생성
            with torch.no_grad():
                text_features = self.model.get_text_features(**inputs)
            
            # 정규화
            if normalize:
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
            
            # CPU로 이동 및 numpy 변환
            embeddings = text_features.cpu().numpy()
            
            logger.debug(f"Text embeddings generated: {embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Text encoding failed: {e}")
            raise
    
    def encode_image(
        self,
        images: Union[str, List[str], Image.Image, List[Image.Image]],
        normalize: bool = True
    ) -> np.ndarray:
        """
        이미지 임베딩 생성
        
        Args:
            images: 이미지 경로, PIL 이미지, 또는 리스트
            normalize: L2 정규화 여부
        
        Returns:
            이미지 임베딩 (N, D)
        """
        # 이미지 로드
        if isinstance(images, (str, Path)):
            images = [Image.open(images).convert("RGB")]
        elif isinstance(images, Image.Image):
            images = [images]
        elif isinstance(images, list):
            loaded_images = []
            for img in images:
                if isinstance(img, (str, Path)):
                    loaded_images.append(Image.open(img).convert("RGB"))
                elif isinstance(img, Image.Image):
                    loaded_images.append(img)
                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")
            images = loaded_images
        else:
            raise ValueError(f"Unsupported images type: {type(images)}")
        
        try:
            # 전처리
            inputs = self.processor(
                images=images,
                return_tensors="pt"
            ).to(self.device)
            
            # 임베딩 생성
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
            
            # 정규화
            if normalize:
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            # CPU로 이동 및 numpy 변환
            embeddings = image_features.cpu().numpy()
            
            logger.debug(f"Image embeddings generated: {embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Image encoding failed: {e}")
            raise
    
    def compute_similarity(
        self,
        text_embeddings: np.ndarray,
        image_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        텍스트-이미지 유사도 계산
        
        Args:
            text_embeddings: 텍스트 임베딩 (M, D)
            image_embeddings: 이미지 임베딩 (N, D)
        
        Returns:
            유사도 행렬 (M, N)
        """
        try:
            # 코사인 유사도 (정규화된 경우 내적과 동일)
            similarity = np.dot(text_embeddings, image_embeddings.T)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            raise
    
    def search_images_with_text(
        self,
        query_text: str,
        image_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        텍스트 쿼리로 이미지 검색
        
        Args:
            query_text: 검색 쿼리
            image_embeddings: 이미지 임베딩 (N, D)
            top_k: 반환할 결과 수
        
        Returns:
            검색 결과 (인덱스, 점수)
        """
        try:
            # 텍스트 임베딩 생성
            text_embedding = self.encode_text(query_text)
            
            # 유사도 계산
            similarities = self.compute_similarity(text_embedding, image_embeddings)[0]
            
            # Top-K 선택
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append({
                    'index': int(idx),
                    'score': float(similarities[idx])
                })
            
            logger.info(f"Text-to-image search: {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Text-to-image search failed: {e}")
            raise
    
    def search_text_with_image(
        self,
        query_image: Union[str, Image.Image],
        text_embeddings: np.ndarray,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        이미지 쿼리로 텍스트 검색
        
        Args:
            query_image: 검색 이미지
            text_embeddings: 텍스트 임베딩 (N, D)
            top_k: 반환할 결과 수
        
        Returns:
            검색 결과 (인덱스, 점수)
        """
        try:
            # 이미지 임베딩 생성
            image_embedding = self.encode_image(query_image)
            
            # 유사도 계산
            similarities = self.compute_similarity(text_embeddings, image_embedding).T[0]
            
            # Top-K 선택
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                results.append({
                    'index': int(idx),
                    'score': float(similarities[idx])
                })
            
            logger.info(f"Image-to-text search: {len(results)} results")
            
            return results
            
        except Exception as e:
            logger.error(f"Image-to-text search failed: {e}")
            raise
    
    def batch_encode_texts(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        배치 텍스트 임베딩 생성
        
        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기
        
        Returns:
            텍스트 임베딩 (N, D)
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            embeddings = self.encode_text(batch_texts)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)
    
    def batch_encode_images(
        self,
        images: List[Union[str, Image.Image]],
        batch_size: int = 16
    ) -> np.ndarray:
        """
        배치 이미지 임베딩 생성
        
        Args:
            images: 이미지 리스트
            batch_size: 배치 크기
        
        Returns:
            이미지 임베딩 (N, D)
        """
        all_embeddings = []
        
        for i in range(0, len(images), batch_size):
            batch_images = images[i:i + batch_size]
            embeddings = self.encode_image(batch_images)
            all_embeddings.append(embeddings)
        
        return np.vstack(all_embeddings)
    
    def is_available(self) -> bool:
        """CLIP 사용 가능 여부"""
        return self.model is not None and self.processor is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_name': self.model_name,
            'device': str(self.device) if self.device else 'cpu',
            'gpu_available': torch.cuda.is_available(),
            'gpu_used': self.use_gpu,
            'embedding_dim': self.embedding_dim,
            'available': self.is_available()
        }


# Global instance
_clip_processor: Optional[CLIPProcessor] = None


def get_clip_processor(
    model_name: str = "openai/clip-vit-base-patch32",
    use_gpu: bool = True,
    embedding_dim: int = 512
) -> Optional[CLIPProcessor]:
    """
    Get global CLIP processor instance
    
    Returns None if CLIP is not available
    """
    global _clip_processor
    
    if _clip_processor is None:
        try:
            _clip_processor = CLIPProcessor(
                model_name=model_name,
                use_gpu=use_gpu,
                embedding_dim=embedding_dim
            )
        except Exception as e:
            logger.warning(f"CLIP processor not available: {e}")
            return None
    
    return _clip_processor
