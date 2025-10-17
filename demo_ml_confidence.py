#!/usr/bin/env python3
"""
ML 신뢰도 예측 데모 스크립트

실제 사용 예제를 보여줍니다.
"""

import sys
import os

# 백엔드 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from ml.confidence_predictor import MLConfidencePredictor, ConfidenceFeatures
from services.confidence_service import ConfidenceService


def print_section(title):
    """섹션 제목 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_basic_prediction():
    """기본 예측 데모"""
    print_section("1. 기본 신뢰도 예측")
    
    predictor = MLConfidencePredictor()
    
    # 고품질 특징
    high_quality = ConfidenceFeatures(
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
    
    confidence = predictor.predict(high_quality)
    print(f"\n✅ 고품질 쿼리 신뢰도: {confidence:.2%}")
    print(f"   - 많은 소스 (5개)")
    print(f"   - 높은 유사도 (0.9)")
    print(f"   - Deep 모드")
    print(f"   - 캐시 히트")
    
    # 저품질 특징
    low_quality = ConfidenceFeatures(
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
    
    confidence = predictor.predict(low_quality)
    print(f"\n❌ 저품질 쿼리 신뢰도: {confidence:.2%}")
    print(f"   - 소스 없음 (0개)")
    print(f"   - 낮은 유사도 (0.3)")
    print(f"   - Fast 모드")
    print(f"   - 캐시 미스")


def demo_uncertainty():
    """불확실성 추정 데모"""
    print_section("2. 불확실성 추정")
    
    predictor = MLConfidencePredictor()
    
    # 불확실한 케이스
    uncertain = ConfidenceFeatures(
        query_length=10,
        query_complexity=0.5,
        has_keywords=True,
        num_sources=1,  # 적은 소스
        avg_similarity_score=0.4,  # 낮은 유사도
        max_similarity_score=0.5,
        source_diversity=0.3,
        response_length=100,
        has_citations=False,
        reasoning_steps=1,
        mode='fast',
        has_memory_context=False,
        cache_hit=False,
        user_feedback_history=0.0,  # 히스토리 없음
        similar_query_success_rate=0.5
    )
    
    confidence, uncertainty = predictor.predict_with_uncertainty(uncertain)
    print(f"\n⚠️  불확실한 케이스:")
    print(f"   신뢰도: {confidence:.2%}")
    print(f"   불확실성: {uncertainty:.2%}")
    
    if uncertainty > 0.2:
        print(f"\n   → 높은 불확실성! 휴리스틱과 블렌딩 권장")
    else:
        print(f"\n   → 낮은 불확실성, ML 예측 사용 가능")


def demo_service_integration():
    """서비스 통합 데모"""
    print_section("3. ConfidenceService 사용")
    
    service = ConfidenceService(use_ml=True)
    
    # 실제 쿼리 시뮬레이션
    result = service.calculate_confidence(
        query="What is machine learning and how does it work?",
        sources=[
            {'score': 0.92, 'document_id': 'doc1', 'cited': True},
            {'score': 0.88, 'document_id': 'doc2', 'cited': True},
            {'score': 0.75, 'document_id': 'doc3', 'cited': False}
        ],
        response="Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It works by using algorithms to analyze data, identify patterns, and make decisions.",
        mode='balanced',
        reasoning_steps=3,
        has_memory=True,
        cache_hit=False
    )
    
    print(f"\n📊 쿼리 분석 결과:")
    print(f"   신뢰도: {result['confidence']:.2%}")
    print(f"   방법: {result['method']}")
    
    if 'uncertainty' in result:
        print(f"   불확실성: {result['uncertainty']:.2%}")
    
    if 'ml_score' in result and 'heuristic_score' in result:
        print(f"\n   ML 점수: {result['ml_score']:.2%}")
        print(f"   휴리스틱 점수: {result['heuristic_score']:.2%}")
        print(f"   → 블렌딩 사용됨")


def demo_feedback_learning():
    """피드백 학습 데모"""
    print_section("4. 피드백 학습")
    
    service = ConfidenceService(use_ml=True)
    predictor = service.ml_predictor
    
    print(f"\n현재 학습 데이터: {len(predictor.training_data)}개")
    
    # 피드백 시뮬레이션
    print("\n피드백 기록 중...")
    for i in range(5):
        service.record_feedback(
            query=f"Test query {i}",
            sources=[{'score': 0.8, 'document_id': f'doc{i}'}],
            response=f"Test response {i}",
            mode='balanced',
            actual_feedback=0.7 + (i * 0.05),  # 0.7 ~ 0.9
            reasoning_steps=2,
            has_memory=False,
            cache_hit=False
        )
        print(f"   ✓ 피드백 {i+1}/5 기록됨")
    
    print(f"\n업데이트된 학습 데이터: {len(predictor.training_data)}개")
    print(f"\n💡 100개 이상 수집 시 자동 학습됩니다.")


def demo_low_quality_improvement():
    """저품질 쿼리 개선 데모"""
    print_section("5. 저품질 쿼리 개선 (NEW!)")
    
    service = ConfidenceService(use_ml=False)  # 휴리스틱만 사용
    
    # 시나리오 1: 일반 지식 쿼리 (소스 없음)
    print("\n📚 시나리오 1: 일반 지식 쿼리")
    result1 = service.calculate_confidence(
        query="What is machine learning?",  # 일반 지식 쿼리
        sources=[],  # 소스 없음
        response="Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It uses algorithms to analyze data, identify patterns, and make decisions with minimal human intervention.",
        mode='balanced',
        reasoning_steps=2
    )
    print(f"   쿼리: 'What is machine learning?'")
    print(f"   소스: 없음")
    print(f"   신뢰도: {result1['confidence']:.2%}")
    print(f"   방법: {result1['method']}")
    if 'llm_baseline' in result1:
        print(f"   LLM 기본: {result1['llm_baseline']:.2%}")
    if 'response_quality' in result1:
        print(f"   응답 품질: {result1['response_quality']:.2%}")
    
    # 시나리오 2: 짧은 응답 (소스 없음)
    print("\n📝 시나리오 2: 짧은 응답")
    result2 = service.calculate_confidence(
        query="Define AI",
        sources=[],
        response="AI is artificial intelligence.",  # 짧은 응답
        mode='fast',
        reasoning_steps=0
    )
    print(f"   쿼리: 'Define AI'")
    print(f"   소스: 없음")
    print(f"   응답: 짧음 (5단어)")
    print(f"   신뢰도: {result2['confidence']:.2%}")
    print(f"   → 최소 임계값 적용됨")
    
    # 시나리오 3: 고품질 응답 (소스 없음)
    print("\n✨ 시나리오 3: 고품질 응답")
    result3 = service.calculate_confidence(
        query="Explain how neural networks work",
        sources=[],
        response="""Neural networks are computational models inspired by the human brain. They consist of:

1. Input Layer: Receives the initial data
2. Hidden Layers: Process information through weighted connections
3. Output Layer: Produces the final result

The network learns by adjusting weights through backpropagation, minimizing the difference between predicted and actual outputs. This process enables the network to recognize patterns and make predictions on new data.""",
        mode='deep',
        reasoning_steps=3
    )
    print(f"   쿼리: 'Explain how neural networks work'")
    print(f"   소스: 없음")
    print(f"   응답: 고품질 (구조화, 긴 길이)")
    print(f"   신뢰도: {result3['confidence']:.2%}")
    if 'quality_boost' in result3:
        print(f"   품질 보너스: +{result3['quality_boost']:.2%}")
    
    print("\n💡 개선 효과:")
    print(f"   - 일반 지식 쿼리: {result1['confidence']:.2%} (이전: ~5%)")
    print(f"   - 짧은 응답: {result2['confidence']:.2%} (최소 임계값)")
    print(f"   - 고품질 응답: {result3['confidence']:.2%} (품질 보너스)")


def demo_comparison():
    """ML vs 휴리스틱 비교 데모"""
    print_section("6. ML vs 휴리스틱 비교")
    
    service = ConfidenceService(use_ml=True)
    
    features = ConfidenceFeatures(
        query_length=12,
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
    
    heuristic = service._calculate_heuristic_confidence(features)
    ml_score = service.ml_predictor.predict(features)
    
    print(f"\n📊 동일한 특징에 대한 비교:")
    print(f"   휴리스틱 방식: {heuristic:.2%}")
    print(f"   ML 방식: {ml_score:.2%}")
    print(f"   차이: {abs(ml_score - heuristic):.2%}")
    
    if abs(ml_score - heuristic) < 0.1:
        print(f"\n   ✅ 두 방식이 유사한 결과 (차이 < 10%)")
    else:
        print(f"\n   ⚠️  두 방식의 차이가 큼 (차이 ≥ 10%)")


def main():
    """메인 실행 함수"""
    print("\n" + "🤖 ML 신뢰도 예측 시스템 데모".center(60))
    print("=" * 60)
    
    try:
        demo_basic_prediction()
        demo_uncertainty()
        demo_service_integration()
        demo_feedback_learning()
        demo_low_quality_improvement()
        demo_comparison()
        
        print("\n" + "=" * 60)
        print("✅ 모든 데모 완료!".center(60))
        print("=" * 60)
        
        print("\n📚 다음 단계:")
        print("   1. 실제 쿼리에 적용: backend/api/query.py 참고")
        print("   2. 피드백 수집: backend/api/feedback.py 참고")
        print("   3. 모델 학습: 100개 이상 피드백 수집 후 자동 학습")
        print("   4. API 사용: POST /api/confidence/calculate")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
