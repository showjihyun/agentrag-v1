@echo off
REM Test runner script for Windows

echo 🧪 Running Agentic RAG Tests...
echo.

REM Activate virtual environment if exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run different test suites based on argument
if "%1"=="unit" (
    echo Running unit tests...
    pytest tests/unit/ -v -m unit
) else if "%1"=="integration" (
    echo Running integration tests...
    pytest tests/integration/ -v -m integration
) else if "%1"=="security" (
    echo Running security tests...
    pytest tests/ -v -m security
) else if "%1"=="coverage" (
    echo Running tests with coverage...
    pytest --cov=. --cov-report=html --cov-report=term
    echo.
    echo 📊 Coverage report generated in htmlcov/index.html
) else if "%1"=="fast" (
    echo Running fast tests only...
    pytest tests/ -v -m "not slow"
) else (
    echo Running all tests...
    pytest tests/ -v
)

echo.
echo ✅ Tests complete!
