"""
Korean-Optimized Knowledgebase Processor.

AgenticRAG의 한글 처리 기능을 Knowledgebase에 통합:
- 한글/영어 이중 언어 처리
- 형태소 분석 기반 토큰화
- 한글 최적화 청킹
- 하이브리드 검색 (Vector + BM25)
"""

import logging
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Detected language."""
    KOREAN = "ko"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class SearchMode(str, Enum):
    """Search modes for knowledgebase queries."""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"


@dataclass
class ChunkConfig:
    """청킹 설정"""
    target_size: int = 500
    min_size: int = 100
    max_size: int = 1000
    overlap: int = 50
    preserve_structure: bool = True


@dataclass
class SearchConfig:
    """검색 설정"""
    mode: SearchMode = SearchMode.HYBRID
    top_k: int = 10
    min_score: float = 0.3
    rerank: bool = True
    expand_query: bool = True
    vector_weight: float = 0.6
    bm25_weight: float = 0.4
    rrf_k: int = 60


@dataclass
class ProcessedChunk:
    """처리된 청크"""
    chunk_id: str
    text: str
    tokens: List[str]
    language: Language
    size: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgebaseKoreanProcessor:
    """
    한글/영어 이중 언어 Knowledgebase 처리기.
    
    Features:
    - 한글 형태소 분석 (KoNLPy)
    - 한자 → 한글 변환
    - 한글 최적화 청킹
    - 하이브리드 검색 (Vector + BM25)
    - 쿼리 확장
    """
    
    # 한글 불용어
    KOREAN_STOPWORDS = {
        # 조사
        "이", "가", "을", "를", "은", "는", "의", "에", "에서", "로", "으로",
        "와", "과", "도", "만", "까지", "부터", "에게", "한테", "께",
        # 어미
        "다", "고", "며", "면", "니", "냐", "자", "지", "요", "죠",
        # 접속사/부사
        "그리고", "그러나", "하지만", "또한", "즉", "곧", "바로",
        # 대명사
        "이것", "그것", "저것", "여기", "거기", "저기",
        # 일반적인 단어
        "것", "수", "등", "및", "때", "중", "내", "외",
    }
    
    # 영어 불용어
    ENGLISH_STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "to", "of", "in", "for", "on", "with", "at", "by", "from", "as",
        "into", "through", "during", "before", "after", "above", "below",
        "and", "but", "if", "or", "because", "until", "while", "this",
        "that", "these", "those", "what", "which", "who", "whom",
    }
    
    # 한자-한글 매핑
    HANJA_TO_HANGUL = {
        '一': '일', '二': '이', '三': '삼', '四': '사', '五': '오',
        '六': '육', '七': '칠', '八': '팔', '九': '구', '十': '십',
        '百': '백', '千': '천', '萬': '만', '億': '억',
        '大': '대', '小': '소', '中': '중', '高': '고', '低': '저',
        '新': '신', '舊': '구', '前': '전', '後': '후', '上': '상',
        '下': '하', '內': '내', '外': '외', '東': '동', '西': '서',
        '南': '남', '北': '북', '年': '년', '月': '월', '日': '일',
        '時': '시', '分': '분', '秒': '초', '國': '국', '民': '민',
    }
    
    def __init__(
        self,
        chunk_config: Optional[ChunkConfig] = None,
        search_config: Optional[SearchConfig] = None,
        use_morpheme_analysis: bool = True
    ):
        """
        Initialize Korean processor.
        
        Args:
            chunk_config: 청킹 설정
            search_config: 검색 설정
            use_morpheme_analysis: 형태소 분석 사용 여부
        """
        self.chunk_config = chunk_config or ChunkConfig()
        self.search_config = search_config or SearchConfig()
        self.use_morpheme_analysis = use_morpheme_analysis
        
        # 형태소 분석기 초기화
        self._morpheme_analyzer = None
        if use_morpheme_analysis:
            self._init_morpheme_analyzer()
        
        # BM25 인덱스 (컬렉션별)
        self._bm25_indices: Dict[str, Dict] = {}
        
        # 문장 종결 패턴
        self._sentence_endings = re.compile(
            r'([.!?])\s+|'
            r'([.!?。！？])\s*(?=[가-힣A-Z])|'
            r'([다요]\s*[.!?])\s*'
        )
        
        # 문단 구분 패턴
        self._paragraph_pattern = re.compile(r'\n\s*\n')
        
        logger.info(
            f"KnowledgebaseKoreanProcessor initialized: "
            f"morpheme={use_morpheme_analysis}, "
            f"chunk_size={self.chunk_config.target_size}"
        )
    
    def _init_morpheme_analyzer(self):
        """형태소 분석기 초기화"""
        try:
            from konlpy.tag import Okt
            self._morpheme_analyzer = Okt()
            logger.info("KoNLPy Okt initialized for morpheme analysis")
        except ImportError:
            try:
                from konlpy.tag import Mecab
                self._morpheme_analyzer = Mecab()
                logger.info("KoNLPy Mecab initialized for morpheme analysis")
            except ImportError:
                logger.warning(
                    "KoNLPy not available. Install with: pip install konlpy"
                )
                self.use_morpheme_analysis = False
    
    # =========================================================================
    # Language Detection
    # =========================================================================
    
    def detect_language(self, text: str) -> Language:
        """
        텍스트 언어 감지.
        
        Args:
            text: 입력 텍스트
            
        Returns:
            감지된 언어
        """
        if not text:
            return Language.UNKNOWN
        
        korean_count = len(re.findall(r'[가-힣]', text))
        english_count = len(re.findall(r'[a-zA-Z]', text))
        total = korean_count + english_count
        
        if total == 0:
            return Language.UNKNOWN
        
        korean_ratio = korean_count / total
        
        if korean_ratio > 0.7:
            return Language.KOREAN
        elif korean_ratio < 0.3:
            return Language.ENGLISH
        else:
            return Language.MIXED
    
    # =========================================================================
    # Text Preprocessing
    # =========================================================================
    
    def preprocess_text(self, text: str) -> str:
        """
        텍스트 전처리.
        
        Args:
            text: 원본 텍스트
            
        Returns:
            전처리된 텍스트
        """
        if not text:
            return ""
        
        # 1. 유니코드 정규화
        import unicodedata
        text = unicodedata.normalize('NFC', text)
        
        # 2. 한자 변환
        text = self._convert_hanja(text)
        
        # 3. 특수 문자 정규화
        text = self._normalize_special_chars(text)
        
        # 4. 띄어쓰기 정규화
        text = self._normalize_spacing(text)
        
        return text.strip()
    
    def _convert_hanja(self, text: str) -> str:
        """한자를 한글로 변환"""
        for hanja, hangul in self.HANJA_TO_HANGUL.items():
            text = text.replace(hanja, hangul)
        return text
    
    def _normalize_special_chars(self, text: str) -> str:
        """특수 문자 정규화"""
        # 전각 → 반각
        replacements = {
            '　': ' ', '（': '(', '）': ')', '［': '[', '］': ']',
            '｛': '{', '｝': '}', '"': '"', '"': '"', ''': "'", ''': "'",
            '—': '-', '–': '-', '―': '-'
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # 연속 공백 제거
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _normalize_spacing(self, text: str) -> str:
        """띄어쓰기 정규화"""
        # 하이픈 앞뒤 공백 제거
        text = re.sub(r'\s*-\s*', '-', text)
        # @ 앞뒤 공백 제거 (이메일)
        text = re.sub(r'\s*@\s*', '@', text)
        # 점 앞뒤 공백 제거 (도메인)
        text = re.sub(r'\.\s+(?=[a-z0-9])', '.', text)
        # 괄호 앞 공백 제거
        text = re.sub(r'\s+([)\]},.!?;:])', r'\1', text)
        return text
    
    # =========================================================================
    # Tokenization
    # =========================================================================
    
    def tokenize(
        self,
        text: str,
        extract_nouns: bool = False
    ) -> Tuple[List[str], Language]:
        """
        텍스트 토큰화.
        
        Args:
            text: 입력 텍스트
            extract_nouns: 명사만 추출할지 여부
            
        Returns:
            (토큰 리스트, 언어)
        """
        language = self.detect_language(text)
        
        if language == Language.KOREAN:
            tokens = self._tokenize_korean(text, extract_nouns)
        elif language == Language.ENGLISH:
            tokens = self._tokenize_english(text)
        elif language == Language.MIXED:
            tokens = self._tokenize_mixed(text, extract_nouns)
        else:
            tokens = text.lower().split()
        
        return tokens, language
    
    def _tokenize_korean(self, text: str, extract_nouns: bool) -> List[str]:
        """한글 토큰화"""
        if self._morpheme_analyzer and self.use_morpheme_analysis:
            try:
                if extract_nouns:
                    tokens = self._morpheme_analyzer.nouns(text)
                else:
                    pos_tags = self._morpheme_analyzer.pos(text)
                    # 의미있는 품사만 추출
                    meaningful_pos = {'Noun', 'Verb', 'Adjective', 'Adverb'}
                    tokens = [
                        word for word, pos in pos_tags
                        if pos in meaningful_pos or pos.startswith('N')
                    ]
                
                # 불용어 제거
                tokens = [
                    t for t in tokens
                    if t not in self.KOREAN_STOPWORDS and len(t) > 1
                ]
                return tokens
                
            except Exception as e:
                logger.warning(f"Korean tokenization failed: {e}")
        
        # Fallback: 단순 토큰화
        tokens = re.findall(r'[가-힣]+|[a-zA-Z]+|\d+', text)
        return [t for t in tokens if t not in self.KOREAN_STOPWORDS and len(t) > 1]
    
    def _tokenize_english(self, text: str) -> List[str]:
        """영어 토큰화"""
        tokens = re.findall(r'\b[a-z]+\b', text.lower())
        return [t for t in tokens if t not in self.ENGLISH_STOPWORDS and len(t) > 2]
    
    def _tokenize_mixed(self, text: str, extract_nouns: bool) -> List[str]:
        """혼합 텍스트 토큰화"""
        korean_parts = re.findall(r'[가-힣]+', text)
        english_parts = re.findall(r'[a-zA-Z]+', text)
        
        tokens = []
        
        if korean_parts:
            korean_text = ' '.join(korean_parts)
            tokens.extend(self._tokenize_korean(korean_text, extract_nouns))
        
        if english_parts:
            english_text = ' '.join(english_parts)
            tokens.extend(self._tokenize_english(english_text))
        
        return tokens
    
    # =========================================================================
    # Chunking
    # =========================================================================
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ProcessedChunk]:
        """
        텍스트를 청크로 분할.
        
        Args:
            text: 원본 텍스트
            metadata: 메타데이터
            
        Returns:
            청크 리스트
        """
        if not text or not text.strip():
            return []
        
        # 전처리
        text = self.preprocess_text(text)
        language = self.detect_language(text)
        
        # 구조 기반 청킹
        if self.chunk_config.preserve_structure:
            raw_chunks = self._chunk_by_structure(text)
        else:
            raw_chunks = self._chunk_by_size(text)
        
        # ProcessedChunk 생성
        chunks = []
        for idx, chunk_text in enumerate(raw_chunks):
            tokens, _ = self.tokenize(chunk_text, extract_nouns=True)
            
            chunk = ProcessedChunk(
                chunk_id=f"chunk_{idx}_{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}",
                text=chunk_text,
                tokens=tokens,
                language=language,
                size=len(chunk_text),
                metadata=metadata or {}
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from text ({language.value})")
        return chunks
    
    def _chunk_by_structure(self, text: str) -> List[str]:
        """구조 기반 청킹"""
        chunks = []
        paragraphs = self._paragraph_pattern.split(text)
        
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > self.chunk_config.max_size:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                
                # 오버랩 처리
                if self.chunk_config.overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    if len(overlap_text) <= self.chunk_config.overlap:
                        current_chunk = [overlap_text, para]
                        current_size = len(overlap_text) + para_size
                    else:
                        current_chunk = [para]
                        current_size = para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _chunk_by_size(self, text: str) -> List[str]:
        """크기 기반 청킹"""
        chunks = []
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_config.target_size:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """문장 분리"""
        parts = self._sentence_endings.split(text)
        sentences = []
        current = ""
        
        for part in parts:
            if part is None:
                continue
            part = part.strip()
            if not part:
                continue
            
            if part in ['.', '!', '?', '。', '！', '？']:
                current += part
                if current.strip():
                    sentences.append(current.strip())
                current = ""
            else:
                current += part + " "
        
        if current.strip():
            sentences.append(current.strip())
        
        return sentences

    # =========================================================================
    # BM25 Index Management
    # =========================================================================
    
    def build_bm25_index(
        self,
        collection_id: str,
        chunks: List[ProcessedChunk]
    ) -> None:
        """
        BM25 인덱스 구축.
        
        Args:
            collection_id: 컬렉션 ID
            chunks: 청크 리스트
        """
        try:
            from rank_bm25 import BM25Okapi
            
            corpus = [chunk.tokens for chunk in chunks]
            texts = [chunk.text for chunk in chunks]
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            
            bm25 = BM25Okapi(corpus)
            
            self._bm25_indices[collection_id] = {
                "bm25": bm25,
                "corpus": corpus,
                "texts": texts,
                "chunk_ids": chunk_ids,
                "updated_at": datetime.utcnow()
            }
            
            logger.info(
                f"Built BM25 index for {collection_id}: {len(chunks)} chunks"
            )
            
        except ImportError:
            logger.warning("rank_bm25 not installed. Install with: pip install rank-bm25")
    
    def update_bm25_index(
        self,
        collection_id: str,
        new_chunks: List[ProcessedChunk]
    ) -> None:
        """
        BM25 인덱스 업데이트 (증분).
        
        Args:
            collection_id: 컬렉션 ID
            new_chunks: 새 청크 리스트
        """
        if collection_id not in self._bm25_indices:
            self.build_bm25_index(collection_id, new_chunks)
            return
        
        try:
            from rank_bm25 import BM25Okapi
            
            index_data = self._bm25_indices[collection_id]
            
            # 기존 데이터에 추가
            for chunk in new_chunks:
                index_data["corpus"].append(chunk.tokens)
                index_data["texts"].append(chunk.text)
                index_data["chunk_ids"].append(chunk.chunk_id)
            
            # BM25 재구축
            index_data["bm25"] = BM25Okapi(index_data["corpus"])
            index_data["updated_at"] = datetime.utcnow()
            
            logger.info(
                f"Updated BM25 index for {collection_id}: "
                f"+{len(new_chunks)} chunks, total={len(index_data['corpus'])}"
            )
            
        except ImportError:
            pass
    
    def search_bm25(
        self,
        collection_id: str,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[str, str, float]]:
        """
        BM25 키워드 검색.
        
        Args:
            collection_id: 컬렉션 ID
            query: 검색 쿼리
            top_k: 반환할 결과 수
            
        Returns:
            [(chunk_id, text, score), ...]
        """
        if collection_id not in self._bm25_indices:
            logger.warning(f"BM25 index not found for {collection_id}")
            return []
        
        index_data = self._bm25_indices[collection_id]
        bm25 = index_data["bm25"]
        
        # 쿼리 토큰화
        query_tokens, _ = self.tokenize(query, extract_nouns=True)
        
        if not query_tokens:
            query_tokens = query.lower().split()
        
        # BM25 스코어 계산
        scores = bm25.get_scores(query_tokens)
        
        # 상위 결과 추출
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in indexed_scores[:top_k]:
            if score > 0:
                results.append((
                    index_data["chunk_ids"][idx],
                    index_data["texts"][idx],
                    float(score)
                ))
        
        return results
    
    # =========================================================================
    # Hybrid Search
    # =========================================================================
    
    async def hybrid_search(
        self,
        collection_id: str,
        query: str,
        vector_results: List[Tuple[str, str, float]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 (Vector + BM25).
        
        Args:
            collection_id: 컬렉션 ID
            query: 검색 쿼리
            vector_results: 벡터 검색 결과 [(chunk_id, text, score), ...]
            top_k: 반환할 결과 수
            
        Returns:
            통합 검색 결과
        """
        config = self.search_config
        
        # BM25 검색
        bm25_results = self.search_bm25(collection_id, query, top_k * 2)
        
        # RRF (Reciprocal Rank Fusion)
        rrf_scores: Dict[str, Dict] = {}
        k = config.rrf_k
        
        # 벡터 검색 결과 스코어링
        for rank, (chunk_id, text, score) in enumerate(vector_results):
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"text": text, "score": 0, "sources": []}
            rrf_scores[chunk_id]["score"] += config.vector_weight / (k + rank + 1)
            rrf_scores[chunk_id]["sources"].append("vector")
        
        # BM25 결과 스코어링
        for rank, (chunk_id, text, score) in enumerate(bm25_results):
            if chunk_id not in rrf_scores:
                rrf_scores[chunk_id] = {"text": text, "score": 0, "sources": []}
            rrf_scores[chunk_id]["score"] += config.bm25_weight / (k + rank + 1)
            rrf_scores[chunk_id]["sources"].append("bm25")
        
        # 정렬 및 결과 생성
        sorted_results = sorted(
            rrf_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        
        results = []
        for chunk_id, data in sorted_results[:top_k]:
            results.append({
                "chunk_id": chunk_id,
                "text": data["text"],
                "score": data["score"],
                "sources": list(set(data["sources"])),
                "is_hybrid": len(set(data["sources"])) > 1
            })
        
        logger.info(
            f"Hybrid search: vector={len(vector_results)}, "
            f"bm25={len(bm25_results)}, merged={len(results)}"
        )
        
        return results
    
    # =========================================================================
    # Query Processing
    # =========================================================================
    
    def preprocess_query(self, query: str) -> str:
        """
        검색 쿼리 전처리.
        
        Args:
            query: 원본 쿼리
            
        Returns:
            전처리된 쿼리
        """
        # 기본 전처리
        query = self.preprocess_text(query)
        
        # 유니코드 정규화
        import unicodedata
        query = unicodedata.normalize('NFC', query)
        
        return query.strip()
    
    def expand_query(self, query: str) -> List[str]:
        """
        쿼리 확장 (동의어, 관련어).
        
        Args:
            query: 원본 쿼리
            
        Returns:
            확장된 쿼리 리스트
        """
        expanded = [query]
        language = self.detect_language(query)
        
        if language in [Language.KOREAN, Language.MIXED]:
            expanded.extend(self._expand_korean_query(query))
        
        if language in [Language.ENGLISH, Language.MIXED]:
            expanded.extend(self._expand_english_query(query))
        
        # 명사 추출 버전 추가
        tokens, _ = self.tokenize(query, extract_nouns=True)
        if tokens:
            expanded.append(' '.join(tokens))
        
        return list(set(expanded))
    
    def _expand_korean_query(self, query: str) -> List[str]:
        """한글 쿼리 확장"""
        expanded = []
        
        # 동의어 매핑
        synonyms = {
            "방법": ["방식", "절차", "과정", "how to"],
            "문제": ["이슈", "오류", "에러", "issue", "error"],
            "사용": ["이용", "활용", "적용", "use"],
            "설정": ["설치", "구성", "세팅", "config", "setup"],
            "확인": ["검토", "점검", "체크", "check"],
            "생성": ["만들기", "작성", "create"],
            "삭제": ["제거", "지우기", "delete", "remove"],
            "수정": ["변경", "편집", "update", "edit"],
            "검색": ["찾기", "조회", "search", "find"],
            "저장": ["보관", "기록", "save"],
        }
        
        tokens, _ = self.tokenize(query, extract_nouns=True)
        
        for token in tokens:
            if token in synonyms:
                for synonym in synonyms[token]:
                    expanded.append(query.replace(token, synonym))
        
        return expanded
    
    def _expand_english_query(self, query: str) -> List[str]:
        """영어 쿼리 확장"""
        expanded = []
        
        # 동의어 매핑
        synonyms = {
            "create": ["make", "generate", "build"],
            "delete": ["remove", "erase", "drop"],
            "update": ["modify", "change", "edit"],
            "search": ["find", "query", "lookup"],
            "error": ["issue", "problem", "bug"],
            "config": ["configuration", "settings", "setup"],
        }
        
        query_lower = query.lower()
        
        for word, syns in synonyms.items():
            if word in query_lower:
                for syn in syns:
                    expanded.append(query_lower.replace(word, syn))
        
        return expanded
    
    # =========================================================================
    # Keyword Extraction
    # =========================================================================
    
    def extract_keywords(
        self,
        text: str,
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        키워드 추출.
        
        Args:
            text: 입력 텍스트
            top_k: 추출할 키워드 수
            
        Returns:
            [(keyword, score), ...]
        """
        tokens, language = self.tokenize(text, extract_nouns=True)
        
        # 빈도 계산
        from collections import Counter
        freq = Counter(tokens)
        
        # 스코어 계산 (빈도 * 길이 가중치)
        scored = []
        for token, count in freq.items():
            score = count * (1 + len(token) * 0.1)
            scored.append((token, score))
        
        # 정렬
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:top_k]


# =========================================================================
# Factory Functions
# =========================================================================

_processor_instance: Optional[KnowledgebaseKoreanProcessor] = None


def get_knowledgebase_korean_processor(
    chunk_config: Optional[ChunkConfig] = None,
    search_config: Optional[SearchConfig] = None,
    use_morpheme_analysis: bool = True
) -> KnowledgebaseKoreanProcessor:
    """
    싱글톤 프로세서 인스턴스 반환.
    
    Args:
        chunk_config: 청킹 설정
        search_config: 검색 설정
        use_morpheme_analysis: 형태소 분석 사용 여부
        
    Returns:
        KnowledgebaseKoreanProcessor 인스턴스
    """
    global _processor_instance
    
    if _processor_instance is None:
        _processor_instance = KnowledgebaseKoreanProcessor(
            chunk_config=chunk_config,
            search_config=search_config,
            use_morpheme_analysis=use_morpheme_analysis
        )
    
    return _processor_instance
