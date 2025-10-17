"""
Script to run end-to-end tests with proper setup and reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"\n✗ {description} failed with exit code {result.returncode}")
        return False

    print(f"\n✓ {description} completed successfully")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run end-to-end tests")
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip environment setup (assume services are already running)",
    )
    parser.add_argument(
        "--test-file",
        type=str,
        help="Run specific test file (e.g., test_document_workflow.py)",
    )
    parser.add_argument(
        "--marker", type=str, help="Run tests with specific marker (e.g., 'not slow')"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Change to backend directory
    backend_dir = Path(__file__).parent.parent

    print("=" * 60)
    print("END-TO-END TEST RUNNER")
    print("=" * 60)

    # Step 1: Setup environment (unless skipped)
    if not args.skip_setup:
        if not run_command(
            [sys.executable, str(backend_dir / "tests" / "setup_test_env.py")],
            "Setting up test environment",
        ):
            print("\n✗ Environment setup failed. Exiting.")
            sys.exit(1)
    else:
        print("\n⚠ Skipping environment setup (--skip-setup)")

    # Step 2: Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest"]

    # Add test path
    if args.test_file:
        test_path = backend_dir / "tests" / "e2e" / args.test_file
        if not test_path.exists():
            print(f"\n✗ Test file not found: {test_path}")
            sys.exit(1)
        pytest_cmd.append(str(test_path))
    else:
        pytest_cmd.append(str(backend_dir / "tests" / "e2e"))

    # Add markers
    if args.marker:
        pytest_cmd.extend(["-m", args.marker])

    # Add coverage
    if args.coverage:
        pytest_cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

    # Add verbosity
    if args.verbose:
        pytest_cmd.extend(["-v", "-s"])
    else:
        pytest_cmd.append("-v")

    # Step 3: Run tests
    if not run_command(pytest_cmd, "Running end-to-end tests"):
        print("\n✗ Tests failed")
        sys.exit(1)

    # Step 4: Summary
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)

    if args.coverage:
        print("\nCoverage report generated:")
        print(f"  HTML: {backend_dir / 'htmlcov' / 'index.html'}")

    print("\nTest artifacts:")
    print(f"  Test data: {backend_dir / 'tests' / 'data'}")
    print(f"  Logs: Check pytest output above")


if __name__ == "__main__":
    main()
