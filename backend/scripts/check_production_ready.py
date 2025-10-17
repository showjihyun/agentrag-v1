"""Production readiness checker script."""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ProductionChecker:
    """Check if system is ready for production deployment."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def check(self, name: str, condition: bool, error_msg: str = "") -> bool:
        """Run a check and print result."""
        if condition:
            print(f"{GREEN}✓{RESET} {name}")
            self.checks_passed += 1
            return True
        else:
            print(f"{RED}✗{RESET} {name}")
            if error_msg:
                print(f"  {RED}→{RESET} {error_msg}")
            self.checks_failed += 1
            return False

    def warn(self, name: str, message: str):
        """Print a warning."""
        print(f"{YELLOW}⚠{RESET} {name}")
        print(f"  {YELLOW}→{RESET} {message}")
        self.warnings += 1

    def section(self, title: str):
        """Print section header."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}{title}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

    def check_file_exists(self, filepath: str) -> bool:
        """Check if file exists."""
        return Path(filepath).exists()

    def check_directory_exists(self, dirpath: str) -> bool:
        """Check if directory exists."""
        return Path(dirpath).is_dir()

    def check_env_file(self) -> bool:
        """Check .env file configuration."""
        if not self.check_file_exists(".env"):
            return False

        required_vars = [
            "DATABASE_URL",
            "SECRET_KEY",
            "REDIS_HOST",
            "MILVUS_HOST",
        ]

        with open(".env", "r") as f:
            content = f.read()

        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)

        if missing:
            print(f"  {RED}→{RESET} Missing variables: {', '.join(missing)}")
            return False

        return True

    def run_all_checks(self):
        """Run all production readiness checks."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Production Readiness Checker{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")

        # 1. File Structure
        self.section("1. File Structure")
        self.check("Backend directory exists", self.check_directory_exists("backend"))
        self.check("Frontend directory exists", self.check_directory_exists("frontend"))
        self.check(
            "Tests directory exists", self.check_directory_exists("backend/tests")
        )

        # 2. Configuration Files
        self.section("2. Configuration Files")
        self.check(
            ".env file exists",
            self.check_file_exists(".env"),
            "Create .env from .env.example",
        )
        self.check(".env.example exists", self.check_file_exists(".env.example"))
        self.check(
            "docker-compose.yml exists", self.check_file_exists("docker-compose.yml")
        )
        self.check(
            "docker-compose.prod.yml exists",
            self.check_file_exists("docker-compose.prod.yml"),
        )

        # 3. Database Models
        self.section("3. Database Models")
        models = [
            "backend/db/models/user.py",
            "backend/db/models/document.py",
            "backend/db/models/conversation.py",
            "backend/db/models/feedback.py",
            "backend/db/models/permission.py",
            "backend/db/models/usage.py",
        ]
        for model in models:
            self.check(f"{Path(model).name} exists", self.check_file_exists(model))

        # 4. Repositories
        self.section("4. Repository Layer")
        repositories = [
            "backend/db/repositories/user_repository.py",
            "backend/db/repositories/document_repository.py",
            "backend/db/repositories/session_repository.py",
            "backend/db/repositories/message_repository.py",
            "backend/db/repositories/feedback_repository.py",
            "backend/db/repositories/permission_repository.py",
            "backend/db/repositories/usage_repository.py",
        ]
        for repo in repositories:
            self.check(f"{Path(repo).name} exists", self.check_file_exists(repo))

        # 5. Security
        self.section("5. Security")
        self.check(
            "Security utilities exist",
            self.check_file_exists("backend/core/security.py"),
        )
        self.check(
            "Validators exist", self.check_file_exists("backend/core/validators.py")
        )
        self.check(
            "Auth service exists",
            self.check_file_exists("backend/services/auth_service.py"),
        )

        # 6. Performance
        self.section("6. Performance Optimization")
        self.check(
            "Performance utilities exist",
            self.check_file_exists("backend/core/performance.py"),
        )
        self.check(
            "Cache manager exists",
            self.check_file_exists("backend/core/cache_manager.py"),
        )
        self.check(
            "Query optimizer exists",
            self.check_file_exists("backend/core/query_optimizer.py"),
        )

        # 7. Monitoring
        self.section("7. Monitoring & Observability")
        self.check(
            "Monitoring utilities exist",
            self.check_file_exists("backend/core/monitoring.py"),
        )
        self.check(
            "Health check API exists", self.check_file_exists("backend/api/health.py")
        )
        self.check(
            "Monitoring middleware exists",
            self.check_file_exists("backend/middleware/monitoring_middleware.py"),
        )

        # 8. Testing
        self.section("8. Testing Infrastructure")
        self.check(
            "Unit tests exist", self.check_directory_exists("backend/tests/unit")
        )
        self.check(
            "Integration tests exist",
            self.check_directory_exists("backend/tests/integration"),
        )
        self.check("pytest.ini exists", self.check_file_exists("backend/pytest.ini"))
        self.check(
            "Test requirements exist",
            self.check_file_exists("backend/requirements-test.txt"),
        )

        # 9. Documentation
        self.section("9. Documentation")
        docs = [
            "README.md",
            "DEPLOYMENT_GUIDE.md",
            "QUICK_START_PRODUCTION.md",
            "PRODUCTION_READY_PHASE_COMPLETE.md",
        ]
        for doc in docs:
            self.check(f"{doc} exists", self.check_file_exists(doc))

        # 10. Warnings
        self.section("10. Recommendations")

        if not self.check_file_exists("backend/logs"):
            self.warn(
                "Logs directory", "Create backend/logs directory for application logs"
            )

        if not self.check_file_exists(".gitignore"):
            self.warn(".gitignore file", "Create .gitignore to exclude sensitive files")

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print check summary."""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Summary{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")

        total = self.checks_passed + self.checks_failed
        pass_rate = (self.checks_passed / total * 100) if total > 0 else 0

        print(f"Total Checks: {total}")
        print(f"{GREEN}Passed: {self.checks_passed}{RESET}")
        print(f"{RED}Failed: {self.checks_failed}{RESET}")
        print(f"{YELLOW}Warnings: {self.warnings}{RESET}")
        print(f"\nPass Rate: {pass_rate:.1f}%")

        if self.checks_failed == 0:
            print(f"\n{GREEN}{'='*60}{RESET}")
            print(f"{GREEN}✓ System is READY for production deployment!{RESET}")
            print(f"{GREEN}{'='*60}{RESET}\n")
            return 0
        else:
            print(f"\n{RED}{'='*60}{RESET}")
            print(f"{RED}✗ System is NOT ready for production{RESET}")
            print(f"{RED}Please fix the failed checks above{RESET}")
            print(f"{RED}{'='*60}{RESET}\n")
            return 1


def main():
    """Main entry point."""
    checker = ProductionChecker()
    exit_code = checker.run_all_checks()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
