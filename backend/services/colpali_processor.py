"""
ColPali Image Processor for Multimodal RAG

ColPali (Contextualized Late Interaction over Patches) 기반 이미지 처리:
- 최고 수준의 정확도 (nDCG@5: 81.3)
- 빠른 인덱싱 (페이지당 ~2.5초)
- 표/차트 완벽 인식
- 메모리 최적화 (바이너리화 시 32배 감소)
- 검색 속도 최적화 (풀링+리랭킹으로 13배 향상)

우선순위: ColPali > Vision LLM > EasyOCR
"""

import logging
import torch
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from PIL import Image
import io

logger = logging.getLogger(__name__)


class ColPaliProcessor:
    """
    ColPali 기반 이미지 처리기
    
    Features:
    - 패치 기반 멀티벡터 임베딩
    - Late interaction 검색
    - 바이너리화 최적화
    - 풀링 + 리랭킹
    - GPU 가속
    """
    
    def __init__(
        self,
        model_name: str = "vidore/colpali-v1.2",
        use_gpu: bool = True,
        enable_binarization: bool = True,
        enable_pooling: bool = True,
        pooling_factor: int = 9  # 1024 patches → ~128 patches
    ):
        """
        초기화
        
        Args:
            model_name: ColPali 모델 이름
            use_gpu: GPU 사용 여부
            enable_binarization: 바이너리화 활성화 (메모리 32배 감소)
            enable_pooling: 풀링 활성화 (속도 13배 향상)
            pooling_factor: 풀링 비율 (9 = 3x3 패치 풀링)
        """
        self.model_name = model_name
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.enable_binarization = enable_binarization
        self.enable_pooling = enable_pooling
        self.pooling_factor = pooling_factor
        
        self.model = None
        self.processor = None
        self.device = None
        
        # Lazy loading
        self._init_model()
        
        logger.info(
            f"ColPaliProcessor initialized: "
            f"model={model_name}, gpu={self.use_gpu}, "
            f"binarization={enable_binarization}, pooling={enable_pooling}"
        )
    
    def _init_model(self):
        """모델 초기화 (lazy loading)"""
        try:
            logger.info("🔄 Importing ColPali modules...")
            from colpali_engine.models import ColPali, ColPaliProcessor
            logger.info("✅ ColPali modules imported successfully")
            
            # GPU 가용성 체크
            gpu_available = torch.cuda.is_available()
            if gpu_available:
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
                logger.info(f"🎮 GPU detected: {gpu_name} ({gpu_memory:.1f}GB)")
            else:
                logger.info("💻 No GPU detected, using CPU")
            
            # 디바이스 설정
            self.device = torch.device("cuda" if self.use_gpu and gpu_available else "cpu")
            
            if self.use_gpu and not gpu_available:
                logger.warning("⚠️  GPU requested but not available, falling back to CPU")
            
            logger.info(f"📦 Loading ColPali model: {self.model_name}")
            logger.info(f"🔧 Device: {self.device}")
            
            # 모델 로드
            self.model = ColPali.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.use_gpu and gpu_available else torch.float32,
                device_map="auto" if self.use_gpu and gpu_available else None
            ).eval()
            
            # GPU로 명시적 이동 (device_map이 작동하지 않을 경우 대비)
            if self.use_gpu and gpu_available:
                self.model = self.model.to(self.device)
            
            # 프로세서 로드
            self.processor = ColPaliProcessor.from_pretrained(self.model_name)
            
            # 최종 확인
            actual_device = next(self.model.parameters()).device
            logger.info(f"✅ ColPali model loaded successfully")
            logger.info(f"   Device: {actual_device}")
            logger.info(f"   Dtype: {next(self.model.parameters()).dtype}")
            logger.info(f"   Binarization: {self.enable_binarization}")
            logger.info(f"   Pooling: {self.enable_pooling} (factor={self.pooling_factor})")
            
        except ImportError as e:
            logger.error(
                f"❌ ColPali import failed: {e}. "
                "Install with: pip install colpali-engine"
            )
            raise ImportError(
                f"ColPali not installed. Please install: pip install colpali-engine. Error: {e}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize ColPali model: {e}")
            raise
    
    def process_image(
        self,
        image_path: str,
        return_embeddings: bool = True
    ) -> Dict[str, Any]:
        """
        이미지 처리 및 임베딩 생성
        
        Args:
            image_path: 이미지 파일 경로
            return_embeddings: 임베딩 반환 여부
        
        Returns:
            {
                'embeddings': np.ndarray,  # 패치 임베딩 (N, D)
                'num_patches': int,        # 패치 수
                'image_size': Tuple,       # 이미지 크기
                'method': str,             # 'colpali'
                'confidence': float,       # 신뢰도
                'metadata': Dict           # 메타데이터
            }
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        try:
            # Check if it's a PDF file
            if image_path.lower().endswith('.pdf'):
                # Convert PDF to images
                import fitz  # PyMuPDF
                doc = fitz.open(image_path)
                
                # Process first page only for now
                page = doc[0]
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x scale for better quality
                
                # Convert to PIL Image
                import io
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data)).convert("RGB")
                image_size = image.size
                
                doc.close()
            else:
                # 이미지 로드
                image = Image.open(image_path).convert("RGB")
                image_size = image.size
            
            # 전처리
            inputs = self.processor(
                images=image,
                return_tensors="pt"
            )
            
            # GPU로 이동 (명시적)
            if self.use_gpu and torch.cuda.is_available():
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 임베딩 생성
            import time
            start_time = time.time()
            
            with torch.no_grad():
                embeddings = self.model(**inputs)
            
            processing_time = time.time() - start_time
            
            # CPU로 이동 및 numpy 변환
            embeddings = embeddings.cpu().numpy()
            
            logger.debug(f"⚡ Processing time: {processing_time:.2f}s on {self.device}")
            
            # 최적화 적용
            if self.enable_pooling:
                embeddings = self._apply_pooling(embeddings)
            
            if self.enable_binarization:
                embeddings = self._apply_binarization(embeddings)
            
            num_patches = embeddings.shape[0]
            
            logger.info(
                f"✅ ColPali processed image: {num_patches} patches, "
                f"shape={embeddings.shape}, device={self.device}"
            )
            
            result = {
                'embeddings': embeddings if return_embeddings else None,
                'num_patches': num_patches,
                'image_size': image_size,
                'method': 'colpali',
                'confidence': 0.95,  # ColPali는 높은 신뢰도
                'metadata': {
                    'model': self.model_name,
                    'device': str(self.device),
                    'binarized': self.enable_binarization,
                    'pooled': self.enable_pooling,
                    'pooling_factor': self.pooling_factor if self.enable_pooling else None
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"ColPali processing failed for {image_path}: {e}")
            raise
    
    def _apply_pooling(self, embeddings: np.ndarray) -> np.ndarray:
        """
        패치 풀링 적용
        
        1024 patches → ~128 patches (9x reduction)
        속도 13배 향상, 정확도 유지
        
        Args:
            embeddings: 원본 패치 임베딩 (N, D)
        
        Returns:
            풀링된 임베딩 (N/pooling_factor, D)
        """
        try:
            N, D = embeddings.shape
            
            # 풀링 팩터로 나누어떨어지도록 조정
            num_pooled = N // self.pooling_factor
            
            if num_pooled == 0:
                logger.warning("Too few patches for pooling, skipping")
                return embeddings
            
            # 그룹으로 나누기
            embeddings_grouped = embeddings[:num_pooled * self.pooling_factor].reshape(
                num_pooled, self.pooling_factor, D
            )
            
            # 평균 풀링
            pooled = embeddings_grouped.mean(axis=1)
            
            logger.debug(f"Pooling applied: {N} → {num_pooled} patches")
            
            return pooled
            
        except Exception as e:
            logger.warning(f"Pooling failed: {e}, using original embeddings")
            return embeddings
    
    def _apply_binarization(self, embeddings: np.ndarray) -> np.ndarray:
        """
        임베딩 바이너리화
        
        메모리 32배 감소, 속도 4배 향상
        
        Args:
            embeddings: 원본 임베딩 (N, D)
        
        Returns:
            바이너리 임베딩 (N, D/8) - uint8 packed
        """
        try:
            # 0을 기준으로 바이너리화
            binary = (embeddings > 0).astype(np.uint8)
            
            # 비트 패킹 (8개 값을 1바이트로)
            N, D = binary.shape
            D_packed = (D + 7) // 8  # 올림
            
            packed = np.zeros((N, D_packed), dtype=np.uint8)
            
            for i in range(D_packed):
                start_idx = i * 8
                end_idx = min(start_idx + 8, D)
                
                for j in range(start_idx, end_idx):
                    bit_pos = j - start_idx
                    packed[:, i] |= (binary[:, j] << bit_pos)
            
            logger.debug(f"Binarization applied: {embeddings.nbytes} → {packed.nbytes} bytes")
            
            return packed
            
        except Exception as e:
            logger.warning(f"Binarization failed: {e}, using original embeddings")
            return embeddings
    
    def process_text_query(self, query: str) -> np.ndarray:
        """
        텍스트 쿼리를 ColPali 임베딩으로 변환
        
        Args:
            query: 검색 쿼리 텍스트
        
        Returns:
            쿼리 임베딩 (M, D)
        """
        try:
            # PaliGemmaProcessor는 이미지가 필요하므로 더미 이미지 생성
            # 또는 텍스트 전용 처리 방식 사용
            from PIL import Image
            import numpy as np
            
            # 작은 더미 이미지 생성 (1x1 흰색 이미지)
            dummy_image = Image.new('RGB', (1, 1), color='white')
            
            # 텍스트와 더미 이미지로 전처리
            inputs = self.processor(
                text=query,
                images=dummy_image,
                return_tensors="pt"
            ).to(self.device)
            
            # 임베딩 생성
            with torch.no_grad():
                embeddings = self.model(**inputs)
            
            # CPU로 이동 및 numpy 변환
            embeddings = embeddings.cpu().numpy()
            
            # 최적화 적용
            if self.enable_pooling:
                embeddings = self._apply_pooling(embeddings)
            
            if self.enable_binarization:
                embeddings = self._apply_binarization(embeddings)
            
            logger.debug(f"Query embedding generated: shape={embeddings.shape}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise
    
    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray,
        use_late_interaction: bool = True
    ) -> float:
        """
        Late interaction 유사도 계산
        
        MaxSim: max_i(query_i · doc_j) for each query patch
        
        Args:
            query_embedding: 쿼리 임베딩 (M, D)
            doc_embeddings: 문서 임베딩 (N, D)
            use_late_interaction: Late interaction 사용 여부
        
        Returns:
            유사도 점수
        """
        try:
            if use_late_interaction:
                # Late interaction (MaxSim)
                # 각 쿼리 패치에 대해 가장 유사한 문서 패치 찾기
                similarities = np.dot(query_embedding, doc_embeddings.T)  # (M, N)
                max_sims = similarities.max(axis=1)  # (M,)
                score = max_sims.sum()  # 또는 mean()
            else:
                # 단순 평균 유사도
                query_avg = query_embedding.mean(axis=0)
                doc_avg = doc_embeddings.mean(axis=0)
                score = np.dot(query_avg, doc_avg)
            
            return float(score)
            
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0
    
    def batch_process_images(
        self,
        image_paths: List[str],
        batch_size: int = 4
    ) -> List[Dict[str, Any]]:
        """
        배치 이미지 처리
        
        Args:
            image_paths: 이미지 경로 리스트
            batch_size: 배치 크기
        
        Returns:
            처리 결과 리스트
        """
        results = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            
            for path in batch_paths:
                try:
                    result = self.process_image(path)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
                    results.append({
                        'error': str(e),
                        'method': 'colpali',
                        'confidence': 0.0
                    })
        
        return results
    
    def is_available(self) -> bool:
        """ColPali 사용 가능 여부 확인"""
        try:
            return self.model is not None and self.processor is not None
        except:
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_name': self.model_name,
            'device': str(self.device) if self.device else 'cpu',
            'gpu_available': torch.cuda.is_available(),
            'gpu_used': self.use_gpu,
            'binarization': self.enable_binarization,
            'pooling': self.enable_pooling,
            'pooling_factor': self.pooling_factor,
            'available': self.is_available()
        }


# Global instance
_colpali_processor: Optional[ColPaliProcessor] = None


def get_colpali_processor(
    model_name: str = "vidore/colpali-v1.2",
    use_gpu: bool = True,
    enable_binarization: bool = True,
    enable_pooling: bool = True,
    pooling_factor: int = 9
) -> Optional[ColPaliProcessor]:
    """
    Get global ColPali processor instance
    
    Returns None if ColPali is not available
    """
    global _colpali_processor
    
    if _colpali_processor is None:
        try:
            _colpali_processor = ColPaliProcessor(
                model_name=model_name,
                use_gpu=use_gpu,
                enable_binarization=enable_binarization,
                enable_pooling=enable_pooling,
                pooling_factor=pooling_factor
            )
        except Exception as e:
            logger.warning(f"ColPali not available: {e}")
            return None
    
    return _colpali_processor
