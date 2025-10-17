"""
Multi-Language Complexity Analyzer

Extends complexity analysis to support multiple languages beyond English and Korean.

Supported Languages:
- English (en)
- Korean (ko)
- Japanese (ja)
- Chinese (zh)
- Spanish (es)
- German (de)
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported languages"""

    ENGLISH = "en"
    KOREAN = "ko"
    JAPANESE = "ja"
    CHINESE = "zh"
    SPANISH = "es"
    GERMAN = "de"
    AUTO = "auto"


@dataclass
class LanguageFeatures:
    """Language-specific features detected in query"""

    language: Language
    confidence: float
    word_count: int
    char_count: int
    sentence_count: int

    # Language-specific features
    particles: List[str] = None  # Japanese, Korean
    honorifics: List[str] = None  # Japanese, Korean
    compound_words: List[str] = None  # German
    verb_conjugations: int = 0  # Spanish
    characters: List[str] = None  # Chinese, Japanese


class MultiLanguageAnalyzer:
    """
    Multi-language complexity analyzer

    Provides language-specific complexity analysis for:
    - English: Standard analysis
    - Korean: Particle and honorific analysis
    - Japanese: Particle, honorific, and kanji analysis
    - Chinese: Character-based analysis
    - Spanish: Verb conjugation complexity
    - German: Compound word analysis
    """

    def __init__(self):
        self._init_language_patterns()

    def _init_language_patterns(self):
        """Initialize language detection patterns"""
        # Korean patterns
        self.korean_pattern = re.compile(r"[가-힣]+")
        self.korean_particles = [
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "에",
            "에서",
            "로",
            "으로",
            "와",
            "과",
        ]
        self.korean_honorifics = ["님", "씨", "요", "습니다", "십니다"]

        # Japanese patterns
        self.japanese_pattern = re.compile(
            r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+"
        )
        self.hiragana_pattern = re.compile(r"[\u3040-\u309F]+")
        self.katakana_pattern = re.compile(r"[\u30A0-\u30FF]+")
        self.kanji_pattern = re.compile(r"[\u4E00-\u9FFF]+")
        self.japanese_particles = [
            "は",
            "が",
            "を",
            "に",
            "で",
            "と",
            "から",
            "まで",
            "の",
            "へ",
        ]
        self.japanese_honorifics = ["さん", "さま", "ます", "です", "ございます"]

        # Chinese patterns
        self.chinese_pattern = re.compile(r"[\u4E00-\u9FFF]+")

        # Spanish patterns
        self.spanish_verbs = ["ar", "er", "ir", "ado", "ido", "ando", "iendo"]

        # German patterns
        self.german_compounds = re.compile(r"[A-ZÄÖÜ][a-zäöüß]+[A-ZÄÖÜ][a-zäöüß]+")

    def detect_language(self, text: str) -> Tuple[Language, float]:
        """
        Detect language of text

        Returns:
            (language, confidence)
        """
        if not text:
            return Language.ENGLISH, 0.5

        # Count character types
        korean_chars = len(self.korean_pattern.findall(text))
        japanese_chars = len(self.japanese_pattern.findall(text))
        chinese_chars = len(self.chinese_pattern.findall(text))

        total_chars = len(text)

        # Korean detection
        if korean_chars > 0:
            confidence = korean_chars / total_chars
            if confidence > 0.3:
                return Language.KOREAN, confidence

        # Japanese detection
        if japanese_chars > 0:
            confidence = japanese_chars / total_chars
            if confidence > 0.3:
                return Language.JAPANESE, confidence

        # Chinese detection (excluding Japanese kanji)
        if chinese_chars > 0 and japanese_chars == 0:
            confidence = chinese_chars / total_chars
            if confidence > 0.3:
                return Language.CHINESE, confidence

        # Spanish detection (simple heuristic)
        spanish_indicators = ["¿", "¡", "ñ", "á", "é", "í", "ó", "ú"]
        spanish_count = sum(1 for char in text if char in spanish_indicators)
        if spanish_count > 0:
            confidence = min(0.8, spanish_count / 10)
            return Language.SPANISH, confidence

        # German detection (simple heuristic)
        german_indicators = ["ä", "ö", "ü", "ß"]
        german_count = sum(1 for char in text if char in german_indicators)
        if german_count > 0:
            confidence = min(0.8, german_count / 10)
            return Language.GERMAN, confidence

        # Default to English
        return Language.ENGLISH, 0.7

    def extract_features(self, text: str, language: Language) -> LanguageFeatures:
        """Extract language-specific features"""
        # Basic features
        words = text.split()
        word_count = len(words)
        char_count = len(text)
        sentence_count = len(re.split(r"[.!?。！？]", text))

        features = LanguageFeatures(
            language=language,
            confidence=1.0,
            word_count=word_count,
            char_count=char_count,
            sentence_count=sentence_count,
        )

        # Language-specific features
        if language == Language.KOREAN:
            features.particles = self._extract_korean_particles(text)
            features.honorifics = self._extract_korean_honorifics(text)

        elif language == Language.JAPANESE:
            features.particles = self._extract_japanese_particles(text)
            features.honorifics = self._extract_japanese_honorifics(text)
            features.characters = self._analyze_japanese_characters(text)

        elif language == Language.CHINESE:
            features.characters = self._analyze_chinese_characters(text)

        elif language == Language.SPANISH:
            features.verb_conjugations = self._count_spanish_verbs(text)

        elif language == Language.GERMAN:
            features.compound_words = self._extract_german_compounds(text)

        return features

    def calculate_complexity_score(
        self, text: str, language: Optional[Language] = None
    ) -> Tuple[float, Dict[str, any]]:
        """
        Calculate complexity score with language-specific analysis

        Returns:
            (score, factors)
        """
        # Detect language if not provided
        if not language or language == Language.AUTO:
            language, lang_confidence = self.detect_language(text)
        else:
            lang_confidence = 1.0

        # Extract features
        features = self.extract_features(text, language)

        # Base complexity factors
        factors = {
            "language": language.value,
            "language_confidence": lang_confidence,
            "word_count": features.word_count,
            "char_count": features.char_count,
            "sentence_count": features.sentence_count,
        }

        # Calculate base score
        score = 0.0

        # Factor 1: Length (20%)
        if language in [Language.CHINESE, Language.JAPANESE]:
            # Character-based languages
            if features.char_count > 50:
                score += 0.20
            elif features.char_count > 25:
                score += 0.10
            else:
                score += 0.05
        else:
            # Word-based languages
            if features.word_count > 30:
                score += 0.20
            elif features.word_count > 15:
                score += 0.10
            else:
                score += 0.05

        # Factor 2: Question type (25%)
        question_score = self._analyze_question_type(text, language)
        score += question_score * 0.25
        factors["question_type_score"] = question_score

        # Factor 3: Multiple questions (15%)
        question_marks = text.count("?") + text.count("？")
        if question_marks > 2:
            score += 0.15
        elif question_marks > 1:
            score += 0.10
        factors["question_count"] = question_marks

        # Factor 4: Comparison/analysis keywords (20%)
        comparison_score = self._analyze_comparison_keywords(text, language)
        score += comparison_score * 0.20
        factors["comparison_score"] = comparison_score

        # Factor 5: Language-specific complexity (10%)
        lang_score = self._calculate_language_specific_score(features, language)
        score += lang_score * 0.10
        factors["language_specific_score"] = lang_score

        # Factor 6: Sentence structure (10%)
        structure_score = self._analyze_sentence_structure(features)
        score += structure_score * 0.10
        factors["structure_score"] = structure_score

        return min(1.0, score), factors

    def _extract_korean_particles(self, text: str) -> List[str]:
        """Extract Korean particles"""
        found = []
        for particle in self.korean_particles:
            if particle in text:
                found.append(particle)
        return found

    def _extract_korean_honorifics(self, text: str) -> List[str]:
        """Extract Korean honorifics"""
        found = []
        for honorific in self.korean_honorifics:
            if honorific in text:
                found.append(honorific)
        return found

    def _extract_japanese_particles(self, text: str) -> List[str]:
        """Extract Japanese particles"""
        found = []
        for particle in self.japanese_particles:
            if particle in text:
                found.append(particle)
        return found

    def _extract_japanese_honorifics(self, text: str) -> List[str]:
        """Extract Japanese honorifics"""
        found = []
        for honorific in self.japanese_honorifics:
            if honorific in text:
                found.append(honorific)
        return found

    def _analyze_japanese_characters(self, text: str) -> List[str]:
        """Analyze Japanese character types"""
        return [
            f"hiragana:{len(self.hiragana_pattern.findall(text))}",
            f"katakana:{len(self.katakana_pattern.findall(text))}",
            f"kanji:{len(self.kanji_pattern.findall(text))}",
        ]

    def _analyze_chinese_characters(self, text: str) -> List[str]:
        """Analyze Chinese characters"""
        chars = self.chinese_pattern.findall(text)
        return [f"characters:{len(''.join(chars))}"]

    def _count_spanish_verbs(self, text: str) -> int:
        """Count Spanish verb forms"""
        count = 0
        text_lower = text.lower()
        for verb_ending in self.spanish_verbs:
            count += text_lower.count(verb_ending)
        return count

    def _extract_german_compounds(self, text: str) -> List[str]:
        """Extract German compound words"""
        return self.german_compounds.findall(text)

    def _analyze_question_type(self, text: str, language: Language) -> float:
        """Analyze question type complexity"""
        text_lower = text.lower()

        # Analytical questions (high complexity)
        analytical_keywords = {
            Language.ENGLISH: ["why", "how", "explain", "analyze", "evaluate"],
            Language.KOREAN: ["왜", "어떻게", "설명", "분석", "평가"],
            Language.JAPANESE: ["なぜ", "どのように", "説明", "分析", "評価"],
            Language.CHINESE: ["为什么", "怎么", "解释", "分析", "评估"],
            Language.SPANISH: ["por qué", "cómo", "explicar", "analizar", "evaluar"],
            Language.GERMAN: ["warum", "wie", "erklären", "analysieren", "bewerten"],
        }

        # Comparative questions (medium-high complexity)
        comparative_keywords = {
            Language.ENGLISH: ["compare", "contrast", "difference", "versus"],
            Language.KOREAN: ["비교", "대조", "차이", "대"],
            Language.JAPANESE: ["比較", "対照", "違い", "対"],
            Language.CHINESE: ["比较", "对比", "差异", "对"],
            Language.SPANISH: ["comparar", "contrastar", "diferencia", "versus"],
            Language.GERMAN: [
                "vergleichen",
                "gegenüberstellen",
                "unterschied",
                "versus",
            ],
        }

        # Factual questions (low complexity)
        factual_keywords = {
            Language.ENGLISH: ["what", "who", "when", "where"],
            Language.KOREAN: ["무엇", "누구", "언제", "어디"],
            Language.JAPANESE: ["何", "誰", "いつ", "どこ"],
            Language.CHINESE: ["什么", "谁", "什么时候", "哪里"],
            Language.SPANISH: ["qué", "quién", "cuándo", "dónde"],
            Language.GERMAN: ["was", "wer", "wann", "wo"],
        }

        # Check analytical
        if any(kw in text_lower for kw in analytical_keywords.get(language, [])):
            return 1.0

        # Check comparative
        if any(kw in text_lower for kw in comparative_keywords.get(language, [])):
            return 0.8

        # Check factual
        if any(kw in text_lower for kw in factual_keywords.get(language, [])):
            return 0.4

        return 0.5

    def _analyze_comparison_keywords(self, text: str, language: Language) -> float:
        """Analyze comparison and analysis keywords"""
        text_lower = text.lower()

        keywords = {
            Language.ENGLISH: [
                "compare",
                "contrast",
                "analyze",
                "evaluate",
                "assess",
                "versus",
            ],
            Language.KOREAN: ["비교", "대조", "분석", "평가", "검토", "대"],
            Language.JAPANESE: ["比較", "対照", "分析", "評価", "検討", "対"],
            Language.CHINESE: ["比较", "对比", "分析", "评估", "审查", "对"],
            Language.SPANISH: [
                "comparar",
                "contrastar",
                "analizar",
                "evaluar",
                "valorar",
                "versus",
            ],
            Language.GERMAN: [
                "vergleichen",
                "gegenüberstellen",
                "analysieren",
                "bewerten",
                "beurteilen",
                "versus",
            ],
        }

        count = sum(1 for kw in keywords.get(language, []) if kw in text_lower)

        if count >= 2:
            return 1.0
        elif count == 1:
            return 0.6
        else:
            return 0.0

    def _calculate_language_specific_score(
        self, features: LanguageFeatures, language: Language
    ) -> float:
        """Calculate language-specific complexity score"""
        if language == Language.KOREAN:
            # More particles and honorifics = more complex
            particle_count = len(features.particles) if features.particles else 0
            honorific_count = len(features.honorifics) if features.honorifics else 0
            return min(1.0, (particle_count + honorific_count) / 10)

        elif language == Language.JAPANESE:
            # More kanji and honorifics = more complex
            kanji_info = next(
                (c for c in features.characters if c.startswith("kanji:")), "kanji:0"
            )
            kanji_count = int(kanji_info.split(":")[1])
            honorific_count = len(features.honorifics) if features.honorifics else 0
            return min(1.0, (kanji_count + honorific_count * 2) / 20)

        elif language == Language.CHINESE:
            # More characters = more complex
            char_info = (
                features.characters[0] if features.characters else "characters:0"
            )
            char_count = int(char_info.split(":")[1])
            return min(1.0, char_count / 50)

        elif language == Language.SPANISH:
            # More verb conjugations = more complex
            return min(1.0, features.verb_conjugations / 10)

        elif language == Language.GERMAN:
            # More compound words = more complex
            compound_count = (
                len(features.compound_words) if features.compound_words else 0
            )
            return min(1.0, compound_count / 5)

        return 0.5

    def _analyze_sentence_structure(self, features: LanguageFeatures) -> float:
        """Analyze sentence structure complexity"""
        if features.sentence_count == 0:
            return 0.5

        # Average words per sentence
        avg_words = features.word_count / features.sentence_count

        if avg_words > 20:
            return 1.0
        elif avg_words > 10:
            return 0.6
        else:
            return 0.3
