@echo off
REM Run all workflow tests
REM Usage: tests\run-all-tests.bat

setlocal enabledelayedexpansion

echo ==================================
echo Workflow Tools Test Suite
echo ==================================
echo.

set TOTAL_TESTS=0
set PASSED_TESTS=0
set FAILED_TESTS=0

REM 1. Backend Unit Tests
echo ==================================
echo 1. Backend Unit Tests
echo ==================================
set /a TOTAL_TESTS+=1
cd backend
python -m pytest tests/unit/test_workflow_tools.py -v
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [91m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
cd ..
echo.

REM 2. Backend Integration Tests
echo ==================================
echo 2. Backend Integration Tests
echo ==================================
set /a TOTAL_TESTS+=1
cd backend
python -m pytest tests/integration/test_workflow_api.py -v
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [91m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
cd ..
echo.

REM 3. Frontend Component Tests
echo ==================================
echo 3. Frontend Component Tests
echo ==================================
set /a TOTAL_TESTS+=1
cd frontend
call npm test -- tool-configs.test.tsx --passWithNoTests
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [91m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
cd ..
echo.

REM 4. System Verification
echo ==================================
echo 4. System Verification
echo ==================================
set /a TOTAL_TESTS+=1
python tests/workflow-scenarios/verify-setup.py
if %ERRORLEVEL% EQU 0 (
    echo [92m✓ PASSED[0m
    set /a PASSED_TESTS+=1
) else (
    echo [91m✗ FAILED[0m
    set /a FAILED_TESTS+=1
)
echo.

REM Summary
echo ==================================
echo Test Summary
echo ==================================
echo Total Tests: %TOTAL_TESTS%
echo Passed: %PASSED_TESTS%
echo Failed: %FAILED_TESTS%
echo.

if %FAILED_TESTS% EQU 0 (
    echo [92m✓ All tests passed![0m
    exit /b 0
) else (
    echo [91m✗ Some tests failed[0m
    exit /b 1
)
