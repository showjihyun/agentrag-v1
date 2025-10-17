"""
Unit tests for Query Complexity Analyzer
"""

import pytest
from backend.services.query_complexity_analyzer import (
    QueryComplexityAnalyzer,
    ComplexityLevel,
    get_analyzer,
)
from backend.models.hybrid import QueryMode


class TestQueryComplexityAnalyzer:
    """Test suite for QueryComplexityAnalyzer"""

    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = QueryComplexityAnalyzer()

    def test_simple_factual_query(self):
        """Test simple factual query classification"""
        query = "What is machine learning?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert level == ComplexityLevel.SIMPLE
        assert mode == QueryMode.FAST
        assert confidence > 0.7
        assert reasoning["complexity_score"] < 0.4

    def test_simple_korean_query(self):
        """Test simple Korean query classification"""
        query = "머신러닝이 무엇인가요?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert level == ComplexityLevel.SIMPLE
        assert mode == QueryMode.FAST
        assert confidence > 0.7

    def test_moderate_query(self):
        """Test moderate complexity query"""
        query = "How does machine learning work and what are its applications?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert level == ComplexityLevel.MODERATE
        assert mode == QueryMode.BALANCED
        assert confidence > 0.8
        assert 0.3 < reasoning["complexity_score"] < 0.7

    def test_complex_analytical_query(self):
        """Test complex analytical query"""
        query = "Compare and contrast supervised and unsupervised learning approaches, analyzing their strengths and weaknesses"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert level == ComplexityLevel.COMPLEX
        assert mode == QueryMode.DEEP
        assert reasoning["complexity_score"] > 0.6

    def test_complex_korean_query(self):
        """Test complex Korean query"""
        query = "지도 학습과 비지도 학습의 장단점을 비교 분석하고 각각의 적용 사례를 설명해주세요"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert level == ComplexityLevel.COMPLEX
        assert mode == QueryMode.DEEP

    def test_length_analysis_short(self):
        """Test length analysis for short queries"""
        query = "What is AI?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert reasoning["length_score"] == 0.0
        assert mode == QueryMode.FAST

    def test_length_analysis_long(self):
        """Test length analysis for long queries"""
        query = " ".join(["word"] * 30)  # 30 words
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert reasoning["length_score"] == 1.0

    def test_keyword_analysis_factual(self):
        """Test keyword analysis for factual queries"""
        queries = [
            "What is the definition of neural networks?",
            "Who invented deep learning?",
            "When was the first AI created?",
            "Where is machine learning used?",
        ]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert reasoning["keyword_score"] < 0.5
            assert mode == QueryMode.FAST

    def test_keyword_analysis_analytical(self):
        """Test keyword analysis for analytical queries"""
        queries = [
            "Compare neural networks and decision trees",
            "Analyze the effectiveness of deep learning",
            "Evaluate the pros and cons of reinforcement learning",
        ]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert reasoning["keyword_score"] > 0.6
            assert mode in [QueryMode.BALANCED, QueryMode.DEEP]

    def test_structure_analysis_simple(self):
        """Test structure analysis for simple queries"""
        query = "What is AI?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert reasoning["structure_score"] < 0.5

    def test_structure_analysis_complex(self):
        """Test structure analysis for complex queries"""
        query = "What is AI? How does it work? What are its applications?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert reasoning["structure_score"] > 0.7

    def test_question_type_factual(self):
        """Test question type analysis for factual questions"""
        queries = [
            "What is machine learning?",
            "Who created TensorFlow?",
            "When was PyTorch released?",
        ]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert reasoning["question_type_score"] < 0.4

    def test_question_type_explanatory(self):
        """Test question type analysis for explanatory questions"""
        queries = ["How does backpropagation work?", "Why is deep learning effective?"]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert 0.4 <= reasoning["question_type_score"] <= 0.7

    def test_question_type_analytical(self):
        """Test question type analysis for analytical questions"""
        queries = [
            "Compare CNNs and RNNs",
            "Analyze the impact of batch size on training",
            "Evaluate different optimization algorithms",
        ]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert reasoning["question_type_score"] > 0.7

    def test_reasoning_factors(self):
        """Test that reasoning factors are provided"""
        query = "Compare supervised and unsupervised learning"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert "factors" in reasoning
        assert isinstance(reasoning["factors"], list)
        assert len(reasoning["factors"]) > 0

    def test_mode_explanation(self):
        """Test mode explanation generation"""
        queries_and_modes = [
            ("What is AI?", QueryMode.FAST),
            ("How does machine learning work?", QueryMode.BALANCED),
            (
                "Compare and analyze different neural network architectures",
                QueryMode.DEEP,
            ),
        ]

        for query, expected_mode in queries_and_modes:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            explanation = self.analyzer.get_mode_explanation(mode, reasoning)

            assert isinstance(explanation, str)
            assert len(explanation) > 0
            assert mode.value.upper() in explanation.upper()

    def test_singleton_analyzer(self):
        """Test singleton analyzer instance"""
        analyzer1 = get_analyzer()
        analyzer2 = get_analyzer()

        assert analyzer1 is analyzer2

    def test_edge_case_empty_query(self):
        """Test edge case: empty query"""
        query = ""
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        # Should default to moderate/balanced
        assert mode in [QueryMode.FAST, QueryMode.BALANCED]

    def test_edge_case_very_long_query(self):
        """Test edge case: very long query"""
        query = " ".join(["word"] * 100)  # 100 words
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        assert reasoning["length_score"] == 1.0

    def test_mixed_language_query(self):
        """Test mixed language query (English + Korean)"""
        query = "Compare machine learning과 deep learning의 차이점"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        # Should detect complexity from both languages
        assert mode in [QueryMode.BALANCED, QueryMode.DEEP]

    def test_confidence_scores(self):
        """Test that confidence scores are reasonable"""
        queries = [
            "What is AI?",
            "How does machine learning work?",
            "Compare and analyze different approaches to neural network training",
        ]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert 0.0 <= confidence <= 1.0
            assert confidence > 0.5  # Should be reasonably confident

    def test_complexity_score_range(self):
        """Test that complexity scores are in valid range"""
        queries = [
            "What is AI?",
            "How does machine learning work?",
            "Compare and analyze different approaches",
        ]

        for query in queries:
            level, mode, confidence, reasoning = self.analyzer.analyze(query)
            assert 0.0 <= reasoning["complexity_score"] <= 1.0

    def test_all_score_components_present(self):
        """Test that all score components are present in reasoning"""
        query = "What is machine learning?"
        level, mode, confidence, reasoning = self.analyzer.analyze(query)

        required_keys = [
            "complexity_score",
            "length_score",
            "keyword_score",
            "structure_score",
            "question_type_score",
            "factors",
        ]

        for key in required_keys:
            assert key in reasoning


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
