#!/bin/bash
# Test runner script

echo "🧪 Running Agentic RAG Tests..."
echo ""

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run different test suites based on argument
case "$1" in
    "unit")
        echo "Running unit tests..."
        pytest tests/unit/ -v -m unit
        ;;
    "integration")
        echo "Running integration tests..."
        pytest tests/integration/ -v -m integration
        ;;
    "security")
        echo "Running security tests..."
        pytest tests/ -v -m security
        ;;
    "coverage")
        echo "Running tests with coverage..."
        pytest --cov=. --cov-report=html --cov-report=term
        echo ""
        echo "📊 Coverage report generated in htmlcov/index.html"
        ;;
    "fast")
        echo "Running fast tests only..."
        pytest tests/ -v -m "not slow"
        ;;
    *)
        echo "Running all tests..."
        pytest tests/ -v
        ;;
esac

echo ""
echo "✅ Tests complete!"
