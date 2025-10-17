#!/usr/bin/env python3
"""
Verification script for Hybrid RAG configuration.
Tests that all new configuration parameters are loaded correctly.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings


def verify_hybrid_rag_config():
    """Verify Hybrid RAG configuration is loaded correctly."""
    print("\n" + "=" * 70)
    print("HYBRID RAG CONFIGURATION VERIFICATION")
    print("=" * 70)

    errors = []
    warnings = []

    # Test 1: Feature flag
    print("\n[Test 1] Feature Flag")
    print(f"  HYBRID_RAG_ENABLED: {settings.HYBRID_RAG_ENABLED}")
    if not isinstance(settings.HYBRID_RAG_ENABLED, bool):
        errors.append("HYBRID_RAG_ENABLED must be a boolean")
    else:
        print("  ✓ Feature flag is valid")

    # Test 2: Complexity thresholds
    print("\n[Test 2] Complexity Thresholds")
    print(f"  COMPLEXITY_THRESHOLD_SIMPLE: {settings.COMPLEXITY_THRESHOLD_SIMPLE}")
    print(f"  COMPLEXITY_THRESHOLD_COMPLEX: {settings.COMPLEXITY_THRESHOLD_COMPLEX}")

    if not (0.0 < settings.COMPLEXITY_THRESHOLD_SIMPLE < 1.0):
        errors.append("COMPLEXITY_THRESHOLD_SIMPLE must be between 0.0 and 1.0")

    if not (0.0 < settings.COMPLEXITY_THRESHOLD_COMPLEX < 1.0):
        errors.append("COMPLEXITY_THRESHOLD_COMPLEX must be between 0.0 and 1.0")

    if settings.COMPLEXITY_THRESHOLD_SIMPLE >= settings.COMPLEXITY_THRESHOLD_COMPLEX:
        errors.append(
            "COMPLEXITY_THRESHOLD_SIMPLE must be less than COMPLEXITY_THRESHOLD_COMPLEX"
        )

    if not errors:
        print("  ✓ Complexity thresholds are valid")
        print(f"  ✓ Routing ranges:")
        print(f"    - Static RAG: < {settings.COMPLEXITY_THRESHOLD_SIMPLE}")
        print(
            f"    - Static + Validation: {settings.COMPLEXITY_THRESHOLD_SIMPLE} - {settings.COMPLEXITY_THRESHOLD_COMPLEX}"
        )
        print(f"    - Agentic RAG: > {settings.COMPLEXITY_THRESHOLD_COMPLEX}")

    # Test 3: Confidence thresholds
    print("\n[Test 3] Confidence Thresholds")
    print(f"  CONFIDENCE_THRESHOLD_HIGH: {settings.CONFIDENCE_THRESHOLD_HIGH}")
    print(f"  CONFIDENCE_THRESHOLD_LOW: {settings.CONFIDENCE_THRESHOLD_LOW}")

    if not (0.0 < settings.CONFIDENCE_THRESHOLD_HIGH < 1.0):
        errors.append("CONFIDENCE_THRESHOLD_HIGH must be between 0.0 and 1.0")

    if not (0.0 < settings.CONFIDENCE_THRESHOLD_LOW < 1.0):
        errors.append("CONFIDENCE_THRESHOLD_LOW must be between 0.0 and 1.0")

    if settings.CONFIDENCE_THRESHOLD_LOW >= settings.CONFIDENCE_THRESHOLD_HIGH:
        errors.append(
            "CONFIDENCE_THRESHOLD_LOW must be less than CONFIDENCE_THRESHOLD_HIGH"
        )

    if not errors:
        print("  ✓ Confidence thresholds are valid")
        print(f"  ✓ Escalation ranges:")
        print(
            f"    - High confidence (no escalation): >= {settings.CONFIDENCE_THRESHOLD_HIGH}"
        )
        print(
            f"    - Medium confidence: {settings.CONFIDENCE_THRESHOLD_LOW} - {settings.CONFIDENCE_THRESHOLD_HIGH}"
        )
        print(f"    - Low confidence (escalate): < {settings.CONFIDENCE_THRESHOLD_LOW}")

    # Test 4: Static RAG parameters
    print("\n[Test 4] Static RAG Parameters")
    print(f"  STATIC_RAG_TOP_K: {settings.STATIC_RAG_TOP_K}")
    print(f"  STATIC_RAG_TIMEOUT: {settings.STATIC_RAG_TIMEOUT}s")
    print(f"  ENABLE_STATIC_RAG_CACHE: {settings.ENABLE_STATIC_RAG_CACHE}")
    print(f"  STATIC_RAG_CACHE_TTL: {settings.STATIC_RAG_CACHE_TTL}s")

    if settings.STATIC_RAG_TOP_K < 1:
        errors.append("STATIC_RAG_TOP_K must be at least 1")
    elif settings.STATIC_RAG_TOP_K > 50:
        warnings.append(f"STATIC_RAG_TOP_K ({settings.STATIC_RAG_TOP_K}) is very high")

    if settings.STATIC_RAG_TIMEOUT < 0.5:
        errors.append("STATIC_RAG_TIMEOUT must be at least 0.5 seconds")
    elif settings.STATIC_RAG_TIMEOUT > 10.0:
        warnings.append(
            f"STATIC_RAG_TIMEOUT ({settings.STATIC_RAG_TIMEOUT}s) is very high"
        )

    if settings.STATIC_RAG_CACHE_TTL < 60:
        errors.append("STATIC_RAG_CACHE_TTL must be at least 60 seconds")

    if not errors:
        print("  ✓ Static RAG parameters are valid")

    # Test 5: Agentic RAG parameters
    print("\n[Test 5] Agentic RAG Parameters")
    print(f"  AGENTIC_RAG_MAX_ITERATIONS: {settings.AGENTIC_RAG_MAX_ITERATIONS}")

    if settings.AGENTIC_RAG_MAX_ITERATIONS < 1:
        errors.append("AGENTIC_RAG_MAX_ITERATIONS must be at least 1")
    elif settings.AGENTIC_RAG_MAX_ITERATIONS > 50:
        warnings.append(
            f"AGENTIC_RAG_MAX_ITERATIONS ({settings.AGENTIC_RAG_MAX_ITERATIONS}) is very high"
        )

    if not errors:
        print("  ✓ Agentic RAG parameters are valid")

    # Test 6: Escalation configuration
    print("\n[Test 6] Escalation Configuration")
    print(f"  ENABLE_AUTO_ESCALATION: {settings.ENABLE_AUTO_ESCALATION}")
    print(
        f"  ESCALATION_CONFIDENCE_THRESHOLD: {settings.ESCALATION_CONFIDENCE_THRESHOLD}"
    )

    if settings.ESCALATION_CONFIDENCE_THRESHOLD != settings.CONFIDENCE_THRESHOLD_LOW:
        warnings.append(
            f"ESCALATION_CONFIDENCE_THRESHOLD ({settings.ESCALATION_CONFIDENCE_THRESHOLD}) "
            f"should match CONFIDENCE_THRESHOLD_LOW ({settings.CONFIDENCE_THRESHOLD_LOW}) for consistency"
        )

    if not errors:
        print("  ✓ Escalation configuration is valid")

    # Test 7: Integration with existing config
    print("\n[Test 7] Integration with Existing Configuration")
    print(f"  ENABLE_SPECULATIVE_RAG: {settings.ENABLE_SPECULATIVE_RAG}")
    print(f"  DEFAULT_QUERY_MODE: {settings.DEFAULT_QUERY_MODE}")

    if settings.HYBRID_RAG_ENABLED and not settings.ENABLE_SPECULATIVE_RAG:
        warnings.append(
            "HYBRID_RAG_ENABLED is true but ENABLE_SPECULATIVE_RAG is false. "
            "Consider enabling both for optimal performance."
        )

    print("  ✓ Integration check complete")

    # Summary
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)

    if errors:
        print(f"\n❌ FAILED: {len(errors)} error(s) found:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
    else:
        print("\n✅ SUCCESS: All configuration parameters are valid!")

    if warnings:
        print(f"\n⚠️  {len(warnings)} warning(s):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")

    print("\n" + "=" * 70)

    # Print configuration summary if valid
    if not errors and settings.DEBUG:
        print("\nConfiguration Summary:")
        print(
            f"  Hybrid RAG: {'Enabled' if settings.HYBRID_RAG_ENABLED else 'Disabled'}"
        )
        if settings.HYBRID_RAG_ENABLED:
            print(f"  Expected distribution:")
            print(f"    - Static RAG: 60-70% of queries")
            print(f"    - Agentic RAG: 20-30% of queries")
            print(f"    - Escalations: 10-15% of queries")
            print(f"  Performance targets:")
            print(f"    - Static RAG latency: < {settings.STATIC_RAG_TIMEOUT}s")
            print(f"    - Cache hit rate: > 30%")

    return len(errors) == 0


if __name__ == "__main__":
    try:
        success = verify_hybrid_rag_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: Configuration verification failed with exception:")
        print(f"  {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
