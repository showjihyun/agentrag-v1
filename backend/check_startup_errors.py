"""
Backend startup error checker
Checks for common import and configuration errors before starting the server
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def check_imports():
    """Check if all required imports work"""
    errors = []

    print("Checking imports...")

    # Check main imports
    try:
        from backend.config import settings

        print("✓ Config loaded successfully")
    except Exception as e:
        errors.append(f"Config import error: {e}")

    # Check API imports
    try:
        from backend.api import auth, conversations, documents, query

        print("✓ API modules loaded")
    except Exception as e:
        errors.append(f"API import error: {e}")

    # Check models
    try:
        from backend.models.error import ErrorResponse, ValidationErrorResponse

        print("✓ Error models loaded")
    except Exception as e:
        errors.append(f"Models import error: {e}")

    # Check core dependencies
    try:
        from backend.core.dependencies import get_container

        print("✓ Core dependencies loaded")
    except Exception as e:
        errors.append(f"Dependencies import error: {e}")

    return errors


def check_env_file():
    """Check if .env file exists and has required variables"""
    errors = []

    print("\nChecking .env file...")

    if not os.path.exists(".env"):
        errors.append(".env file not found")
        return errors

    print("✓ .env file exists")

    # Check required variables
    required_vars = [
        "LLM_PROVIDER",
        "LLM_MODEL",
        "MILVUS_HOST",
        "REDIS_HOST",
        "DATABASE_URL",
    ]

    with open(".env", "r") as f:
        env_content = f.read()

    for var in required_vars:
        if f"{var}=" in env_content:
            print(f"✓ {var} is set")
        else:
            errors.append(f"Missing required variable: {var}")

    return errors


def main():
    """Run all checks"""
    print("=" * 60)
    print("Backend Startup Error Checker")
    print("=" * 60)

    all_errors = []

    # Check environment file
    env_errors = check_env_file()
    all_errors.extend(env_errors)

    # Check imports
    import_errors = check_imports()
    all_errors.extend(import_errors)

    print("\n" + "=" * 60)
    if all_errors:
        print("❌ ERRORS FOUND:")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")
        print("\nPlease fix these errors before starting the backend.")
        return 1
    else:
        print("✅ ALL CHECKS PASSED!")
        print("\nYou can now start the backend with:")
        print("  python -m uvicorn backend.main:app --reload --port 8000")
        return 0


if __name__ == "__main__":
    sys.exit(main())
