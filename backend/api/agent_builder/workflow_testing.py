"""
Workflow Testing API

Endpoints for testing and optimizing workflows.
"""

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.database import get_db
from backend.db.models.user import User
from backend.services.agent_builder.workflow_service import WorkflowService
from backend.services.agent_builder.workflow_testing import (
    get_test_runner,
    TestCase,
    TestAssertion,
    NodeMock,
    TestCaseGenerator,
)
from backend.services.agent_builder.workflow_optimizer import (
    get_optimizer,
    OptimizationType,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent-builder/workflows",
    tags=["agent-builder-testing"],
)


# Request/Response Models
class TestAssertionRequest(BaseModel):
    name: str
    condition: str
    expected: Any


class NodeMockRequest(BaseModel):
    node_id: str
    return_value: Any = None
    delay_ms: int = 0


class TestCaseRequest(BaseModel):
    name: str
    description: str = ""
    input_data: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None
    expected_status: str = "completed"
    assertions: List[TestAssertionRequest] = []
    node_mocks: List[NodeMockRequest] = []
    timeout_seconds: int = 30


class TestSuiteRequest(BaseModel):
    test_cases: List[TestCaseRequest]
    parallel: bool = False
    stop_on_failure: bool = False


class OptimizeRequest(BaseModel):
    optimization_types: List[str] = []
    apply_automatically: bool = False


# Endpoints
@router.post("/{workflow_id}/test")
async def run_single_test(
    workflow_id: str,
    test_case: TestCaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run a single test case against a workflow."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    # Check permissions
    if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    
    # Convert request to TestCase
    tc = TestCase(
        name=test_case.name,
        description=test_case.description,
        input_data=test_case.input_data,
        expected_output=test_case.expected_output,
        expected_status=test_case.expected_status,
        assertions=[
            TestAssertion(
                name=a.name,
                condition=a.condition,
                expected=a.expected,
            )
            for a in test_case.assertions
        ],
        node_mocks={
            m.node_id: NodeMock(
                node_id=m.node_id,
                return_value=m.return_value,
                delay_ms=m.delay_ms,
            )
            for m in test_case.node_mocks
        },
        timeout_seconds=test_case.timeout_seconds,
    )
    
    # Run test
    test_runner = get_test_runner(db)
    result = await test_runner.run_test(workflow, tc)
    
    return result.to_dict()


@router.post("/{workflow_id}/test/suite")
async def run_test_suite(
    workflow_id: str,
    suite: TestSuiteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run a test suite against a workflow."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    
    # Convert requests to TestCases
    test_cases = [
        TestCase(
            name=tc.name,
            description=tc.description,
            input_data=tc.input_data,
            expected_output=tc.expected_output,
            expected_status=tc.expected_status,
            assertions=[
                TestAssertion(name=a.name, condition=a.condition, expected=a.expected)
                for a in tc.assertions
            ],
            node_mocks={
                m.node_id: NodeMock(node_id=m.node_id, return_value=m.return_value, delay_ms=m.delay_ms)
                for m in tc.node_mocks
            },
            timeout_seconds=tc.timeout_seconds,
        )
        for tc in suite.test_cases
    ]
    
    # Run suite
    test_runner = get_test_runner(db)
    result = await test_runner.run_suite(
        workflow,
        test_cases,
        parallel=suite.parallel,
        stop_on_failure=suite.stop_on_failure,
    )
    
    return result.to_dict()


@router.post("/{workflow_id}/test/generate")
async def generate_test_cases(
    workflow_id: str,
    num_cases: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate test cases for a workflow."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    
    generator = TestCaseGenerator()
    test_cases = generator.generate_test_cases(workflow, num_cases)
    
    return {
        "workflow_id": workflow_id,
        "generated_count": len(test_cases),
        "test_cases": [
            {
                "name": tc.name,
                "description": tc.description,
                "input_data": tc.input_data,
                "expected_status": tc.expected_status,
            }
            for tc in test_cases
        ],
    }


@router.get("/{workflow_id}/test/coverage")
async def get_test_coverage(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get test coverage for a workflow."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    test_runner = get_test_runner(db)
    coverage = test_runner.get_coverage(workflow_id)
    
    # Calculate coverage percentage
    graph = workflow.graph_definition or {}
    total_nodes = len(graph.get("nodes", []))
    executed_nodes = coverage.get("executed_count", 0)
    
    coverage["total_nodes"] = total_nodes
    coverage["coverage_percentage"] = (
        round(executed_nodes / total_nodes * 100, 2)
        if total_nodes > 0 else 0
    )
    
    return coverage


@router.get("/{workflow_id}/optimize/analyze")
async def analyze_workflow(
    workflow_id: str,
    include_metrics: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Analyze workflow for optimization opportunities."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    
    optimizer = get_optimizer(db)
    report = await optimizer.analyze(workflow, include_metrics)
    
    return report.to_dict()


@router.post("/{workflow_id}/optimize/apply")
async def apply_optimizations(
    workflow_id: str,
    request: OptimizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply optimizations to a workflow."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    if str(workflow.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    
    # Convert string types to enum
    opt_types = [OptimizationType(t) for t in request.optimization_types]
    
    optimizer = get_optimizer(db)
    result = await optimizer.apply_optimizations(workflow, opt_types)
    
    # Optionally save the optimized graph
    if request.apply_automatically and result.get("optimized_graph"):
        from backend.models.agent_builder import WorkflowUpdate
        
        workflow_service.update_workflow(
            workflow_id,
            WorkflowUpdate(graph_definition=result["optimized_graph"]),
        )
        result["saved"] = True
    else:
        result["saved"] = False
    
    return result


@router.get("/{workflow_id}/metrics")
async def get_workflow_metrics(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get performance metrics for a workflow."""
    workflow_service = WorkflowService(db)
    workflow = workflow_service.get_workflow(workflow_id)
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found",
        )
    
    if str(workflow.user_id) != str(current_user.id) and not workflow.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )
    
    optimizer = get_optimizer(db)
    metrics = await optimizer._get_metrics(workflow_id)
    
    if not metrics:
        return {
            "workflow_id": workflow_id,
            "message": "No execution data available",
        }
    
    return metrics.to_dict()
