"""
Unit tests for enhanced AdaptiveRAGService complexity analysis.

Tests:
- Weighted factor analysis
- Confidence scoring
- Korean language support
- ComplexityAnalysis object structure
- Edge cases
"""

import pytest
from backend.services.adaptive_rag_service import (
    AdaptiveRAGService,
    QueryComplexity,
    ComplexityAnalysis,
)


@pytest.fixture
def service():
    """Create AdaptiveRAGService instance."""
    return AdaptiveRAGService()


class TestEnhancedComplexityAnalysis:
    """Test enhanced complexity analysis features."""

    def test_simple_query_english(self, service):
        """Test simple English query classification."""
        query = "What is RAG?"
        analysis = service.analyze_query_complexity(query)

        assert isinstance(analysis, ComplexityAnalysis)
        assert analysis.complexity == QueryComplexity.SIMPLE
        assert 0.0 <= analysis.score <= 1.0
        assert 0.0 <= analysis.confidence <= 1.0
        assert analysis.language in ["en", "mixed"]
        assert analysis.word_count == 3
        assert analysis.question_type == "factual"
        assert "SIMPLE" in analysis.reasoning

    def test_medium_query_english(self, service):
        """Test medium complexity English query."""
        query = "Compare RAG and fine-tuning approaches for LLMs"
        analysis = service.analyze_query_complexity(query)

        assert analysis.complexity == QueryComplexity.MEDIUM
        assert 0.35 <= analysis.score <= 0.70
        assert analysis.confidence > 0.6
        assert analysis.question_type == "comparative"
        assert (
            "comparison" in analysis.reasoning.lower()
            or "comparative" in analysis.reasoning.lower()
        )

    def test_complex_query_english(self, service):
        """Test complex English query classification."""
        query = (
            "Analyze the evolution of RAG systems from 2020 to 2024 and "
            "explain why certain approaches became dominant while comparing "
            "their performance characteristics and cost implications"
        )
        analysis = service.analyze_query_complexity(query)

        assert analysis.complexity == QueryComplexity.COMPLEX
        assert analysis.score > 0.70
        assert analysis.confidence > 0.6
        assert analysis.word_count > 30
        assert analysis.question_type == "analytical"

    def test_simple_query_korean(self, service):
        """Test simple Korean query classification."""
        query = "RAG가 무엇인가요?"
        analysis = service.analyze_query_complexity(query, language="ko")

        assert isinstance(analysis, ComplexityAnalysis)
        assert analysis.complexity == QueryComplexity.SIMPLE
        assert analysis.language == "ko"
        assert analysis.question_type == "factual"

    def test_medium_query_korean(self, service):
        """Test medium complexity Korean query."""
        query = "RAG와 파인튜닝의 차이점을 비교해주세요"
        analysis = service.analyze_query_complexity(query, language="ko")

        assert analysis.complexity in [QueryComplexity.MEDIUM, QueryComplexity.COMPLEX]
        assert analysis.language == "ko"
        assert analysis.factors["comparison"]["score"] > 0

    def test_complex_query_korean(self, service):
        """Test complex Korean query classification."""
        query = (
            "2020년부터 2024년까지 RAG 시스템의 발전 과정을 분석하고 "
            "특정 접근 방식이 왜 지배적이 되었는지 설명하면서 "
            "성능 특성과 비용 영향을 비교해주세요"
        )
        analysis = service.analyze_query_complexity(query, language="ko")

        assert analysis.complexity == QueryComplexity.COMPLEX
        assert analysis.score > 0.70
        assert analysis.language == "ko"

    def test_mixed_language_query(self, service):
        """Test mixed language query."""
        query = "RAG와 fine-tuning을 compare해주세요"
        analysis = service.analyze_query_complexity(query)

        assert analysis.language == "mixed"
        assert isinstance(analysis.complexity, QueryComplexity)

    def test_weighted_factors(self, service):
        """Test that all weighted factors are present."""
        query = "Compare and analyze the evolution of RAG systems"
        analysis = service.analyze_query_complexity(query)

        # Check all factors are present
        assert "word_count" in analysis.factors
        assert "question_type" in analysis.factors
        assert "multiple_questions" in analysis.factors
        assert "comparison" in analysis.factors
        assert "temporal" in analysis.factors
        assert "entity" in analysis.factors

        # Check each factor has required fields
        for factor_name, factor_data in analysis.factors.items():
            assert "score" in factor_data
            assert "weight" in factor_data

    def test_confidence_scoring(self, service):
        """Test confidence scoring for different scenarios."""
        # Clear SIMPLE case (far from threshold)
        simple_query = "What is AI?"
        simple_analysis = service.analyze_query_complexity(simple_query)

        # Boundary case (near threshold)
        boundary_query = "What is AI and how does it work?"
        boundary_analysis = service.analyze_query_complexity(boundary_query)

        # Clear COMPLEX case (far from threshold)
        complex_query = (
            "Analyze and compare the historical evolution of artificial intelligence "
            "from 1950 to 2024, explaining why certain paradigms became dominant "
            "and evaluating their impact on modern machine learning systems"
        )
        complex_analysis = service.analyze_query_complexity(complex_query)

        # Confidence should be higher for clear cases
        assert simple_analysis.confidence > 0.7
        assert complex_analysis.confidence > 0.7

    def test_multiple_questions(self, service):
        """Test multiple questions detection."""
        query = "What is RAG? How does it work? Why is it useful?"
        analysis = service.analyze_query_complexity(query)

        assert analysis.factors["multiple_questions"]["count"] == 3
        assert analysis.factors["multiple_questions"]["score"] > 0.5

    def test_temporal_complexity(self, service):
        """Test temporal complexity detection."""
        query = "Explain the evolution and timeline of RAG systems over time"
        analysis = service.analyze_query_complexity(query)

        assert analysis.factors["temporal"]["score"] > 0
        assert (
            "temporal" in analysis.reasoning.lower()
            or "evolution" in analysis.reasoning.lower()
        )

    def test_entity_complexity(self, service):
        """Test entity complexity detection."""
        query = "Compare RAG and fine-tuning and prompt engineering and retrieval"
        analysis = service.analyze_query_complexity(query)

        assert analysis.factors["entity"]["score"] > 0

    def test_question_types(self, service):
        """Test different question type classifications."""
        # Factual
        factual = service.analyze_query_complexity("What is machine learning?")
        assert factual.question_type == "factual"

        # Comparative
        comparative = service.analyze_query_complexity("Compare RAG vs fine-tuning")
        assert comparative.question_type == "comparative"

        # Analytical
        analytical = service.analyze_query_complexity("Why does RAG work better?")
        assert analytical.question_type == "analytical"

    def test_reasoning_generation(self, service):
        """Test reasoning string generation."""
        query = "Compare and analyze RAG systems"
        analysis = service.analyze_query_complexity(query)

        assert isinstance(analysis.reasoning, str)
        assert len(analysis.reasoning) > 0
        assert analysis.complexity.value.upper() in analysis.reasoning

    def test_threshold_boundaries(self, service):
        """Test classification at threshold boundaries."""
        # Test with custom thresholds
        custom_service = AdaptiveRAGService(threshold_simple=0.3, threshold_complex=0.7)

        # Query that should be near boundaries
        query = "What is RAG and how does it work?"
        analysis = custom_service.analyze_query_complexity(query)

        assert isinstance(analysis.complexity, QueryComplexity)
        assert 0.0 <= analysis.score <= 1.0

    def test_empty_query(self, service):
        """Test handling of empty query."""
        query = ""
        analysis = service.analyze_query_complexity(query)

        # Should not crash, should return valid analysis
        assert isinstance(analysis, ComplexityAnalysis)
        assert analysis.word_count == 0

    def test_very_long_query(self, service):
        """Test handling of very long query."""
        query = " ".join(["word"] * 100)
        analysis = service.analyze_query_complexity(query)

        assert analysis.word_count == 100
        assert analysis.factors["word_count"]["score"] == 1.0

    def test_special_characters(self, service):
        """Test handling of special characters."""
        query = "What is RAG? (Retrieval-Augmented Generation) & how does it work?"
        analysis = service.analyze_query_complexity(query)

        assert isinstance(analysis, ComplexityAnalysis)
        assert analysis.complexity in [QueryComplexity.SIMPLE, QueryComplexity.MEDIUM]

    def test_language_detection(self, service):
        """Test language detection."""
        # English
        en_query = "What is machine learning?"
        en_analysis = service.analyze_query_complexity(en_query)
        assert en_analysis.language == "en"

        # Korean
        ko_query = "머신러닝이 무엇인가요?"
        ko_analysis = service.analyze_query_complexity(ko_query)
        assert ko_analysis.language == "ko"

        # Mixed
        mixed_query = "What is 머신러닝?"
        mixed_analysis = service.analyze_query_complexity(mixed_query)
        assert mixed_analysis.language == "mixed"

    def test_korean_particles(self, service):
        """Test Korean particle detection."""
        query = "RAG는 무엇이고 어떻게 작동하나요?"
        analysis = service.analyze_query_complexity(query, language="ko")

        assert analysis.language == "ko"
        assert isinstance(analysis.complexity, QueryComplexity)

    def test_korean_honorifics(self, service):
        """Test Korean honorific detection."""
        query = "RAG에 대해 설명해주세요"
        analysis = service.analyze_query_complexity(query, language="ko")

        assert analysis.language == "ko"
        assert isinstance(analysis.complexity, QueryComplexity)

    def test_score_normalization(self, service):
        """Test that scores are properly normalized to 0.0-1.0."""
        queries = [
            "What?",
            "What is RAG?",
            "Compare RAG and fine-tuning",
            "Analyze the evolution of RAG systems over time and explain why",
        ]

        for query in queries:
            analysis = service.analyze_query_complexity(query)
            assert 0.0 <= analysis.score <= 1.0
            assert 0.0 <= analysis.confidence <= 1.0

    def test_get_adaptive_config(self, service):
        """Test get_adaptive_config with enhanced analysis."""
        query = "Compare RAG and fine-tuning"
        config = service.get_adaptive_config(query)

        assert "complexity" in config
        assert "complexity_score" in config
        assert "confidence" in config
        assert "complexity_analysis" in config
        assert "factors" in config["complexity_analysis"]
        assert "reasoning" in config["complexity_analysis"]
        assert "language" in config["complexity_analysis"]
        assert "question_type" in config["complexity_analysis"]

    def test_timestamp_in_analysis(self, service):
        """Test that timestamp is included in analysis."""
        query = "What is RAG?"
        analysis = service.analyze_query_complexity(query)

        assert hasattr(analysis, "timestamp")
        assert analysis.timestamp is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_none_query(self, service):
        """Test handling of None query."""
        # Should handle gracefully
        try:
            analysis = service.analyze_query_complexity(None)
            # If it doesn't crash, check it returns valid default
            assert isinstance(analysis, ComplexityAnalysis)
        except (TypeError, AttributeError):
            # Expected to fail, which is acceptable
            pass

    def test_numeric_query(self, service):
        """Test handling of numeric query."""
        query = "12345"
        analysis = service.analyze_query_complexity(query)

        assert isinstance(analysis, ComplexityAnalysis)

    def test_unicode_query(self, service):
        """Test handling of various Unicode characters."""
        query = "What is RAG? 🤖 機械学習 مرحبا"
        analysis = service.analyze_query_complexity(query)

        assert isinstance(analysis, ComplexityAnalysis)

    def test_consistency(self, service):
        """Test that same query produces consistent results."""
        query = "Compare RAG and fine-tuning"

        analysis1 = service.analyze_query_complexity(query)
        analysis2 = service.analyze_query_complexity(query)

        assert analysis1.complexity == analysis2.complexity
        assert analysis1.score == analysis2.score
        assert analysis1.question_type == analysis2.question_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
