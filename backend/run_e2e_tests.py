"""
Simple runner for E2E tests that handles path setup.
"""

import sys
import os
import asyncio

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Now we can import with backend prefix
from backend.services.agent_builder.human_in_loop import (
    HumanInTheLoop,
    ApprovalPriority,
    ApprovalStatus
)
from backend.services.agent_builder.cost_optimizer import (
    CostOptimizer,
    ModelPricing
)
from backend.services.agent_builder.hierarchical_memory import (
    HierarchicalMemory,
    MemoryType,
    MemoryImportance
)
from backend.services.agent_builder.prompt_optimizer import (
    AutoPromptOptimizer,
    OptimizationStrategy
)
from backend.services.agent_builder.api_integrator import (
    AutoAPIIntegrator,
    APIEndpoint,
    HTTPMethod,
    APIAuthType
)

from unittest.mock import Mock


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


async def test_all_features():
    """Run all E2E tests."""
    print_header("AGENT BUILDER E2E TESTS")
    
    mock_db = Mock()
    results = []
    
    # Test 1: Human-in-the-Loop
    print_header("Test 1: Human-in-the-Loop")
    try:
        hitl = HumanInTheLoop(mock_db)
        print_success("Initialized")
        
        request = await hitl.request_approval(
            agent_id="test_001",
            execution_id="exec_001",
            action="Deploy",
            context={},
            requester_id="user_1",
            approver_ids=["manager_1"],
            priority=ApprovalPriority.HIGH
        )
        print_success(f"Request created: {request.request_id}")
        
        await hitl.approve(request.request_id, "manager_1")
        print_success("Request approved")
        
        results.append(("Human-in-the-Loop", True))
    except Exception as e:
        print_error(f"Failed: {e}")
        results.append(("Human-in-the-Loop", False))
    
    # Test 2: Cost Optimizer
    print_header("Test 2: Cost Optimizer")
    try:
        optimizer = CostOptimizer(mock_db)
        print_success("Initialized")
        
        cost = ModelPricing.get_cost("gpt-3.5-turbo", 1000, 500)
        print_success(f"Cost calculated: ${cost:.4f}")
        
        rec = await optimizer.optimize_for_cost(
            task="Test task",
            budget_usd=0.01,
            quality_threshold=0.8
        )
        print_success(f"Model recommended: {rec['recommended_model']}")
        
        await optimizer.track_execution(
            agent_id="test_001",
            model="gpt-3.5-turbo",
            prompt_tokens=500,
            completion_tokens=300
        )
        print_success("Execution tracked")
        
        results.append(("Cost Optimizer", True))
    except Exception as e:
        print_error(f"Failed: {e}")
        results.append(("Cost Optimizer", False))
    
    # Test 3: Hierarchical Memory
    print_header("Test 3: Hierarchical Memory")
    try:
        memory = HierarchicalMemory(mock_db)
        print_success("Initialized")
        
        mem = await memory.store(
            agent_id="test_001",
            content="Test memory",
            memory_type=MemoryType.SHORT_TERM,
            importance=MemoryImportance.HIGH
        )
        print_success(f"Memory stored: {mem.memory_id}")
        
        stats = memory.get_memory_stats("test_001")
        print_success(f"Total memories: {stats['total_count']}")
        
        results.append(("Hierarchical Memory", True))
    except Exception as e:
        print_error(f"Failed: {e}")
        results.append(("Hierarchical Memory", False))
    
    # Test 4: Prompt Optimizer
    print_header("Test 4: Prompt Optimizer")
    try:
        optimizer = AutoPromptOptimizer(mock_db)
        print_success("Initialized")
        
        optimized = await optimizer.optimize_prompt(
            agent_id="test_001",
            current_prompt="Test prompt",
            performance_data={
                "success_rate": 0.8,
                "avg_duration_ms": 2000
            }
        )
        print_success(f"Prompt optimized ({len(optimized)} chars)")
        
        test = await optimizer.run_ab_test(
            agent_id="test_001",
            prompt_variants=["A", "B", "C"]
        )
        print_success(f"A/B test started: {test['test_id']}")
        
        results.append(("Prompt Optimizer", True))
    except Exception as e:
        print_error(f"Failed: {e}")
        results.append(("Prompt Optimizer", False))
    
    # Test 5: API Integrator
    print_header("Test 5: API Integrator")
    try:
        integrator = AutoAPIIntegrator(mock_db)
        print_success("Initialized")
        
        endpoint = APIEndpoint(
            path="/api/test",
            method=HTTPMethod.GET,
            operation_id="test",
            summary="Test"
        )
        print_success(f"Endpoint created: {endpoint.path}")
        
        await integrator.close()
        print_success("Closed")
        
        results.append(("API Integrator", True))
    except Exception as e:
        print_error(f"Failed: {e}")
        results.append(("API Integrator", False))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(name)
        else:
            print_error(name)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.RESET}\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_all_features())
    sys.exit(0 if success else 1)
