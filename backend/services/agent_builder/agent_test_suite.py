"""
Agent Test Suite for comprehensive testing.

Provides unit, integration, and performance testing for agents.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    """Types of tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    REGRESSION = "regression"


class TestStatus(str, Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    description: str
    test_type: TestType
    input_data: Dict[str, Any]
    expected_output: Optional[Any] = None
    expected_error: Optional[str] = None
    timeout_seconds: int = 30
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class TestResult:
    """Represents a test result."""
    test_case: TestCase
    status: TestStatus
    actual_output: Optional[Any] = None
    error_message: Optional[str] = None
    duration_ms: float = 0
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AgentTestSuite:
    """
    Comprehensive test suite for agents.
    
    Features:
    - Unit testing
    - Integration testing
    - Performance testing
    - Regression testing
    - Test reporting
    """
    
    def __init__(self, db: Session):
        """
        Initialize test suite.
        
        Args:
            db: Database session
        """
        self.db = db
        self.test_cases: List[TestCase] = []
        self.test_results: List[TestResult] = []
        
        logger.info("AgentTestSuite initialized")
    
    def add_test_case(self, test_case: TestCase):
        """Add a test case to the suite."""
        self.test_cases.append(test_case)
        logger.debug(f"Added test case: {test_case.name}")
    
    def add_test_cases(self, test_cases: List[TestCase]):
        """Add multiple test cases."""
        self.test_cases.extend(test_cases)
        logger.info(f"Added {len(test_cases)} test cases")
    
    async def run_test_suite(
        self,
        agent_id: str,
        test_types: Optional[List[TestType]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run test suite for an agent.
        
        Args:
            agent_id: Agent ID to test
            test_types: Optional filter by test types
            tags: Optional filter by tags
            
        Returns:
            Test report
        """
        logger.info(f"Running test suite for agent {agent_id}")
        
        start_time = datetime.now(timezone.utc)
        
        # Filter test cases
        filtered_tests = self._filter_test_cases(test_types, tags)
        
        if not filtered_tests:
            logger.warning("No test cases to run")
            return {
                "agent_id": agent_id,
                "total_tests": 0,
                "message": "No test cases found"
            }
        
        # Run tests
        results = []
        for test_case in filtered_tests:
            result = await self._run_single_test(agent_id, test_case)
            results.append(result)
            self.test_results.append(result)
        
        # Generate report
        report = self._generate_report(agent_id, results, start_time)
        
        logger.info(f"Test suite completed: {report['passed']}/{report['total']} passed")
        
        return report
    
    def _filter_test_cases(
        self,
        test_types: Optional[List[TestType]],
        tags: Optional[List[str]]
    ) -> List[TestCase]:
        """Filter test cases by type and tags."""
        filtered = self.test_cases
        
        if test_types:
            filtered = [tc for tc in filtered if tc.test_type in test_types]
        
        if tags:
            filtered = [
                tc for tc in filtered
                if any(tag in tc.tags for tag in tags)
            ]
        
        return filtered
    
    async def _run_single_test(
        self,
        agent_id: str,
        test_case: TestCase
    ) -> TestResult:
        """Run a single test case."""
        logger.debug(f"Running test: {test_case.name}")
        
        start_time = datetime.now(timezone.utc)
        
        try:
            # Execute test with timeout
            async with asyncio.timeout(test_case.timeout_seconds):
                actual_output = await self._execute_agent(
                    agent_id,
                    test_case.input_data
                )
            
            # Validate output
            status = self._validate_output(
                actual_output,
                test_case.expected_output,
                test_case.expected_error
            )
            
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return TestResult(
                test_case=test_case,
                status=status,
                actual_output=actual_output,
                duration_ms=duration_ms
            )
            
        except asyncio.TimeoutError:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return TestResult(
                test_case=test_case,
                status=TestStatus.FAILED,
                error_message=f"Test timeout after {test_case.timeout_seconds}s",
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                error_message=str(e),
                duration_ms=duration_ms
            )
    
    async def _execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any]
    ) -> Any:
        """Execute agent with input data."""
        # Simplified - in production, use WorkflowExecutor
        # This is a placeholder
        return {"output": "test result"}
    
    def _validate_output(
        self,
        actual_output: Any,
        expected_output: Optional[Any],
        expected_error: Optional[str]
    ) -> TestStatus:
        """Validate test output."""
        if expected_error:
            # Expecting an error
            if isinstance(actual_output, dict) and "error" in actual_output:
                if expected_error in str(actual_output["error"]):
                    return TestStatus.PASSED
            return TestStatus.FAILED
        
        if expected_output is not None:
            # Compare with expected output
            if self._compare_outputs(actual_output, expected_output):
                return TestStatus.PASSED
            return TestStatus.FAILED
        
        # No expected output specified, just check for no errors
        if isinstance(actual_output, dict) and "error" in actual_output:
            return TestStatus.FAILED
        
        return TestStatus.PASSED
    
    def _compare_outputs(self, actual: Any, expected: Any) -> bool:
        """Compare actual and expected outputs."""
        # Simplified comparison
        if isinstance(expected, dict) and isinstance(actual, dict):
            for key, value in expected.items():
                if key not in actual or actual[key] != value:
                    return False
            return True
        
        return actual == expected
    
    def _generate_report(
        self,
        agent_id: str,
        results: List[TestResult],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Generate test report."""
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        
        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        
        # Group by test type
        by_type = {}
        for result in results:
            test_type = result.test_case.test_type.value
            if test_type not in by_type:
                by_type[test_type] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0
                }
            
            by_type[test_type]["total"] += 1
            if result.status == TestStatus.PASSED:
                by_type[test_type]["passed"] += 1
            elif result.status == TestStatus.FAILED:
                by_type[test_type]["failed"] += 1
        
        # Failed tests details
        failed_tests = [
            {
                "name": r.test_case.name,
                "error": r.error_message,
                "expected": r.test_case.expected_output,
                "actual": r.actual_output
            }
            for r in results
            if r.status in [TestStatus.FAILED, TestStatus.ERROR]
        ]
        
        return {
            "agent_id": agent_id,
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "success_rate": passed / total if total > 0 else 0,
            "duration_ms": duration_ms,
            "by_type": by_type,
            "failed_tests": failed_tests,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def export_report(
        self,
        report: Dict[str, Any],
        format: str = "json"
    ) -> str:
        """
        Export test report.
        
        Args:
            report: Test report
            format: Export format (json, html, junit)
            
        Returns:
            Exported report
        """
        if format == "json":
            return json.dumps(report, indent=2)
        elif format == "html":
            return self._export_html(report)
        elif format == "junit":
            return self._export_junit(report)
        else:
            raise ValueError(f"Unknown format: {format}")
    
    def _export_html(self, report: Dict[str, Any]) -> str:
        """Export report as HTML."""
        html = f"""
        <html>
        <head><title>Test Report - {report['agent_id']}</title></head>
        <body>
            <h1>Test Report</h1>
            <p>Agent: {report['agent_id']}</p>
            <p>Total: {report['total']}</p>
            <p>Passed: {report['passed']}</p>
            <p>Failed: {report['failed']}</p>
            <p>Success Rate: {report['success_rate']:.1%}</p>
            <p>Duration: {report['duration_ms']:.0f}ms</p>
        </body>
        </html>
        """
        return html
    
    def _export_junit(self, report: Dict[str, Any]) -> str:
        """Export report as JUnit XML."""
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <testsuite name="{report['agent_id']}" 
                   tests="{report['total']}" 
                   failures="{report['failed']}" 
                   errors="{report['errors']}" 
                   time="{report['duration_ms']/1000:.3f}">
        </testsuite>
        """
        return xml


# Example test cases
EXAMPLE_TEST_CASES = [
    TestCase(
        name="test_basic_query",
        description="Test basic query handling",
        test_type=TestType.UNIT,
        input_data={"query": "What is AI?"},
        expected_output={"output": "AI is..."},
        tags=["basic", "query"]
    ),
    TestCase(
        name="test_complex_query",
        description="Test complex multi-step query",
        test_type=TestType.INTEGRATION,
        input_data={"query": "Analyze and summarize..."},
        timeout_seconds=60,
        tags=["complex", "integration"]
    ),
    TestCase(
        name="test_performance",
        description="Test response time",
        test_type=TestType.PERFORMANCE,
        input_data={"query": "Quick test"},
        timeout_seconds=5,
        tags=["performance"]
    ),
]
