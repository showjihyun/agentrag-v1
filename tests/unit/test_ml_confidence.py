"""
Unit tests for ML-based confidence prediction
"""

import pytest
import numpy as np
from backend.ml.confidence_predictor import (
    MLConfidencePredictor,
    ConfidenceFeatures
)
from backend.services.confidence_service import ConfidenceService


class TestMLConfidencePredictor:
    """Test ML confidence predictor"""
    
    def test_predictor_initialization(self):
        """Test predictor initializes correctly"""
        predictor = MLConfidencePredictor()
        assert predictor.weights is not None
        assert 'bias' in predictor.weights
        assert predictor.feature_stats is not None
    
    def test_basic_prediction(self):
        """Test basic confidence prediction"""
        predictor = MLConfidencePredictor()
        
        features = ConfidenceFeatures(
            query_length=10,
            query_complexity=0.5,
            has_keywords=True,
            num_sources=3,
            avg_similarity_score=0.8,
            max_similarity_score=0.9,
            source_diversity=0.7,
            response_length=150,
            has_citations=True,
            reasoning_steps=2,
            mode='balanced',
            has_memory_context=True,
            cache_hit=False,
            user_feedback_history=0.75,
            similar_query_success_rate=0.8
        )
        
        confidence = predictor.predict(features)
        
        # Confidence should be between 0 and 1
        assert 0.0 <= confidence <= 1.0
        
        # With good features, confidence should be reasonably high
        assert confidence > 0.5
    
    def test_prediction_with_uncertainty(self):
        """Test prediction with uncertainty estimation"""
        predictor = MLConfidencePredictor()
        
        features = ConfidenceFeatures(
            query_length=5,
            query_complexity=0.3,
            has_keywords=False,
            num_sources=1,  # Low sources
            avg_similarity_score=0.4,  # Low similarity
            max_similarity_score=0.5,
            source_diversity=0.3,
            response_length=50,
            has_citations=False,
            reasoning_steps=1,
            mode='fast',
            has_memory_context=False,
            cache_hit=False,
            user_feedback_history=0.0,  # No history
            similar_query_success_rate=0.5
        )
        
        confidence, uncertainty = predictor.predict_with_uncertainty(features)
        
        # Should have higher uncertainty with poor features
        assert uncertainty > 0.1
        assert 0.0 <= confidence <= 1.0
    
    def test_high_quality_features(self):
        """Test prediction with high-quality features"""
        predictor = MLConfidencePredictor()
        
        high_quality_features = ConfidenceFeatures(
            query_length=15,
            query_complexity=0.7,
            has_keywords=True,
            num_sources=5,
            avg_similarity_score=0.9,
            max_similarity_score=0.95,
            source_diversity=0.8,
            response_length=300,
            has_citations=True,
            reasoning_steps=4,
            mode='deep',
            has_memory_context=True,
            cache_hit=True,
            user_feedback_history=0.9,
            similar_query_success_rate=0.85
        )
        
        confidence = predictor.predict(high_quality_features)
        
        # High quality features should yield high confidence
        assert confidence > 0.7
    
    def test_low_quality_features(self):
        """Test prediction with low-quality features"""
        predictor = MLConfidencePredictor()
        
        low_quality_features = ConfidenceFeatures(
            query_length=3,
            query_complexity=0.2,
            has_keywords=False,
            num_sources=0,
            avg_similarity_score=0.3,
            max_similarity_score=0.3,
            source_diversity=0.0,
            response_length=20,
            has_citations=False,
            reasoning_steps=0,
            mode='fast',
            has_memory_context=False,
            cache_hit=False,
            user_feedback_history=0.3,
            similar_query_success_rate=0.4
        )
        
        confidence = predictor.predict(low_quality_features)
        
        # Low quality features should yield lower confidence
        assert confidence < 0.6
    
    def test_mode_impact(self):
        """Test that mode affects confidence"""
        predictor = MLConfidencePredictor()
        
        base_features = {
            'query_length': 10,
            'query_complexity': 0.5,
            'has_keywords': True,
            'num_sources': 3,
            'avg_similarity_score': 0.7,
            'max_similarity_score': 0.8,
            'source_diversity': 0.6,
            'response_length': 150,
            'has_citations': True,
            'reasoning_steps': 2,
            'has_memory_context': True,
            'cache_hit': False,
            'user_feedback_history': 0.7,
            'similar_query_success_rate': 0.75
        }
        
        fast_features = ConfidenceFeatures(**base_features, mode='fast')
        balanced_features = ConfidenceFeatures(**base_features, mode='balanced')
        deep_features = ConfidenceFeatures(**base_features, mode='deep')
        
        fast_conf = predictor.predict(fast_features)
        balanced_conf = predictor.predict(balanced_features)
        deep_conf = predictor.predict(deep_features)
        
        # Deep mode should generally have higher confidence
        assert deep_conf >= balanced_conf
    
    def test_feedback_recording(self):
        """Test feedback recording for training"""
        predictor = MLConfidencePredictor()
        
        features = ConfidenceFeatures(
            query_length=10,
            query_complexity=0.5,
            has_keywords=True,
            num_sources=3,
            avg_similarity_score=0.8,
            max_similarity_score=0.9,
            source_diversity=0.7,
            response_length=150,
            has_citations=True,
            reasoning_steps=2,
            mode='balanced',
            has_memory_context=True,
            cache_hit=False,
            user_feedback_history=0.75,
            similar_query_success_rate=0.8
        )
        
        initial_data_count = len(predictor.training_data)
        predictor.record_feedback(features, 0.85)
        
        assert len(predictor.training_data) == initial_data_count + 1


class TestConfidenceService:
    """Test confidence service integration"""
    
    def test_service_initialization(self):
        """Test service initializes correctly"""
        service = ConfidenceService(use_ml=True)
        assert service.ml_predictor is not None
        
        service_no_ml = ConfidenceService(use_ml=False)
        assert service_no_ml.ml_predictor is None
    
    def test_calculate_confidence_ml(self):
        """Test confidence calculation with ML"""
        service = ConfidenceService(use_ml=True)
        
        result = service.calculate_confidence(
            query="What is machine learning?",
            sources=[
                {'score': 0.9, 'document_id': 'doc1', 'cited': True},
                {'score': 0.8, 'document_id': 'doc2', 'cited': True},
                {'score': 0.7, 'document_id': 'doc3', 'cited': False}
            ],
            response="Machine learning is a subset of AI that enables systems to learn from data.",
            mode='balanced',
            reasoning_steps=2,
            has_memory=True,
            cache_hit=False
        )
        
        assert 'confidence' in result
        assert 'method' in result
        assert 0.0 <= result['confidence'] <= 1.0
        assert result['method'] in ['ml', 'blended', 'heuristic']
    
    def test_calculate_confidence_heuristic(self):
        """Test confidence calculation with heuristic fallback"""
        service = ConfidenceService(use_ml=False)
        
        result = service.calculate_confidence(
            query="What is AI?",
            sources=[{'score': 0.8, 'document_id': 'doc1'}],
            response="AI is artificial intelligence.",
            mode='fast',
            reasoning_steps=1,
            has_memory=False,
            cache_hit=True
        )
        
        assert result['method'] == 'heuristic'
        assert 0.0 <= result['confidence'] <= 1.0
    
    def test_query_complexity_estimation(self):
        """Test query complexity estimation"""
        service = ConfidenceService(use_ml=False)
        
        simple_query = "What is AI?"
        complex_query = "Explain how neural networks work, compare different architectures, and analyze their performance"
        
        simple_complexity = service._estimate_query_complexity(simple_query)
        complex_complexity = service._estimate_query_complexity(complex_query)
        
        assert complex_complexity > simple_complexity
        assert 0.0 <= simple_complexity <= 1.0
        assert 0.0 <= complex_complexity <= 1.0
    
    def test_domain_keywords_detection(self):
        """Test domain keyword detection"""
        service = ConfidenceService(use_ml=False)
        
        assert service._has_domain_keywords("What is machine learning?")
        assert service._has_domain_keywords("Explain neural networks")
        assert not service._has_domain_keywords("What is the weather today?")
    
    def test_source_diversity_calculation(self):
        """Test source diversity calculation"""
        service = ConfidenceService(use_ml=False)
        
        diverse_sources = [
            {'document_id': 'doc1'},
            {'document_id': 'doc2'},
            {'document_id': 'doc3'}
        ]
        
        same_sources = [
            {'document_id': 'doc1'},
            {'document_id': 'doc1'},
            {'document_id': 'doc1'}
        ]
        
        diverse_score = service._calculate_source_diversity(diverse_sources)
        same_score = service._calculate_source_diversity(same_sources)
        
        assert diverse_score > same_score
        assert diverse_score == 1.0
        assert same_score < 1.0
    
    def test_feedback_recording(self):
        """Test feedback recording through service"""
        service = ConfidenceService(use_ml=True)
        
        service.record_feedback(
            query="Test query",
            sources=[{'score': 0.8, 'document_id': 'doc1'}],
            response="Test response",
            mode='fast',
            actual_feedback=0.9,
            reasoning_steps=1,
            has_memory=False,
            cache_hit=False
        )
        
        # Should not raise any errors
        assert True


class TestMLvsHeuristic:
    """Compare ML and heuristic approaches"""
    
    def test_ml_vs_heuristic_comparison(self):
        """Test comparison between ML and heuristic"""
        service = ConfidenceService(use_ml=True)
        
        features = ConfidenceFeatures(
            query_length=10,
            query_complexity=0.6,
            has_keywords=True,
            num_sources=4,
            avg_similarity_score=0.85,
            max_similarity_score=0.92,
            source_diversity=0.75,
            response_length=200,
            has_citations=True,
            reasoning_steps=3,
            mode='balanced',
            has_memory_context=True,
            cache_hit=False,
            user_feedback_history=0.8,
            similar_query_success_rate=0.82
        )
        
        heuristic_score = service._calculate_heuristic_confidence(features)
        ml_score = service.ml_predictor.predict(features)
        
        # Both should be in valid range
        assert 0.0 <= heuristic_score <= 1.0
        assert 0.0 <= ml_score <= 1.0
        
        # Scores should be reasonably close (within 30%)
        difference = abs(ml_score - heuristic_score)
        assert difference < 0.3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
