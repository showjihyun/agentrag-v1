#!/bin/bash

# Run all workflow tests
# Usage: ./tests/run-all-tests.sh

set -e

echo "=================================="
echo "Workflow Tools Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to run tests
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${YELLOW}Running: $test_name${NC}"
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if eval "$test_command"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    echo ""
}

# 1. Backend Unit Tests
echo "=================================="
echo "1. Backend Unit Tests"
echo "=================================="
run_test "Workflow Tools Unit Tests" "cd backend && python -m pytest tests/unit/test_workflow_tools.py -v"

# 2. Backend Integration Tests
echo "=================================="
echo "2. Backend Integration Tests"
echo "=================================="
run_test "Workflow API Integration Tests" "cd backend && python -m pytest tests/integration/test_workflow_api.py -v"

# 3. Frontend Component Tests
echo "=================================="
echo "3. Frontend Component Tests"
echo "=================================="
run_test "Tool Config Components" "cd frontend && npm test -- tool-configs.test.tsx --passWithNoTests"

# 4. System Verification
echo "=================================="
echo "4. System Verification"
echo "=================================="
run_test "System Setup Verification" "python tests/workflow-scenarios/verify-setup.py"

# Summary
echo "=================================="
echo "Test Summary"
echo "=================================="
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Some tests failed${NC}"
    exit 1
fi
