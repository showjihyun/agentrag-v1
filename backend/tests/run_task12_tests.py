#!/usr/bin/env python3
"""
Script to run all Task 12 integration and E2E tests.

This script provides a convenient way to run all tests related to Task 12
(Integration and End-to-End Testing) with proper reporting.

Usage:
    python run_task12_tests.py [options]

Options:
    --fast          Skip slow performance tests
    --e2e-only      Run only E2E tests
    --integration   Run only integration tests
    --performance   Run only performance tests
    --verbose       Show detailed output
    --coverage      Generate coverage report
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    if result.returncode == 0:
        print(f"\n✅ {description} - PASSED")
        return True
    else:
        print(f"\n❌ {description} - FAILED")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run Task 12 integration and E2E tests"
    )
    parser.add_argument(
        "--fast", action="store_true", help="Skip slow performance tests"
    )
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--performance", action="store_true", help="Run only performance tests"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )

    args = parser.parse_args()

    # Build base pytest command
    base_cmd = ["pytest"]

    if args.verbose:
        base_cmd.append("-v")
    else:
        base_cmd.append("-v")  # Always verbose for better output

    if args.coverage:
        base_cmd.extend(
            [
                "--cov=services",
                "--cov=models",
                "--cov-report=html",
                "--cov-report=term-missing",
            ]
        )

    # Determine which tests to run
    test_files = []

    if args.e2e_only:
        test_files.append("tests/e2e/test_hybrid_modes.py")
    elif args.integration:
        test_files.append("tests/integration/test_path_coordination.py")
    elif args.performance:
        test_files.append("tests/integration/test_hybrid_performance.py")
    else:
        # Run all Task 12 tests
        test_files = [
            "tests/e2e/test_hybrid_modes.py",
            "tests/integration/test_path_coordination.py",
            "tests/integration/test_hybrid_performance.py",
        ]

    # Add marker for fast tests
    if args.fast:
        base_cmd.extend(["-m", "not slow"])

    # Run tests
    results = []

    print("\n" + "=" * 60)
    print("Task 12: Integration and E2E Testing")
    print("=" * 60)

    if args.e2e_only:
        print("\nRunning: E2E Tests Only")
    elif args.integration:
        print("\nRunning: Integration Tests Only")
    elif args.performance:
        print("\nRunning: Performance Tests Only")
    else:
        print("\nRunning: All Task 12 Tests")

    if args.fast:
        print("Mode: Fast (skipping slow tests)")

    print()

    for test_file in test_files:
        cmd = base_cmd + [test_file]

        # Determine test category
        if "e2e" in test_file:
            category = "E2E Tests (Mode Testing)"
        elif "path_coordination" in test_file:
            category = "Integration Tests (Path Coordination)"
        elif "hybrid_performance" in test_file:
            category = "Performance Tests"
        else:
            category = "Tests"

        success = run_command(cmd, category)
        results.append((category, success))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60 + "\n")

    all_passed = True
    for category, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{category}: {status}")
        if not success:
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("✅ All Task 12 tests PASSED!")
        print("=" * 60 + "\n")

        if args.coverage:
            print("Coverage report generated in htmlcov/index.html")

        return 0
    else:
        print("❌ Some tests FAILED. Please review the output above.")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
