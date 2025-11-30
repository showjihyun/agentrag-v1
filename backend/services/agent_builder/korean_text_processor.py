"""
Korean & English Bilingual Text Processor for Knowledgebase.

Optimized for:
- Korean morphological analysis (형태소 분석)
- Korean-English mixed text handling
- Proper tokenization for both languages
- Korean-optimized BM25 search
"""

import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Detected language."""
    KOREAN = "ko"
    ENGLISH = "en"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class TokenizedText:
    """Tokenized text result."""
    original: str
    tokens: List[str]
    language: Language
    morphemes: Optional[List[Dict[str, str]]] = None


class KoreanTextProcessor:
    """
    Bilingual text processor optimized for Korean and English.
    
    Features:
    - Korean morphological analysis using KoNLPy
    - Proper handling of Korean-English mixed text
    - Stopword removal for both languages
    - Noun extraction for better search
    """
    
    # Korean stopwords (조사, 어미, 접속사 등)
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
    
    # English stopwords
    ENGLISH_STOPWORDS = {
        "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "as", "into", "through", "during", "before", "after",
        "above", "below", "between", "under", "again", "further", "then",
        "once", "here", "there", "when", "where", "why", "how", "all",
        "each", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "and", "but", "if", "or", "because", "until", "while", "this",
        "that", "these", "those", "what", "which", "who", "whom",
    }
    
    def __init__(self, use_konlpy: bool = True):
        """
        Initialize Korean text processor.
        
        Args:
            use_konlpy: Whether to use KoNLPy for morphological analysis
        """
        self.use_konlpy = use_konlpy
        self._tagger = None
        self._mecab = None
        self._okt = None
    
    @property
    def tagger(self):
        """Lazy load Korean morphological analyzer."""
        if self._tagger is None and self.use_konlpy:
            try:
                # Try MeCab first (fastest)
                from konlpy.tag import Mecab
                self._tagger = Mecab()
                self._mecab = self._tagger
                logger.info("Using MeCab for Korean morphological analysis")
            except Exception:
                try:
                    # Fallback to Okt (Open Korean Text)
                    from konlpy.tag import Okt
                    self._tagger = Okt()
                    self._okt = self._tagger
                    logger.info("Using Okt for Korean morphological analysis")
                except Exception as e:
                    logger.warning(f"KoNLPy not available: {e}")
                    self.use_konlpy = False
        return self._tagger
    
    def detect_language(self, text: str) -> Language:
        """
        Detect primary language of text.
        
        Args:
            text: Input text
            
        Returns:
            Detected language
        """
        if not text:
            return Language.UNKNOWN
        
        # Count Korean and English characters
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
    
    def tokenize(self, text: str, extract_nouns: bool = False) -> TokenizedText:
        """
        Tokenize text with language-aware processing.
        
        Args:
            text: Input text
            extract_nouns: Whether to extract only nouns (better for search)
            
        Returns:
            TokenizedText with tokens and metadata
        """
        language = self.detect_language(text)
        
        if language == Language.KOREAN:
            return self._tokenize_korean(text, extract_nouns)
        elif language == Language.ENGLISH:
            return self._tokenize_english(text)
        elif language == Language.MIXED:
            return self._tokenize_mixed(text, extract_nouns)
        else:
            return TokenizedText(
                original=text,
                tokens=text.lower().split(),
                language=language
            )
    
    def _tokenize_korean(self, text: str, extract_nouns: bool) -> TokenizedText:
        """Tokenize Korean text using morphological analysis."""
        morphemes = None
        
        if self.tagger and self.use_konlpy:
            try:
                if extract_nouns:
                    # Extract nouns only (better for search)
                    tokens = self.tagger.nouns(text)
                else:
                    # Full morphological analysis
                    pos_tags = self.tagger.pos(text)
                    morphemes = [{"word": word, "pos": pos} for word, pos in pos_tags]
                    
                    # Filter to meaningful parts of speech
                    # N: Noun, V: Verb, A: Adjective
                    meaningful_pos = {'NNG', 'NNP', 'NNB', 'NR', 'NP',  # Nouns
                                     'VV', 'VA', 'VX',  # Verbs, Adjectives
                                     'MAG', 'MAJ',  # Adverbs
                                     'SL', 'SH', 'SN'}  # Foreign, Chinese, Numbers
                    
                    tokens = [
                        word for word, pos in pos_tags
                        if pos in meaningful_pos or pos.startswith('N') or pos.startswith('V')
                    ]
                
                # Remove stopwords
                tokens = [t for t in tokens if t not in self.KOREAN_STOPWORDS and len(t) > 1]
                
                return TokenizedText(
                    original=text,
                    tokens=tokens,
                    language=Language.KOREAN,
                    morphemes=morphemes
                )
                
            except Exception as e:
                logger.warning(f"Korean tokenization failed: {e}")
        
        # Fallback: simple character-based tokenization
        tokens = self._simple_korean_tokenize(text)
        return TokenizedText(
            original=text,
            tokens=tokens,
            language=Language.KOREAN
        )
    
    def _simple_korean_tokenize(self, text: str) -> List[str]:
        """Simple Korean tokenization without KoNLPy."""
        # Split by whitespace and punctuation
        tokens = re.findall(r'[가-힣]+|[a-zA-Z]+|\d+', text)
        # Remove stopwords and short tokens
        tokens = [t for t in tokens if t not in self.KOREAN_STOPWORDS and len(t) > 1]
        return tokens
    
    def _tokenize_english(self, text: str) -> TokenizedText:
        """Tokenize English text."""
        # Lowercase and split
        text_lower = text.lower()
        tokens = re.findall(r'\b[a-z]+\b', text_lower)
        
        # Remove stopwords
        tokens = [t for t in tokens if t not in self.ENGLISH_STOPWORDS and len(t) > 2]
        
        return TokenizedText(
            original=text,
            tokens=tokens,
            language=Language.ENGLISH
        )
    
    def _tokenize_mixed(self, text: str, extract_nouns: bool) -> TokenizedText:
        """Tokenize mixed Korean-English text."""
        # Separate Korean and English parts
        korean_parts = re.findall(r'[가-힣]+', text)
        english_parts = re.findall(r'[a-zA-Z]+', text)
        
        all_tokens = []
        
        # Process Korean parts
        if korean_parts:
            korean_text = ' '.join(korean_parts)
            korean_result = self._tokenize_korean(korean_text, extract_nouns)
            all_tokens.extend(korean_result.tokens)
        
        # Process English parts
        if english_parts:
            english_text = ' '.join(english_parts)
            english_result = self._tokenize_english(english_text)
            all_tokens.extend(english_result.tokens)
        
        return TokenizedText(
            original=text,
            tokens=all_tokens,
            language=Language.MIXED
        )
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Extract keywords from text using TF-IDF-like scoring.
        
        Args:
            text: Input text
            top_k: Number of keywords to extract
            
        Returns:
            List of (keyword, score) tuples
        """
        tokenized = self.tokenize(text, extract_nouns=True)
        
        # Count token frequencies
        freq = {}
        for token in tokenized.tokens:
            freq[token] = freq.get(token, 0) + 1
        
        # Score by frequency and length
        scored = []
        for token, count in freq.items():
            # Longer tokens and higher frequency = higher score
            score = count * (1 + len(token) * 0.1)
            scored.append((token, score))
        
        # Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:top_k]
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize search query for better matching.
        
        Args:
            query: Search query
            
        Returns:
            Normalized query
        """
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Normalize Korean characters (compatibility jamo to standard)
        try:
            import unicodedata
            query = unicodedata.normalize('NFC', query)
        except Exception:
            pass
        
        return query
    
    def expand_query_korean(self, query: str) -> List[str]:
        """
        Expand Korean query with related terms.
        
        Args:
            query: Original query
            
        Returns:
            List of expanded query terms
        """
        expanded = [query]
        
        # Add noun forms
        tokenized = self.tokenize(query, extract_nouns=True)
        if tokenized.tokens:
            expanded.append(' '.join(tokenized.tokens))
        
        # Common Korean query expansions
        expansions = {
            "방법": ["방식", "절차", "과정"],
            "문제": ["이슈", "오류", "에러"],
            "사용": ["이용", "활용", "적용"],
            "설정": ["설치", "구성", "세팅"],
            "확인": ["검토", "점검", "체크"],
        }
        
        for token in tokenized.tokens:
            if token in expansions:
                for synonym in expansions[token]:
                    expanded.append(query.replace(token, synonym))
        
        return list(set(expanded))


class BilingualBM25:
    """
    BM25 implementation optimized for Korean-English bilingual search.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25.
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.processor = KoreanTextProcessor()
        
        self.corpus = []
        self.doc_lengths = []
        self.avg_doc_length = 0
        self.doc_freqs = {}
        self.idf = {}
        self.doc_count = 0
    
    def fit(self, documents: List[str]):
        """
        Fit BM25 on document corpus.
        
        Args:
            documents: List of document texts
        """
        self.corpus = []
        self.doc_lengths = []
        self.doc_freqs = {}
        
        for doc in documents:
            tokenized = self.processor.tokenize(doc, extract_nouns=True)
            tokens = tokenized.tokens
            
            self.corpus.append(tokens)
            self.doc_lengths.append(len(tokens))
            
            # Count document frequencies
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
        
        self.doc_count = len(documents)
        self.avg_doc_length = sum(self.doc_lengths) / max(self.doc_count, 1)
        
        # Calculate IDF
        import math
        for token, df in self.doc_freqs.items():
            self.idf[token] = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
    
    def get_scores(self, query: str) -> List[float]:
        """
        Get BM25 scores for query against all documents.
        
        Args:
            query: Search query
            
        Returns:
            List of scores for each document
        """
        tokenized = self.processor.tokenize(query, extract_nouns=True)
        query_tokens = tokenized.tokens
        
        scores = []
        
        for i, doc_tokens in enumerate(self.corpus):
            score = 0
            doc_length = self.doc_lengths[i]
            
            # Count term frequencies in document
            tf = {}
            for token in doc_tokens:
                tf[token] = tf.get(token, 0) + 1
            
            for token in query_tokens:
                if token not in tf:
                    continue
                
                idf = self.idf.get(token, 0)
                term_freq = tf[token]
                
                # BM25 formula
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * doc_length / self.avg_doc_length
                )
                
                score += idf * (numerator / denominator)
            
            scores.append(score)
        
        return scores
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search and return top-k results.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of (doc_index, score) tuples
        """
        scores = self.get_scores(query)
        
        # Get top-k indices
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        
        return indexed_scores[:top_k]


# Singleton instance
_processor: Optional[KoreanTextProcessor] = None


def get_korean_processor() -> KoreanTextProcessor:
    """Get singleton Korean text processor."""
    global _processor
    if _processor is None:
        _processor = KoreanTextProcessor()
    return _processor
