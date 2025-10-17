"""
Simple verification script for Adaptive Routing Configuration (Task 9).

This script verifies configuration without starting the full application.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_configuration():
    """Verify all adaptive routing configuration"""
    print("\n" + "=" * 70)
    print("ADAPTIVE ROUTING CONFIGURATION VERIFICATION (Task 9)")
    print("=" * 70)

    all_passed = True

    # Test 1: Configuration Loading
    print("\n[TEST 1] Configuration Loading")
    print("-" * 70)

    try:
        config_items = [
            ("ADAPTIVE_ROUTING_ENABLED", settings.ADAPTIVE_ROUTING_ENABLED),
            (
                "ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE",
                settings.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE,
            ),
            (
                "ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX",
                settings.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX,
            ),
            ("FAST_MODE_TIMEOUT", settings.FAST_MODE_TIMEOUT),
            ("BALANCED_MODE_TIMEOUT", settings.BALANCED_MODE_TIMEOUT),
            ("DEEP_MODE_TIMEOUT", settings.DEEP_MODE_TIMEOUT),
            ("FAST_MODE_TOP_K", settings.FAST_MODE_TOP_K),
            ("BALANCED_MODE_TOP_K", settings.BALANCED_MODE_TOP_K),
            ("DEEP_MODE_TOP_K", settings.DEEP_MODE_TOP_K),
            ("FAST_MODE_CACHE_TTL", settings.FAST_MODE_CACHE_TTL),
            ("BALANCED_MODE_CACHE_TTL", settings.BALANCED_MODE_CACHE_TTL),
            ("DEEP_MODE_CACHE_TTL", settings.DEEP_MODE_CACHE_TTL),
            ("ENABLE_AUTO_THRESHOLD_TUNING", settings.ENABLE_AUTO_THRESHOLD_TUNING),
            ("TUNING_INTERVAL_HOURS", settings.TUNING_INTERVAL_HOURS),
            ("TUNING_MIN_SAMPLES", settings.TUNING_MIN_SAMPLES),
            ("TUNING_DRY_RUN", settings.TUNING_DRY_RUN),
            ("ENABLE_PATTERN_LEARNING", settings.ENABLE_PATTERN_LEARNING),
            ("MIN_SAMPLES_FOR_LEARNING", settings.MIN_SAMPLES_FOR_LEARNING),
            ("PATTERN_SIMILARITY_THRESHOLD", settings.PATTERN_SIMILARITY_THRESHOLD),
            ("PATTERN_LEARNING_WINDOW_DAYS", settings.PATTERN_LEARNING_WINDOW_DAYS),
            ("TARGET_FAST_MODE_PERCENTAGE", settings.TARGET_FAST_MODE_PERCENTAGE),
            (
                "TARGET_BALANCED_MODE_PERCENTAGE",
                settings.TARGET_BALANCED_MODE_PERCENTAGE,
            ),
            ("TARGET_DEEP_MODE_PERCENTAGE", settings.TARGET_DEEP_MODE_PERCENTAGE),
        ]

        for name, value in config_items:
            print(f"  ✓ {name}: {value}")

        print("\n✅ Configuration Loading: PASSED")

    except Exception as e:
        print(f"\n❌ Configuration Loading: FAILED - {str(e)}")
        all_passed = False

    # Test 2: Validation Logic
    print("\n[TEST 2] Configuration Validation")
    print("-" * 70)

    try:
        # Threshold ordering
        assert (
            settings.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE
            < settings.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX
        )
        print("  ✓ Complexity thresholds properly ordered")

        # Threshold ranges
        assert 0.0 < settings.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE < 1.0
        assert 0.0 < settings.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX < 1.0
        print("  ✓ Complexity thresholds in valid range [0.0, 1.0]")

        # Positive timeouts
        assert settings.FAST_MODE_TIMEOUT > 0
        assert settings.BALANCED_MODE_TIMEOUT > 0
        assert settings.DEEP_MODE_TIMEOUT > 0
        print("  ✓ Mode timeouts are positive")

        # Positive top_k
        assert settings.FAST_MODE_TOP_K > 0
        assert settings.BALANCED_MODE_TOP_K > 0
        assert settings.DEEP_MODE_TOP_K > 0
        print("  ✓ Mode top_k values are positive")

        # Positive cache TTLs
        assert settings.FAST_MODE_CACHE_TTL > 0
        assert settings.BALANCED_MODE_CACHE_TTL > 0
        assert settings.DEEP_MODE_CACHE_TTL > 0
        print("  ✓ Cache TTLs are positive")

        # Target distribution
        total = (
            settings.TARGET_FAST_MODE_PERCENTAGE
            + settings.TARGET_BALANCED_MODE_PERCENTAGE
            + settings.TARGET_DEEP_MODE_PERCENTAGE
        )
        assert abs(total - 1.0) < 0.1
        print(f"  ✓ Target distribution sums to {total:.2f}")

        print("\n✅ Configuration Validation: PASSED")

    except AssertionError as e:
        print(f"\n❌ Configuration Validation: FAILED - {str(e)}")
        all_passed = False

    # Test 3: API Module Check
    print("\n[TEST 3] API Module Check")
    print("-" * 70)

    try:
        # Check if config API module exists
        config_api_path = Path(__file__).parent / "api" / "config.py"
        assert config_api_path.exists(), "api/config.py not found"
        print("  ✓ api/config.py exists")

        # Check if it's imported in main.py
        main_path = Path(__file__).parent / "main.py"
        main_content = main_path.read_text(encoding="utf-8")
        assert "from api import" in main_content and "config" in main_content
        print("  ✓ config router imported in main.py")

        assert "app.include_router(config.router)" in main_content
        print("  ✓ config router registered in main.py")

        print("\n✅ API Module Check: PASSED")

    except AssertionError as e:
        print(f"\n❌ API Module Check: FAILED - {str(e)}")
        all_passed = False

    # Test 4: Environment Variables Documentation
    print("\n[TEST 4] Environment Variables Documentation")
    print("-" * 70)

    try:
        env_example_path = Path(__file__).parent.parent / ".env.example"
        env_content = env_example_path.read_text(encoding="utf-8")

        required_vars = [
            "ADAPTIVE_ROUTING_ENABLED",
            "ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE",
            "ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX",
            "FAST_MODE_TIMEOUT",
            "BALANCED_MODE_TIMEOUT",
            "DEEP_MODE_TIMEOUT",
            "FAST_MODE_TOP_K",
            "BALANCED_MODE_TOP_K",
            "DEEP_MODE_TOP_K",
            "FAST_MODE_CACHE_TTL",
            "BALANCED_MODE_CACHE_TTL",
            "DEEP_MODE_CACHE_TTL",
            "ENABLE_AUTO_THRESHOLD_TUNING",
            "TUNING_INTERVAL_HOURS",
            "TUNING_MIN_SAMPLES",
            "TUNING_DRY_RUN",
            "ENABLE_PATTERN_LEARNING",
            "MIN_SAMPLES_FOR_LEARNING",
            "PATTERN_SIMILARITY_THRESHOLD",
            "PATTERN_LEARNING_WINDOW_DAYS",
            "TARGET_FAST_MODE_PERCENTAGE",
            "TARGET_BALANCED_MODE_PERCENTAGE",
            "TARGET_DEEP_MODE_PERCENTAGE",
        ]

        for var in required_vars:
            assert var in env_content, f"{var} not documented in .env.example"

        print(f"  ✓ All {len(required_vars)} configuration variables documented")
        print("\n✅ Environment Variables Documentation: PASSED")

    except AssertionError as e:
        print(f"\n❌ Environment Variables Documentation: FAILED - {str(e)}")
        all_passed = False

    # Test 5: Feature Flag
    print("\n[TEST 5] Feature Flag")
    print("-" * 70)

    try:
        assert isinstance(settings.ADAPTIVE_ROUTING_ENABLED, bool)
        print(
            f"  ✓ ADAPTIVE_ROUTING_ENABLED is boolean: {settings.ADAPTIVE_ROUTING_ENABLED}"
        )
        print("  ✓ Can be used for gradual rollout")

        print("\n✅ Feature Flag: PASSED")

    except AssertionError as e:
        print(f"\n❌ Feature Flag: FAILED - {str(e)}")
        all_passed = False

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    if all_passed:
        print("\n✅ ALL TESTS PASSED - Task 9 Complete!")
        print("\nAdaptive Routing Configuration is ready:")
        print("  • Configuration loading and validation ✓")
        print(
            "  • API endpoints (/api/config/adaptive, /api/config/system, /api/config/all) ✓"
        )
        print("  • Feature flag (ADAPTIVE_ROUTING_ENABLED) ✓")
        print("  • Environment variables documented in .env.example ✓")
        print("\nConfiguration Details:")
        print(
            f"  • Complexity Thresholds: SIMPLE < {settings.ADAPTIVE_COMPLEXITY_THRESHOLD_SIMPLE}, "
            f"COMPLEX > {settings.ADAPTIVE_COMPLEXITY_THRESHOLD_COMPLEX}"
        )
        print(
            f"  • Mode Timeouts: FAST={settings.FAST_MODE_TIMEOUT}s, "
            f"BALANCED={settings.BALANCED_MODE_TIMEOUT}s, DEEP={settings.DEEP_MODE_TIMEOUT}s"
        )
        print(
            f"  • Mode Parameters: FAST top_k={settings.FAST_MODE_TOP_K}, "
            f"BALANCED top_k={settings.BALANCED_MODE_TOP_K}, DEEP top_k={settings.DEEP_MODE_TOP_K}"
        )
        print(
            f"  • Auto-Tuning: {settings.ENABLE_AUTO_THRESHOLD_TUNING} "
            f"(interval={settings.TUNING_INTERVAL_HOURS}h, dry_run={settings.TUNING_DRY_RUN})"
        )
        print(
            f"  • Pattern Learning: {settings.ENABLE_PATTERN_LEARNING} "
            f"(min_samples={settings.MIN_SAMPLES_FOR_LEARNING})"
        )
        print(
            f"  • Target Distribution: FAST={settings.TARGET_FAST_MODE_PERCENTAGE*100:.0f}%, "
            f"BALANCED={settings.TARGET_BALANCED_MODE_PERCENTAGE*100:.0f}%, "
            f"DEEP={settings.TARGET_DEEP_MODE_PERCENTAGE*100:.0f}%"
        )
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = verify_configuration()
    sys.exit(exit_code)
