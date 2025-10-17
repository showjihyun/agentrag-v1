"""
Korean Text Preprocessor - 한글 문서 전처리 최적화

Features:
- 빠른 텍스트 정규화
- 문서 타입별 최적화
- 배치 처리 지원
- 캐싱 메커니즘
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import unicodedata

logger = logging.getLogger(__name__)


class KoreanPreprocessor:
    """
    한글 문서 전처리 최적화
    
    성능 개선:
    - 정규표현식 컴파일 캐싱
    - 유니코드 정규화
    - 불필요한 처리 스킵
    - 배치 처리 지원
    """
    
    def __init__(self):
        # 정규표현식 미리 컴파일 (성능 향상)
        self.patterns = self._compile_patterns()
        
        # 문서 타입별 설정
        self.doc_type_configs = {
            'hwp': {'normalize_spacing': True, 'remove_hanja': True},
            'hwpx': {'normalize_spacing': True, 'remove_hanja': True},
            'pptx': {'normalize_spacing': False, 'remove_hanja': False},
            'xlsx': {'normalize_spacing': False, 'remove_hanja': False},
            'txt': {'normalize_spacing': True, 'remove_hanja': True},
        }
        
        logger.info("KoreanPreprocessor initialized with optimized patterns")
    
    def _compile_patterns(self) -> Dict:
        """정규표현식 패턴 미리 컴파일"""
        return {
            # 한자 감지
            'hanja': re.compile(r'[\u4E00-\u9FFF]'),
            
            # 한글 감지
            'hangul': re.compile(r'[\uAC00-\uD7A3]'),
            
            # 공백 정규화
            'multiple_spaces': re.compile(r'\s{2,}'),
            'space_before_punct': re.compile(r'\s+([,.!?;:)])'),
            'space_after_punct': re.compile(r'([,.!?;:])\s*'),
            
            # 특수 문자
            'fullwidth_space': re.compile(r'　'),
            'special_quotes': re.compile(r'[""'']'),
            'special_dashes': re.compile(r'[—–―]'),
            
            # 이메일/URL 보호
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'url': re.compile(r'https?://[^\s]+'),
            
            # 하이픈 패턴
            'hyphen_spaces': re.compile(r'\s*-\s*'),
            
            # 괄호 패턴
            'paren_spaces': re.compile(r'\s*([()[\]{}])\s*'),
        }
    
    def preprocess(
        self, 
        text: str, 
        doc_type: str = 'txt',
        fast_mode: bool = False
    ) -> Dict:
        """
        텍스트 전처리
        
        Args:
            text: 원본 텍스트
            doc_type: 문서 타입 (hwp, hwpx, pptx, xlsx, txt)
            fast_mode: 빠른 모드 (최소 처리만)
        
        Returns:
            {
                'text': str,           # 처리된 텍스트
                'stats': Dict,         # 통계 정보
                'is_korean': bool      # 한글 문서 여부
            }
        """
        if not text or not text.strip():
            return {'text': '', 'stats': {}, 'is_korean': False}
        
        original_length = len(text)
        
        # 1. 유니코드 정규화 (빠름)
        text = unicodedata.normalize('NFC', text)
        
        # 2. 한글 문서 여부 확인
        is_korean = self._is_korean_text(text)
        
        # 3. 문서 타입별 설정
        config = self.doc_type_configs.get(doc_type, {})
        
        # 4. 기본 정규화 (항상 수행)
        text = self._basic_normalize(text)
        
        if fast_mode:
            # 빠른 모드: 최소 처리만
            return {
                'text': text,
                'stats': {
                    'original_length': original_length,
                    'processed_length': len(text),
                    'reduction_ratio': 1 - len(text) / original_length if original_length > 0 else 0
                },
                'is_korean': is_korean
            }
        
        # 5. 한글 특화 처리 (한글 문서인 경우)
        if is_korean:
            if config.get('remove_hanja', False):
                text = self._handle_hanja(text)
            
            if config.get('normalize_spacing', False):
                text = self._normalize_korean_spacing(text)
        
        # 6. 통계 수집
        stats = {
            'original_length': original_length,
            'processed_length': len(text),
            'reduction_ratio': 1 - len(text) / original_length if original_length > 0 else 0,
            'has_hanja': bool(self.patterns['hanja'].search(text)),
            'hangul_ratio': self._calculate_hangul_ratio(text)
        }
        
        return {
            'text': text,
            'stats': stats,
            'is_korean': is_korean
        }
    
    def _basic_normalize(self, text: str) -> str:
        """기본 정규화 (빠른 처리)"""
        # 전각 공백 → 반각 공백
        text = self.patterns['fullwidth_space'].sub(' ', text)
        
        # 특수 따옴표 정규화
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # 특수 대시 정규화
        text = self.patterns['special_dashes'].sub('-', text)
        
        # 연속 공백 제거
        text = self.patterns['multiple_spaces'].sub(' ', text)
        
        return text.strip()
    
    def _normalize_korean_spacing(self, text: str) -> str:
        """한글 띄어쓰기 정규화"""
        # 이메일/URL 보호
        protected_patterns = []
        
        # 이메일 보호
        for match in self.patterns['email'].finditer(text):
            placeholder = f"__EMAIL_{len(protected_patterns)}__"
            protected_patterns.append((placeholder, match.group()))
            text = text.replace(match.group(), placeholder)
        
        # URL 보호
        for match in self.patterns['url'].finditer(text):
            placeholder = f"__URL_{len(protected_patterns)}__"
            protected_patterns.append((placeholder, match.group()))
            text = text.replace(match.group(), placeholder)
        
        # 하이픈 앞뒤 공백 제거
        text = self.patterns['hyphen_spaces'].sub('-', text)
        
        # @ 앞뒤 공백 제거
        text = re.sub(r'\s*@\s*', '@', text)
        
        # 점 앞뒤 공백 제거 (이메일/URL 제외)
        text = re.sub(r'\.\s+(?=[a-z0-9])', '.', text)
        text = re.sub(r'(?<=[a-z0-9])\s+\.', '.', text)
        
        # 문장 부호 정리
        text = self.patterns['space_before_punct'].sub(r'\1', text)
        text = self.patterns['space_after_punct'].sub(r'\1 ', text)
        
        # 괄호 정리
        text = re.sub(r'\s*\(\s*', ' (', text)
        text = re.sub(r'\s*\)\s*', ') ', text)
        
        # 보호된 패턴 복원
        for placeholder, original in protected_patterns:
            text = text.replace(placeholder, original)
        
        # 최종 공백 정리
        text = self.patterns['multiple_spaces'].sub(' ', text)
        
        return text.strip()
    
    def _handle_hanja(self, text: str) -> str:
        """한자 처리 (괄호로 표시)"""
        # 한자를 괄호로 감싸기
        def replace_hanja(match):
            hanja = match.group()
            return f"({hanja})"
        
        return self.patterns['hanja'].sub(replace_hanja, text)
    
    @lru_cache(maxsize=1000)
    def _is_korean_text(self, text: str) -> bool:
        """한글 텍스트 여부 확인 (캐싱)"""
        if not text:
            return False
        
        # 샘플링으로 빠르게 확인 (긴 텍스트의 경우)
        sample = text[:1000] if len(text) > 1000 else text
        
        hangul_count = len(self.patterns['hangul'].findall(sample))
        total_chars = len([c for c in sample if c.isalnum()])
        
        if total_chars == 0:
            return False
        
        return (hangul_count / total_chars) >= 0.3  # 30% 이상이면 한글 문서
    
    def _calculate_hangul_ratio(self, text: str) -> float:
        """한글 비율 계산"""
        if not text:
            return 0.0
        
        hangul_count = len(self.patterns['hangul'].findall(text))
        total_chars = len([c for c in text if c.isalnum()])
        
        if total_chars == 0:
            return 0.0
        
        return hangul_count / total_chars
    
    def batch_preprocess(
        self, 
        texts: List[str], 
        doc_type: str = 'txt'
    ) -> List[Dict]:
        """
        배치 전처리 (여러 텍스트 동시 처리)
        
        Args:
            texts: 텍스트 리스트
            doc_type: 문서 타입
        
        Returns:
            List[Dict]: 처리 결과 리스트
        """
        results = []
        
        for text in texts:
            result = self.preprocess(text, doc_type=doc_type)
            results.append(result)
        
        return results


# Global instance
_korean_preprocessor: Optional[KoreanPreprocessor] = None


def get_korean_preprocessor() -> KoreanPreprocessor:
    """Get global Korean preprocessor instance"""
    global _korean_preprocessor
    if _korean_preprocessor is None:
        _korean_preprocessor = KoreanPreprocessor()
    return _korean_preprocessor
