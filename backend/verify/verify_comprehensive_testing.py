"""
Verification script for comprehensive adaptive routing testing.

Runs all test suites and generates coverage report.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")

    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode == 0


def main():
    """Run all tests and generate coverage report."""
    # Set UTF-8 encoding for Windows
    if sys.platform == "win32":
        import codecs

        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

    print("=" * 80)
    print("COMPREHENSIVE ADAPTIVE ROUTING TEST VERIFICATION")
    print("=" * 80)

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)

    results = {}

    # 1. Unit Tests - IntelligentModeRouter
    results["unit_router"] = run_command(
        ["pytest", "tests/unit/test_intelligent_mode_router.py", "-v", "--tb=short"],
        "Unit Tests: IntelligentModeRouter",
    )

    # 2. Unit Tests - QueryPatternLearner
    results["unit_pattern"] = run_command(
        ["pytest", "tests/unit/test_query_pattern_learner.py", "-v", "--tb=short"],
        "Unit Tests: QueryPatternLearner",
    )

    # 3. Unit Tests - ThresholdTuner
    results["unit_tuner"] = run_command(
        ["pytest", "tests/unit/test_threshold_tuner.py", "-v", "--tb=short"],
        "Unit Tests: ThresholdTuner",
    )

    # 4. Unit Tests - AdaptiveMetrics
    results["unit_metrics"] = run_command(
        ["pytest", "tests/unit/test_adaptive_metrics.py", "-v", "--tb=short"],
        "Unit Tests: AdaptiveMetrics",
    )

    # 5. Integration Tests - E2E Flows
    results["integration_e2e"] = run_command(
        [
            "pytest",
            "tests/integration/test_adaptive_routing_e2e.py",
            "-v",
            "--tb=short",
        ],
        "Integration Tests: End-to-End Flows",
    )

    # 6. Performance Tests - Mode Latency
    results["performance"] = run_command(
        ["pytest", "tests/performance/test_mode_latency.py", "-v", "-s", "--tb=short"],
        "Performance Tests: Mode Latency",
    )

    # 7. Coverage Report
    print("\n" + "=" * 80)
    print("GENERATING COVERAGE REPORT")
    print("=" * 80 + "\n")

    coverage_cmd = [
        "pytest",
        "tests/unit/test_intelligent_mode_router.py",
        "tests/unit/test_query_pattern_learner.py",
        "tests/unit/test_threshold_tuner.py",
        "tests/unit/test_adaptive_metrics.py",
        "tests/integration/test_adaptive_routing_e2e.py",
        "--cov=services.intelligent_mode_router",
        "--cov=services.query_pattern_learner",
        "--cov=services.threshold_tuner",
        "--cov=services.adaptive_metrics",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov/adaptive_routing",
        "-v",
    ]

    results["coverage"] = run_command(coverage_cmd, "Coverage Analysis")

    # Print Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80 + "\n")

    all_passed = True
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name:30s}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 80)

    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED")
        print("\nCoverage report generated at: htmlcov/adaptive_routing/index.html")
        print("\nNext steps:")
        print("1. Review coverage report to ensure >85% coverage")
        print("2. Check performance test results meet targets")
        print("3. Review any warnings or edge cases")
        return 0
    else:
        print("[ERROR] SOME TESTS FAILED")
        print("\nPlease review the failed tests above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
