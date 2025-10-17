"""
Audio Processor for Multimodal RAG

음성 RAG 처리:
- 직접 오디오 임베딩 (WavRAG 스타일)
- 음성 정보 보존
- 고성능 검색
- 한국어 최적화
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List
from pathlib import Path
import torch

logger = logging.getLogger(__name__)


class AudioProcessor:
    """
    음성 처리기 (WavRAG 스타일)
    
    Features:
    - 직접 오디오 임베딩 (텍스트 변환 없이)
    - 음성 특징 보존 (억양, 감정, 화자 등)
    - 고성능 검색
    - 한국어 최적화
    """
    
    def __init__(
        self,
        model_name: str = "openai/whisper-large-v3",
        use_gpu: bool = True,
        language: str = "ko"
    ):
        """
        초기화
        
        Args:
            model_name: 오디오 인코더 모델
            use_gpu: GPU 사용 여부
            language: 언어 (ko, en)
        """
        self.model_name = model_name
        self.use_gpu = use_gpu and torch.cuda.is_available()
        self.language = language
        
        self.model = None
        self.processor = None
        self.device = None
        
        # Lazy loading
        self._init_model()
        
        logger.info(
            f"AudioProcessor initialized: model={model_name}, "
            f"gpu={self.use_gpu}, language={language}"
        )
    
    def _init_model(self):
        """모델 초기화"""
        try:
            from transformers import WhisperProcessor, WhisperModel
            
            # 디바이스 설정
            self.device = torch.device("cuda" if self.use_gpu else "cpu")
            
            logger.info(f"Loading audio model: {self.model_name}")
            
            # Whisper 모델 로드 (인코더만 사용)
            self.processor = WhisperProcessor.from_pretrained(self.model_name)
            self.model = WhisperModel.from_pretrained(self.model_name).to(self.device)
            self.model.eval()
            
            logger.info(f"Audio model loaded successfully on {self.device}")
            
        except ImportError:
            logger.error(
                "Transformers not installed. Install with: "
                "pip install transformers"
            )
            raise ImportError(
                "Transformers not installed. Please install: pip install transformers"
            )
        except Exception as e:
            logger.error(f"Failed to initialize audio model: {e}")
            raise
    
    def process_audio(
        self,
        audio_path: str,
        return_embeddings: bool = True,
        return_transcription: bool = False
    ) -> Dict[str, Any]:
        """
        오디오 처리 및 임베딩 생성
        
        Args:
            audio_path: 오디오 파일 경로
            return_embeddings: 임베딩 반환 여부
            return_transcription: 텍스트 변환 반환 여부
        
        Returns:
            {
                'embeddings': np.ndarray,  # 오디오 임베딩
                'transcription': str,      # 텍스트 변환 (선택)
                'duration': float,         # 오디오 길이 (초)
                'sample_rate': int,        # 샘플링 레이트
                'method': str,             # 'audio_rag'
                'confidence': float        # 신뢰도
            }
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio not found: {audio_path}")
        
        try:
            # 오디오 로드
            import librosa
            
            audio, sample_rate = librosa.load(
                audio_path,
                sr=16000,  # Whisper는 16kHz 사용
                mono=True
            )
            
            duration = len(audio) / sample_rate
            
            logger.info(f"Processing audio: {Path(audio_path).name} ({duration:.2f}s)")
            
            # 전처리
            inputs = self.processor(
                audio,
                sampling_rate=sample_rate,
                return_tensors="pt"
            ).to(self.device)
            
            # 임베딩 생성 (인코더만 사용)
            with torch.no_grad():
                # Whisper 인코더 출력
                encoder_outputs = self.model.encoder(
                    inputs.input_features,
                    return_dict=True
                )
                
                # 평균 풀링으로 고정 크기 임베딩 생성
                embeddings = encoder_outputs.last_hidden_state.mean(dim=1)
                embeddings = embeddings.cpu().numpy()
            
            result = {
                'embeddings': embeddings if return_embeddings else None,
                'duration': duration,
                'sample_rate': sample_rate,
                'method': 'audio_rag',
                'confidence': 0.9,  # 직접 임베딩은 높은 신뢰도
                'metadata': {
                    'model': self.model_name,
                    'device': str(self.device),
                    'language': self.language
                }
            }
            
            # 텍스트 변환 (선택)
            if return_transcription:
                transcription = self._transcribe(audio, sample_rate)
                result['transcription'] = transcription
            
            logger.info(
                f"Audio processed: {embeddings.shape if return_embeddings else 'N/A'}, "
                f"{duration:.2f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Audio processing failed for {audio_path}: {e}")
            raise
    
    def _transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        오디오를 텍스트로 변환 (선택적)
        
        Args:
            audio: 오디오 데이터
            sample_rate: 샘플링 레이트
        
        Returns:
            텍스트 변환 결과
        """
        try:
            from transformers import pipeline
            
            # Whisper ASR 파이프라인
            transcriber = pipeline(
                "automatic-speech-recognition",
                model=self.model_name,
                device=0 if self.use_gpu else -1
            )
            
            result = transcriber(
                audio,
                generate_kwargs={"language": self.language}
            )
            
            return result["text"]
            
        except Exception as e:
            logger.warning(f"Transcription failed: {e}")
            return ""
    
    def extract_audio_features(
        self,
        audio_path: str
    ) -> Dict[str, Any]:
        """
        오디오 특징 추출 (음성 분석용)
        
        Args:
            audio_path: 오디오 파일 경로
        
        Returns:
            오디오 특징 (MFCC, 스펙트로그램 등)
        """
        try:
            import librosa
            
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # MFCC (Mel-frequency cepstral coefficients)
            mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            
            # 스펙트럴 특징
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            
            # 제로 크로싱 레이트
            zcr = librosa.feature.zero_crossing_rate(audio)
            
            # 에너지
            rms = librosa.feature.rms(y=audio)
            
            features = {
                'mfcc_mean': mfcc.mean(axis=1).tolist(),
                'mfcc_std': mfcc.std(axis=1).tolist(),
                'spectral_centroid_mean': float(spectral_centroid.mean()),
                'spectral_rolloff_mean': float(spectral_rolloff.mean()),
                'zcr_mean': float(zcr.mean()),
                'rms_mean': float(rms.mean())
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return {}
    
    def is_available(self) -> bool:
        """오디오 프로세서 사용 가능 여부"""
        return self.model is not None and self.processor is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_name': self.model_name,
            'device': str(self.device) if self.device else 'cpu',
            'gpu_available': torch.cuda.is_available(),
            'gpu_used': self.use_gpu,
            'language': self.language,
            'available': self.is_available()
        }


# Global instance
_audio_processor: Optional[AudioProcessor] = None


def get_audio_processor(
    model_name: str = "openai/whisper-large-v3",
    use_gpu: bool = True,
    language: str = "ko"
) -> Optional[AudioProcessor]:
    """
    Get global audio processor instance
    
    Returns None if audio processing is not available
    """
    global _audio_processor
    
    if _audio_processor is None:
        try:
            _audio_processor = AudioProcessor(
                model_name=model_name,
                use_gpu=use_gpu,
                language=language
            )
        except Exception as e:
            logger.warning(f"Audio processor not available: {e}")
            return None
    
    return _audio_processor
