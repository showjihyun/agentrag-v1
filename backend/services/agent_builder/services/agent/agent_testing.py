"""
Agent Testing Framework

Provides testing capabilities for agents:
- Unit tests for individual components
- Scenario-based integration tests
- Performance benchmarks
- Regression testing
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
import time
import json

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestType(str, Enum):
    """Types of tests."""
    UNIT = "unit"
    INTEGRATION = "integration"
    SCENARIO = "scenario"
    PERFORMANCE = "performance"
    REGRESSION = "regression"


@dataclass
class TestAssertion:
    """Single test assertion."""
    name: str
    expected: Any
    actual: Any
    passed: bool
    message: str = ""


@dataclass
class TestCase:
    """Single test case definition."""
    id: str
    name: str
    description: str
    test_type: TestType
    
    # Input
    input_text: str
    input_context: Dict[str, Any] = field(default_factory=dict)
    
    # Expected output
    expected_output: Optional[str] = None
    expected_contains: List[str] = field(default_factory=list)
    expected_not_contains: List[str] = field(default_factory=list)
    expected_tool_calls: List[str] = field(default_factory=list)
    
    # Performance expectations
    max_duration_ms: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["test_type"] = self.test_type.value
        return data


@dataclass
class TestResult:
    """Result of a single test execution."""
    test_id: str
    test_name: str
    status: TestStatus
    
    # Timing
    started_at: str
    completed_at: str
    duration_ms: float
    
    # Results
    assertions: List[TestAssertion] = field(default_factory=list)
    output: Optional[str] = None
    error: Optional[str] = None
    
    # Metrics
    token_usage: int = 0
    tool_calls: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class TestSuite:
    """Collection of test cases."""
    id: str
    name: str
    description: str
    agent_id: str
    
    test_cases: List[TestCase] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "agent_id": self.agent_id,
            "test_cases": [tc.to_dict() for tc in self.test_cases],
            "created_at": self.created_at,
            "created_by": self.created_by,
            "tags": self.tags,
            "total_tests": len(self.test_cases),
        }


@dataclass
class TestRunResult:
    """Result of running a test suite."""
    suite_id: str
    suite_name: str
    agent_id: str
    
    # Timing
    started_at: str
    completed_at: str
    total_duration_ms: float
    
    # Results
    results: List[TestResult] = field(default_factory=list)
    
    # Summary
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "suite_name": self.suite_name,
            "agent_id": self.agent_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_ms": self.total_duration_ms,
            "results": [r.to_dict() for r in self.results],
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "errors": self.errors,
                "pass_rate": round(self.passed / self.total * 100, 2) if self.total > 0 else 0,
            },
        }


class AgentTestRunner:
    """
    Test runner for agent testing.
    
    Features:
    - Run individual tests or full suites
    - Parallel test execution
    - Detailed assertions
    - Performance tracking
    """
    
    def __init__(self, agent_executor: Any):
        self.agent_executor = agent_executor
        self.test_suites: Dict[str, TestSuite] = {}
    
    def create_test_suite(
        self,
        name: str,
        description: str,
        agent_id: str,
        created_by: str,
    ) -> TestSuite:
        """Create a new test suite."""
        import uuid
        
        suite = TestSuite(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            agent_id=agent_id,
            created_by=created_by,
        )
        
        self.test_suites[suite.id] = suite
        return suite
    
    def add_test_case(
        self,
        suite_id: str,
        name: str,
        description: str,
        input_text: str,
        test_type: TestType = TestType.UNIT,
        **kwargs,
    ) -> TestCase:
        """Add a test case to a suite."""
        import uuid
        
        suite = self.test_suites.get(suite_id)
        if not suite:
            raise ValueError(f"Suite not found: {suite_id}")
        
        test_case = TestCase(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            test_type=test_type,
            input_text=input_text,
            **kwargs,
        )
        
        suite.test_cases.append(test_case)
        return test_case
    
    async def run_test(
        self,
        test_case: TestCase,
        agent_id: str,
        user_id: str,
    ) -> TestResult:
        """Run a single test case."""
        started_at = datetime.utcnow()
        start_time = time.perf_counter()
        
        assertions = []
        output = None
        error = None
        status = TestStatus.RUNNING
        token_usage = 0
        tool_calls = []
        
        try:
            # Execute agent
            result = await self.agent_executor.execute_agent(
                agent_id=agent_id,
                user_id=user_id,
                input_data={"input": test_case.input_text, **test_case.input_context},
            )
            
            output = result.output_data.get("output", "") if result.output_data else ""
            token_usage = result.output_data.get("tokens_used", 0) if result.output_data else 0
            
            # Run assertions
            if test_case.expected_output:
                passed = output.strip() == test_case.expected_output.strip()
                assertions.append(TestAssertion(
                    name="exact_match",
                    expected=test_case.expected_output,
                    actual=output,
                    passed=passed,
                    message="" if passed else "Output does not match expected",
                ))
            
            for expected in test_case.expected_contains:
                passed = expected.lower() in output.lower()
                assertions.append(TestAssertion(
                    name=f"contains_{expected[:20]}",
                    expected=expected,
                    actual=output[:200],
                    passed=passed,
                    message="" if passed else f"Output does not contain: {expected}",
                ))
            
            for not_expected in test_case.expected_not_contains:
                passed = not_expected.lower() not in output.lower()
                assertions.append(TestAssertion(
                    name=f"not_contains_{not_expected[:20]}",
                    expected=f"NOT {not_expected}",
                    actual=output[:200],
                    passed=passed,
                    message="" if passed else f"Output should not contain: {not_expected}",
                ))
            
            # Determine status
            if all(a.passed for a in assertions):
                status = TestStatus.PASSED
            else:
                status = TestStatus.FAILED
                
        except Exception as e:
            error = str(e)
            status = TestStatus.ERROR
            logger.error(f"Test error: {e}", exc_info=True)
        
        completed_at = datetime.utcnow()
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Check performance assertions
        if test_case.max_duration_ms and duration_ms > test_case.max_duration_ms:
            assertions.append(TestAssertion(
                name="max_duration",
                expected=f"<= {test_case.max_duration_ms}ms",
                actual=f"{duration_ms:.0f}ms",
                passed=False,
                message=f"Exceeded max duration: {duration_ms:.0f}ms > {test_case.max_duration_ms}ms",
            ))
            if status == TestStatus.PASSED:
                status = TestStatus.FAILED
        
        if test_case.max_tokens and token_usage > test_case.max_tokens:
            assertions.append(TestAssertion(
                name="max_tokens",
                expected=f"<= {test_case.max_tokens}",
                actual=str(token_usage),
                passed=False,
                message=f"Exceeded max tokens: {token_usage} > {test_case.max_tokens}",
            ))
            if status == TestStatus.PASSED:
                status = TestStatus.FAILED
        
        return TestResult(
            test_id=test_case.id,
            test_name=test_case.name,
            status=status,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            duration_ms=duration_ms,
            assertions=assertions,
            output=output[:1000] if output else None,
            error=error,
            token_usage=token_usage,
            tool_calls=tool_calls,
        )
    
    async def run_suite(
        self,
        suite_id: str,
        user_id: str,
        parallel: bool = False,
    ) -> TestRunResult:
        """Run all tests in a suite."""
        suite = self.test_suites.get(suite_id)
        if not suite:
            raise ValueError(f"Suite not found: {suite_id}")
        
        started_at = datetime.utcnow()
        start_time = time.perf_counter()
        
        results = []
        enabled_tests = [tc for tc in suite.test_cases if tc.enabled]
        
        if parallel:
            # Run tests in parallel
            tasks = [
                self.run_test(tc, suite.agent_id, user_id)
                for tc in enabled_tests
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    results[i] = TestResult(
                        test_id=enabled_tests[i].id,
                        test_name=enabled_tests[i].name,
                        status=TestStatus.ERROR,
                        started_at=started_at.isoformat(),
                        completed_at=datetime.utcnow().isoformat(),
                        duration_ms=0,
                        error=str(result),
                    )
        else:
            # Run tests sequentially
            for tc in enabled_tests:
                result = await self.run_test(tc, suite.agent_id, user_id)
                results.append(result)
        
        # Add skipped tests
        skipped_tests = [tc for tc in suite.test_cases if not tc.enabled]
        for tc in skipped_tests:
            results.append(TestResult(
                test_id=tc.id,
                test_name=tc.name,
                status=TestStatus.SKIPPED,
                started_at=started_at.isoformat(),
                completed_at=started_at.isoformat(),
                duration_ms=0,
            ))
        
        completed_at = datetime.utcnow()
        total_duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Calculate summary
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in results if r.status == TestStatus.ERROR)
        
        return TestRunResult(
            suite_id=suite.id,
            suite_name=suite.name,
            agent_id=suite.agent_id,
            started_at=started_at.isoformat(),
            completed_at=completed_at.isoformat(),
            total_duration_ms=total_duration_ms,
            results=results,
            total=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
        )


# ============================================================================
# Pre-built Test Templates
# ============================================================================

def create_basic_test_suite(
    agent_id: str,
    agent_name: str,
    created_by: str,
    runner: AgentTestRunner,
) -> TestSuite:
    """Create a basic test suite with common tests."""
    suite = runner.create_test_suite(
        name=f"Basic Tests - {agent_name}",
        description="Basic functionality tests",
        agent_id=agent_id,
        created_by=created_by,
    )
    
    # Basic response test
    runner.add_test_case(
        suite_id=suite.id,
        name="Basic Response",
        description="Agent should respond to a simple greeting",
        input_text="Hello, how are you?",
        test_type=TestType.UNIT,
        expected_not_contains=["error", "exception", "failed"],
        max_duration_ms=10000,
    )
    
    # Empty input test
    runner.add_test_case(
        suite_id=suite.id,
        name="Empty Input Handling",
        description="Agent should handle empty input gracefully",
        input_text="",
        test_type=TestType.UNIT,
        expected_not_contains=["error", "exception"],
    )
    
    # Long input test
    runner.add_test_case(
        suite_id=suite.id,
        name="Long Input Handling",
        description="Agent should handle long input",
        input_text="Please help me with " + "this task " * 100,
        test_type=TestType.UNIT,
        max_duration_ms=30000,
    )
    
    return suite


def create_performance_test_suite(
    agent_id: str,
    agent_name: str,
    created_by: str,
    runner: AgentTestRunner,
) -> TestSuite:
    """Create a performance test suite."""
    suite = runner.create_test_suite(
        name=f"Performance Tests - {agent_name}",
        description="Performance and latency tests",
        agent_id=agent_id,
        created_by=created_by,
    )
    
    # Fast response test
    runner.add_test_case(
        suite_id=suite.id,
        name="Fast Response",
        description="Simple query should respond quickly",
        input_text="What is 2+2?",
        test_type=TestType.PERFORMANCE,
        max_duration_ms=5000,
        max_tokens=500,
    )
    
    # Token efficiency test
    runner.add_test_case(
        suite_id=suite.id,
        name="Token Efficiency",
        description="Response should be concise",
        input_text="Give me a one-word answer: What color is the sky?",
        test_type=TestType.PERFORMANCE,
        max_tokens=100,
    )
    
    return suite
