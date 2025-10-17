"""
Verification script for answer quality evaluation feature.

Tests:
1. AnswerQualityService initialization
2. Source relevance evaluation
3. Grounding evaluation
4. Hallucination detection
5. Completeness evaluation
6. Overall score calculation
7. Quality level assignment
8. Suggestion generation
9. Database model
10. API endpoints
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")

    try:
        from services.answer_quality_service import (
            AnswerQualityService,
            get_answer_quality_service,
        )

        print("✓ AnswerQualityService imported")

        from db.models.feedback import AnswerFeedback

        print("✓ AnswerFeedback model imported")

        from api.feedback import router

        print("✓ Feedback API imported")

        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_service_init():
    """Test AnswerQualityService initialization."""
    print("\nTesting AnswerQualityService initialization...")

    try:
        from services.answer_quality_service import (
            AnswerQualityService,
            get_answer_quality_service,
        )

        # Direct initialization
        service1 = AnswerQualityService()
        print("✓ Direct initialization works")

        # Singleton
        service2 = get_answer_quality_service()
        service3 = get_answer_quality_service()
        assert service2 is service3, "Singleton should return same instance"
        print("✓ Singleton pattern works")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_source_relevance():
    """Test source relevance evaluation."""
    print("\nTesting source relevance evaluation...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        query = "What is machine learning?"
        sources = [
            {
                "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms."
            },
            {"text": "Deep learning uses neural networks with multiple layers."},
        ]

        relevance = service._evaluate_source_relevance(query, sources)

        assert 0 <= relevance <= 1, f"Relevance should be 0-1, got {relevance}"
        assert (
            relevance > 0.3
        ), f"Relevance should be > 0.3 for relevant sources, got {relevance}"

        print(f"✓ Source relevance evaluation: {relevance:.2f}")

        return True
    except Exception as e:
        print(f"✗ Source relevance evaluation failed: {e}")
        return False


def test_grounding():
    """Test answer grounding evaluation."""
    print("\nTesting grounding evaluation...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        answer = "Machine learning is a subset of AI that uses algorithms to learn from data."
        sources = [
            {"text": "Machine learning is a subset of artificial intelligence."},
            {"text": "Algorithms learn from data in machine learning."},
        ]

        grounding = service._evaluate_grounding(answer, sources)

        assert 0 <= grounding <= 1, f"Grounding should be 0-1, got {grounding}"
        assert (
            grounding > 0.5
        ), f"Grounding should be > 0.5 for well-grounded answer, got {grounding}"

        print(f"✓ Grounding evaluation: {grounding:.2f}")

        return True
    except Exception as e:
        print(f"✗ Grounding evaluation failed: {e}")
        return False


def test_hallucination_detection():
    """Test hallucination detection."""
    print("\nTesting hallucination detection...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        # Low risk answer (grounded in sources)
        answer1 = "Machine learning is a subset of AI."
        sources1 = [
            {"text": "Machine learning is a subset of artificial intelligence."}
        ]
        risk1 = service._detect_hallucination(answer1, sources1)

        assert 0 <= risk1 <= 1, f"Risk should be 0-1, got {risk1}"
        assert risk1 < 0.5, f"Risk should be low for grounded answer, got {risk1}"
        print(f"✓ Low risk detection: {risk1:.2f}")

        # High risk answer (specific numbers not in sources)
        answer2 = "Exactly 42.7% of companies use machine learning."
        sources2 = [{"text": "Many companies use machine learning."}]
        risk2 = service._detect_hallucination(answer2, sources2)

        assert risk2 > risk1, f"Risk should be higher for unsupported claims"
        print(f"✓ High risk detection: {risk2:.2f}")

        return True
    except Exception as e:
        print(f"✗ Hallucination detection failed: {e}")
        return False


def test_completeness():
    """Test completeness evaluation."""
    print("\nTesting completeness evaluation...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        # Complete answer
        query1 = "What is machine learning?"
        answer1 = "Machine learning is a subset of AI that uses algorithms to learn from data."
        completeness1 = service._evaluate_completeness(query1, answer1)

        assert (
            0 <= completeness1 <= 1
        ), f"Completeness should be 0-1, got {completeness1}"
        print(f"✓ Completeness evaluation: {completeness1:.2f}")

        # Incomplete answer
        query2 = "What is machine learning and how does it work?"
        answer2 = "It's AI."
        completeness2 = service._evaluate_completeness(query2, answer2)

        assert completeness2 < completeness1, "Incomplete answer should score lower"
        print(f"✓ Incomplete answer detection: {completeness2:.2f}")

        return True
    except Exception as e:
        print(f"✗ Completeness evaluation failed: {e}")
        return False


def test_overall_score():
    """Test overall score calculation."""
    print("\nTesting overall score calculation...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        # Good quality metrics
        score1 = service._calculate_overall_score(
            source_relevance=0.9,
            grounding=0.9,
            hallucination_risk=0.1,
            completeness=0.9,
            length_score=0.9,
            citation_score=0.9,
        )

        assert 0 <= score1 <= 1, f"Score should be 0-1, got {score1}"
        assert score1 > 0.8, f"Good metrics should yield high score, got {score1}"
        print(f"✓ High quality score: {score1:.2f}")

        # Poor quality metrics
        score2 = service._calculate_overall_score(
            source_relevance=0.3,
            grounding=0.3,
            hallucination_risk=0.8,
            completeness=0.3,
            length_score=0.5,
            citation_score=0.2,
        )

        assert score2 < score1, "Poor metrics should yield lower score"
        print(f"✓ Low quality score: {score2:.2f}")

        # User feedback adjustment
        score3 = service._calculate_overall_score(
            source_relevance=0.7,
            grounding=0.7,
            hallucination_risk=0.3,
            completeness=0.7,
            length_score=0.7,
            citation_score=0.7,
            user_feedback=1,  # Positive
        )

        score4 = service._calculate_overall_score(
            source_relevance=0.7,
            grounding=0.7,
            hallucination_risk=0.3,
            completeness=0.7,
            length_score=0.7,
            citation_score=0.7,
            user_feedback=-1,  # Negative
        )

        assert score3 > score4, "Positive feedback should boost score"
        print(f"✓ Feedback adjustment works: {score3:.2f} vs {score4:.2f}")

        return True
    except Exception as e:
        print(f"✗ Overall score calculation failed: {e}")
        return False


def test_quality_levels():
    """Test quality level assignment."""
    print("\nTesting quality level assignment...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        levels = [
            (0.95, "excellent"),
            (0.80, "good"),
            (0.65, "acceptable"),
            (0.45, "poor"),
            (0.20, "very_poor"),
        ]

        for score, expected_level in levels:
            level = service._get_quality_level(score)
            assert (
                level == expected_level
            ), f"Score {score} should be '{expected_level}', got '{level}'"
            print(f"✓ {score:.2f} → {level}")

        return True
    except Exception as e:
        print(f"✗ Quality level assignment failed: {e}")
        return False


def test_suggestions():
    """Test suggestion generation."""
    print("\nTesting suggestion generation...")

    try:
        from services.answer_quality_service import AnswerQualityService

        service = AnswerQualityService()

        # Poor metrics should generate suggestions
        suggestions = service._generate_suggestions(
            source_relevance=0.3,
            grounding=0.4,
            hallucination_risk=0.7,
            completeness=0.5,
            length_score=0.4,
            citation_score=0.3,
        )

        assert isinstance(suggestions, list), "Suggestions should be a list"
        assert len(suggestions) > 0, "Should generate suggestions for poor metrics"
        print(f"✓ Generated {len(suggestions)} suggestions")

        # Good metrics should have minimal suggestions
        suggestions2 = service._generate_suggestions(
            source_relevance=0.9,
            grounding=0.9,
            hallucination_risk=0.1,
            completeness=0.9,
            length_score=0.9,
            citation_score=0.9,
        )

        assert len(suggestions2) <= 1, "Good metrics should have few suggestions"
        print(f"✓ Good metrics: {len(suggestions2)} suggestions")

        return True
    except Exception as e:
        print(f"✗ Suggestion generation failed: {e}")
        return False


def test_database_model():
    """Test AnswerFeedback database model."""
    print("\nTesting AnswerFeedback model...")

    try:
        from db.models.feedback import AnswerFeedback
        from sqlalchemy import inspect

        # Check model columns
        mapper = inspect(AnswerFeedback)
        columns = {col.key for col in mapper.columns}

        required_fields = {
            "id",
            "user_id",
            "session_id",
            "message_id",
            "query",
            "answer",
            "overall_score",
            "source_relevance",
            "grounding_score",
            "hallucination_risk",
            "completeness_score",
            "length_score",
            "citation_score",
            "user_rating",
            "user_comment",
            "quality_level",
            "suggestions",
            "created_at",
            "feedback_at",
        }

        missing_fields = required_fields - columns

        if missing_fields:
            print(f"✗ Missing fields: {missing_fields}")
            print("  Run migration: backend/db/migrations/add_answer_feedback.sql")
            return False

        print("✓ All required fields present")

        return True
    except Exception as e:
        print(f"✗ Database model check failed: {e}")
        return False


def test_api_endpoints():
    """Test API endpoints are defined."""
    print("\nTesting API endpoints...")

    try:
        from api.feedback import router

        # Check routes
        routes = [route.path for route in router.routes]

        required_endpoints = [
            "/api/feedback/submit",
            "/api/feedback/stats",
            "/api/feedback/history",
        ]

        for endpoint in required_endpoints:
            if endpoint in routes:
                print(f"✓ {endpoint} defined")
            else:
                print(f"✗ {endpoint} missing")
                return False

        return True
    except Exception as e:
        print(f"✗ API endpoint check failed: {e}")
        return False


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Answer Quality Evaluation Feature Verification")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Service Init", test_service_init),
        ("Source Relevance", test_source_relevance),
        ("Grounding", test_grounding),
        ("Hallucination Detection", test_hallucination_detection),
        ("Completeness", test_completeness),
        ("Overall Score", test_overall_score),
        ("Quality Levels", test_quality_levels),
        ("Suggestions", test_suggestions),
        ("Database Model", test_database_model),
        ("API Endpoints", test_api_endpoints),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} test crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All verification tests passed!")
        print("\nNext steps:")
        print("1. Run database migration:")
        print(
            "   psql -U postgres -d your_database -f backend/db/migrations/add_answer_feedback.sql"
        )
        print("2. Test with actual queries")
        print("3. Monitor quality metrics in dashboard")
        print("4. Collect user feedback")
        print("5. Analyze quality trends")
        return 0
    else:
        print("\n⚠ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
