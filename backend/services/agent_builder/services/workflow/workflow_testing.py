"""
Workflow Testing Framework

Provides utilities for testing workflows with mocking,
assertions, and automated test generation.
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestAssertion:
    """A single test assertion."""
    name: str
    condition: str  # Python expression
    expected: Any
    actual: Any = None
    passed: bool = False
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "condition": self.condition,
            "expected": self.expected,
            "actual": self.actual,
            "passed": self.passed,
            "error": self.error,
        }


@dataclass
class NodeMock:
    """Mock configuration for a node."""
    node_id: str
    return_value: Any = None
    side_effect: Optional[Exception] = None
    delay_ms: int = 0
    call_count: int = 0
    calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class TestCase:
    """A workflow test case."""
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    expected_status: str = "completed"
    assertions: List[TestAssertion] = field(default_factory=list)
    node_mocks: Dict[str, NodeMock] = field(default_factory=dict)
    timeout_seconds: int = 30
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Result of a test execution."""
    test_id: str
    test_name: str
    status: TestStatus
    duration_ms: float
    input_data: Dict[str, Any]
    output_data: Optional[Any] = None
    error: Optional[str] = None
    assertions: List[TestAssertion] = field(default_factory=list)
    node_executions: List[Dict[str, Any]] = field(default_factory=list)
    started_at: str = ""
    completed_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "assertions": [a.to_dict() for a in self.assertions],
            "node_executions": self.node_executions,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "passed": self.status == TestStatus.PASSED,
        }


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_name: str
    total: int
    passed: int
    failed: int
    skipped: int
    errors: int
    duration_ms: float
    results: List[TestResult]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "suite_name": self.suite_name,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
            "success_rate": round(self.passed / self.total * 100, 2) if self.total > 0 else 0,
            "results": [r.to_dict() for r in self.results],
        }


class WorkflowTestRunner:
    """
    Test runner for workflows.
    
    Features:
    - Mock node execution
    - Assertion validation
    - Parallel test execution
    - Test coverage tracking
    """
    
    def __init__(self, db_session=None):
        """
        Initialize test runner.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
        self._mocks: Dict[str, NodeMock] = {}
        self._coverage: Dict[str, set] = {}  # workflow_id -> executed_node_ids
    
    async def run_test(
        self,
        workflow: Any,
        test_case: TestCase,
    ) -> TestResult:
        """
        Run a single test case.
        
        Args:
            workflow: Workflow to test
            test_case: Test case to run
            
        Returns:
            Test result
        """
        test_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        
        result = TestResult(
            test_id=test_id,
            test_name=test_case.name,
            status=TestStatus.RUNNING,
            duration_ms=0,
            input_data=test_case.input_data,
            started_at=started_at.isoformat(),
        )
        
        try:
            # Setup mocks
            self._mocks = test_case.node_mocks
            
            # Execute workflow with mocking
            execution_result = await self._execute_with_mocks(
                workflow,
                test_case.input_data,
                test_case.timeout_seconds,
            )
            
            result.output_data = execution_result.get("output")
            result.node_executions = execution_result.get("node_executions", [])
            
            # Track coverage
            workflow_id = str(workflow.id)
            if workflow_id not in self._coverage:
                self._coverage[workflow_id] = set()
            for node_exec in result.node_executions:
                self._coverage[workflow_id].add(node_exec.get("node_id"))
            
            # Check expected status
            actual_status = execution_result.get("status", "completed")
            if actual_status != test_case.expected_status:
                result.status = TestStatus.FAILED
                result.error = f"Expected status '{test_case.expected_status}', got '{actual_status}'"
            else:
                # Run assertions
                all_passed = True
                for assertion in test_case.assertions:
                    assertion_result = self._evaluate_assertion(
                        assertion,
                        execution_result,
                    )
                    result.assertions.append(assertion_result)
                    if not assertion_result.passed:
                        all_passed = False
                
                # Check expected output
                if test_case.expected_output:
                    output_match = self._compare_output(
                        test_case.expected_output,
                        result.output_data,
                    )
                    if not output_match:
                        all_passed = False
                        result.assertions.append(TestAssertion(
                            name="output_match",
                            condition="output == expected",
                            expected=test_case.expected_output,
                            actual=result.output_data,
                            passed=False,
                            error="Output does not match expected",
                        ))
                
                result.status = TestStatus.PASSED if all_passed else TestStatus.FAILED
                
        except asyncio.TimeoutError:
            result.status = TestStatus.ERROR
            result.error = f"Test timed out after {test_case.timeout_seconds}s"
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error = str(e)
            logger.error(f"Test error: {e}", exc_info=True)
        finally:
            completed_at = datetime.utcnow()
            result.completed_at = completed_at.isoformat()
            result.duration_ms = (completed_at - started_at).total_seconds() * 1000
            self._mocks = {}
        
        return result
    
    async def run_suite(
        self,
        workflow: Any,
        test_cases: List[TestCase],
        parallel: bool = False,
        stop_on_failure: bool = False,
    ) -> TestSuiteResult:
        """
        Run a test suite.
        
        Args:
            workflow: Workflow to test
            test_cases: List of test cases
            parallel: Run tests in parallel
            stop_on_failure: Stop on first failure
            
        Returns:
            Suite result
        """
        started_at = datetime.utcnow()
        results: List[TestResult] = []
        
        if parallel:
            # Run all tests concurrently
            tasks = [self.run_test(workflow, tc) for tc in test_cases]
            results = await asyncio.gather(*tasks)
        else:
            # Run sequentially
            for test_case in test_cases:
                result = await self.run_test(workflow, test_case)
                results.append(result)
                
                if stop_on_failure and result.status in [TestStatus.FAILED, TestStatus.ERROR]:
                    # Mark remaining as skipped
                    remaining_idx = test_cases.index(test_case) + 1
                    for remaining in test_cases[remaining_idx:]:
                        results.append(TestResult(
                            test_id=str(uuid.uuid4()),
                            test_name=remaining.name,
                            status=TestStatus.SKIPPED,
                            duration_ms=0,
                            input_data=remaining.input_data,
                        ))
                    break
        
        completed_at = datetime.utcnow()
        
        return TestSuiteResult(
            suite_name=f"Workflow {workflow.id} Tests",
            total=len(results),
            passed=sum(1 for r in results if r.status == TestStatus.PASSED),
            failed=sum(1 for r in results if r.status == TestStatus.FAILED),
            skipped=sum(1 for r in results if r.status == TestStatus.SKIPPED),
            errors=sum(1 for r in results if r.status == TestStatus.ERROR),
            duration_ms=(completed_at - started_at).total_seconds() * 1000,
            results=results,
        )
    
    async def _execute_with_mocks(
        self,
        workflow: Any,
        input_data: Dict[str, Any],
        timeout: int,
    ) -> Dict[str, Any]:
        """Execute workflow with mocked nodes."""
        from backend.services.agent_builder.workflow_executor import WorkflowExecutor
        
        executor = WorkflowExecutor(workflow, self.db)
        
        # Inject mock handler
        original_execute = executor._execute_node_with_retry
        
        async def mocked_execute(node_id, node_type, node_data, data, *args, **kwargs):
            if node_id in self._mocks:
                mock = self._mocks[node_id]
                mock.call_count += 1
                mock.calls.append({"input": data, "timestamp": datetime.utcnow().isoformat()})
                
                if mock.delay_ms > 0:
                    await asyncio.sleep(mock.delay_ms / 1000)
                
                if mock.side_effect:
                    raise mock.side_effect
                
                return mock.return_value
            
            return await original_execute(node_id, node_type, node_data, data, *args, **kwargs)
        
        executor._execute_node_with_retry = mocked_execute
        
        result = await asyncio.wait_for(
            executor._execute_internal(input_data),
            timeout=timeout,
        )
        
        return result
    
    def _evaluate_assertion(
        self,
        assertion: TestAssertion,
        execution_result: Dict[str, Any],
    ) -> TestAssertion:
        """Evaluate a single assertion."""
        try:
            context = {
                "output": execution_result.get("output"),
                "status": execution_result.get("status"),
                "node_results": execution_result.get("node_results", {}),
                "context": execution_result.get("execution_context", {}),
            }
            
            actual = eval(assertion.condition, {"__builtins__": {}}, context)
            assertion.actual = actual
            assertion.passed = actual == assertion.expected
            
            if not assertion.passed:
                assertion.error = f"Expected {assertion.expected}, got {actual}"
                
        except Exception as e:
            assertion.passed = False
            assertion.error = f"Assertion error: {str(e)}"
        
        return assertion
    
    def _compare_output(
        self,
        expected: Dict[str, Any],
        actual: Any,
    ) -> bool:
        """Compare expected and actual output."""
        if not isinstance(actual, dict):
            return False
        
        for key, value in expected.items():
            if key not in actual:
                return False
            if actual[key] != value:
                return False
        
        return True
    
    def get_coverage(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get test coverage for a workflow.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Coverage statistics
        """
        executed = self._coverage.get(workflow_id, set())
        
        return {
            "workflow_id": workflow_id,
            "executed_nodes": list(executed),
            "executed_count": len(executed),
        }


class TestCaseGenerator:
    """
    Generates test cases from workflow definitions.
    
    Features:
    - Automatic test case generation
    - Edge case detection
    - Input variation generation
    """
    
    def generate_test_cases(
        self,
        workflow: Any,
        num_cases: int = 5,
    ) -> List[TestCase]:
        """
        Generate test cases for a workflow.
        
        Args:
            workflow: Workflow to generate tests for
            num_cases: Number of test cases to generate
            
        Returns:
            List of generated test cases
        """
        test_cases = []
        graph = workflow.graph_definition or {}
        nodes = graph.get("nodes", [])
        
        # Basic happy path test
        test_cases.append(TestCase(
            name="happy_path",
            description="Basic workflow execution",
            input_data={"message": "test input"},
            expected_status="completed",
        ))
        
        # Empty input test
        test_cases.append(TestCase(
            name="empty_input",
            description="Workflow with empty input",
            input_data={},
            expected_status="completed",
        ))
        
        # Generate node-specific tests
        for node in nodes[:num_cases - 2]:
            node_type = node.get("type") or node.get("node_type")
            node_id = node.get("id")
            
            if node_type == "condition":
                # Test both branches
                test_cases.append(TestCase(
                    name=f"condition_{node_id}_true",
                    description=f"Test condition node {node_id} true branch",
                    input_data={"condition_value": True},
                    expected_status="completed",
                ))
                test_cases.append(TestCase(
                    name=f"condition_{node_id}_false",
                    description=f"Test condition node {node_id} false branch",
                    input_data={"condition_value": False},
                    expected_status="completed",
                ))
            
            elif node_type in ["ai_agent", "tool"]:
                # Test with mock
                test_cases.append(TestCase(
                    name=f"mock_{node_id}",
                    description=f"Test with mocked {node_type} node",
                    input_data={"message": "test"},
                    node_mocks={
                        node_id: NodeMock(
                            node_id=node_id,
                            return_value={"response": "mocked response"},
                        )
                    },
                    expected_status="completed",
                ))
        
        return test_cases[:num_cases]


# Global test runner
_test_runner: Optional[WorkflowTestRunner] = None


def get_test_runner(db_session=None) -> WorkflowTestRunner:
    """Get or create global test runner."""
    global _test_runner
    if _test_runner is None:
        _test_runner = WorkflowTestRunner(db_session)
    return _test_runner
