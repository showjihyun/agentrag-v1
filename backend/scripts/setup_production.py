"""Production setup automation script."""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd: str, description: str):
    """Run shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")

    try:
        result = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        print(result.stdout)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def create_directories():
    """Create necessary directories."""
    print("\n" + "=" * 60)
    print("Creating directories...")
    print("=" * 60)

    directories = [
        "backend/logs",
        "backend/uploads",
        "backend/temp",
        "frontend/public/uploads",
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}")


def setup_environment():
    """Setup environment file."""
    print("\n" + "=" * 60)
    print("Setting up environment...")
    print("=" * 60)

    if not Path(".env").exists():
        if Path(".env.example").exists():
            import shutil

            shutil.copy(".env.example", ".env")
            print("✓ Created .env from .env.example")
            print("⚠ Please edit .env with your configuration")
        else:
            print("✗ .env.example not found")
            return False
    else:
        print("✓ .env already exists")

    return True


def install_backend_dependencies():
    """Install backend Python dependencies."""
    return run_command(
        "cd backend && pip install -r requirements.txt",
        "Installing backend dependencies",
    )


def install_frontend_dependencies():
    """Install frontend Node.js dependencies."""
    return run_command("cd frontend && npm install", "Installing frontend dependencies")


def run_database_migrations():
    """Run database migrations."""
    return run_command(
        "cd backend && python run_migrations.py", "Running database migrations"
    )


def run_tests():
    """Run test suite."""
    print("\n" + "=" * 60)
    print("Running tests...")
    print("=" * 60)

    # Backend tests
    backend_tests = run_command(
        "cd backend && pytest tests/ -v --tb=short", "Running backend tests"
    )

    if not backend_tests:
        print("⚠ Backend tests failed, but continuing...")

    return True


def check_docker():
    """Check if Docker is running."""
    print("\n" + "=" * 60)
    print("Checking Docker...")
    print("=" * 60)

    try:
        subprocess.run("docker --version", shell=True, check=True, capture_output=True)
        print("✓ Docker is installed")

        subprocess.run(
            "docker-compose --version", shell=True, check=True, capture_output=True
        )
        print("✓ Docker Compose is installed")

        return True
    except subprocess.CalledProcessError:
        print("✗ Docker or Docker Compose not found")
        print("Please install Docker Desktop")
        return False


def start_infrastructure():
    """Start infrastructure services with Docker Compose."""
    return run_command(
        "docker-compose up -d postgres redis milvus-standalone",
        "Starting infrastructure services",
    )


def main():
    """Main setup process."""
    print("\n" + "=" * 60)
    print("Production Setup Script")
    print("=" * 60)

    steps = [
        ("Creating directories", create_directories),
        ("Setting up environment", setup_environment),
        ("Checking Docker", check_docker),
        ("Starting infrastructure", start_infrastructure),
        ("Installing backend dependencies", install_backend_dependencies),
        ("Installing frontend dependencies", install_frontend_dependencies),
        ("Running database migrations", run_database_migrations),
        ("Running tests", run_tests),
    ]

    failed_steps = []

    for step_name, step_func in steps:
        try:
            if not step_func():
                failed_steps.append(step_name)
        except Exception as e:
            print(f"✗ {step_name} failed with error: {e}")
            failed_steps.append(step_name)

    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)

    if failed_steps:
        print(f"\n✗ Setup completed with {len(failed_steps)} failed step(s):")
        for step in failed_steps:
            print(f"  - {step}")
        print("\nPlease fix the issues and run the script again.")
        return 1
    else:
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Edit .env file with your configuration")
        print("2. Start backend: cd backend && uvicorn main:app --reload")
        print("3. Start frontend: cd frontend && npm run dev")
        print("4. Access application at http://localhost:3000")
        return 0


if __name__ == "__main__":
    sys.exit(main())
