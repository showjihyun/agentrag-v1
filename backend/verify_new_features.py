"""
Verification script for new features.
Tests imports and basic functionality without external dependencies.
"""

import sys
import asyncio
from datetime import datetime, timezone

def test_imports():
    """Test all new module imports."""
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)
    
    modules_to_test = [
        ("human_in_loop", "services.agent_builder.human_in_loop"),
        ("cost_optimizer", "services.agent_builder.cost_optimizer"),
        ("api_integrator", "services.agent_builder.api_integrator"),
        ("hierarchical_memory", "services.agent_builder.hierarchical_memory"),
        ("prompt_optimizer", "services.agent_builder.prompt_optimizer"),
    ]
    
    results = []
    for name, module_path in modules_to_test:
        try:
            __import__(module_path)
            print(f"✓ {name:20s} - OK")
            results.append((name, True, None))
        except Exception as e:
            print(f"✗ {name:20s} - FAILED: {str(e)[:50]}")
            results.append((name, False, str(e)))
    
    return results


def test_enums():
    """Test enum definitions."""
    print("\n" + "=" * 60)
    print("Testing Enum Definitions")
    print("=" * 60)
    
    try:
        from services.agent_builder.human_in_loop import ApprovalStatus, ApprovalPriority
        print(f"✓ ApprovalStatus: {list(ApprovalStatus)}")
        print(f"✓ ApprovalPriority: {list(ApprovalPriority)}")
        
        from services.agent_builder.hierarchical_memory import MemoryType, MemoryImportance
        print(f"✓ MemoryType: {list(MemoryType)}")
        print(f"✓ MemoryImportance: {list(MemoryImportance)}")
        
        from services.agent_builder.prompt_optimizer import OptimizationStrategy
        print(f"✓ OptimizationStrategy: {list(OptimizationStrategy)}")
        
        from services.agent_builder.api_integrator import HTTPMethod, APIAuthType
        print(f"✓ HTTPMethod: {list(HTTPMethod)}")
        print(f"✓ APIAuthType: {list(APIAuthType)}")
        
        return True
    except Exception as e:
        print(f"✗ Enum test failed: {e}")
        return False


def test_model_pricing():
    """Test ModelPricing calculations."""
    print("\n" + "=" * 60)
    print("Testing Model Pricing")
    print("=" * 60)
    
    try:
        from services.agent_builder.cost_optimizer import ModelPricing
        
        # Test various models
        models = [
            ("gpt-4", 1000, 500),
            ("gpt-3.5-turbo", 1000, 500),
            ("claude-3-opus", 1000, 500),
            ("llama2", 1000, 500),
        ]
        
        for model, prompt_tokens, completion_tokens in models:
            cost = ModelPricing.get_cost(model, prompt_tokens, completion_tokens)
            tier = ModelPricing.get_model_tier(model)
            print(f"✓ {model:20s} - ${cost:.4f} (tier: {tier.value})")
        
        return True
    except Exception as e:
        print(f"✗ Model pricing test failed: {e}")
        return False


def test_approval_request():
    """Test ApprovalRequest creation."""
    print("\n" + "=" * 60)
    print("Testing ApprovalRequest")
    print("=" * 60)
    
    try:
        from services.agent_builder.human_in_loop import (
            ApprovalRequest,
            ApprovalStatus,
            ApprovalPriority
        )
        
        request = ApprovalRequest(
            request_id="test_123",
            agent_id="agent_456",
            execution_id="exec_789",
            action="Test action",
            context={"key": "value"},
            requester_id="user_1",
            approver_ids=["user_2", "user_3"],
            priority=ApprovalPriority.HIGH,
            timeout_seconds=3600
        )
        
        print(f"✓ Request ID: {request.request_id}")
        print(f"✓ Status: {request.status.value}")
        print(f"✓ Priority: {request.priority.value}")
        print(f"✓ Approvers: {len(request.approver_ids)}")
        print(f"✓ Created at: {request.created_at}")
        print(f"✓ Expires at: {request.expires_at}")
        
        return True
    except Exception as e:
        print(f"✗ ApprovalRequest test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_memory():
    """Test Memory creation and scoring."""
    print("\n" + "=" * 60)
    print("Testing Memory System")
    print("=" * 60)
    
    try:
        from services.agent_builder.hierarchical_memory import (
            Memory,
            MemoryType,
            MemoryImportance
        )
        
        memory = Memory(
            memory_id="mem_123",
            content="Test memory content",
            memory_type=MemoryType.SHORT_TERM,
            agent_id="agent_456",
            importance=MemoryImportance.HIGH
        )
        
        print(f"✓ Memory ID: {memory.memory_id}")
        print(f"✓ Type: {memory.memory_type.value}")
        print(f"✓ Importance: {memory.importance.value}")
        print(f"✓ Access count: {memory.access_count}")
        
        # Access memory
        memory.access()
        print(f"✓ After access: {memory.access_count}")
        
        # Calculate relevance score
        score = memory.relevance_score
        print(f"✓ Relevance score: {score:.3f}")
        
        return True
    except Exception as e:
        print(f"✗ Memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompt_version():
    """Test PromptVersion."""
    print("\n" + "=" * 60)
    print("Testing Prompt Version")
    print("=" * 60)
    
    try:
        from services.agent_builder.prompt_optimizer import (
            PromptVersion,
            OptimizationStrategy
        )
        
        version = PromptVersion(
            version_id="v1",
            prompt_text="You are a helpful assistant.",
            agent_id="agent_123",
            created_at=datetime.now(timezone.utc),
            strategy=OptimizationStrategy.PERFORMANCE_BASED
        )
        
        print(f"✓ Version ID: {version.version_id}")
        print(f"✓ Strategy: {version.strategy.value}")
        print(f"✓ Execution count: {version.execution_count}")
        
        # Simulate executions
        version.execution_count = 10
        version.success_count = 8
        version.avg_duration_ms = 2000
        version.avg_feedback_rating = 4.0
        version.feedback_count = 5
        
        print(f"✓ Success rate: {version.success_rate:.2f}")
        print(f"✓ Performance score: {version.performance_score:.3f}")
        
        return True
    except Exception as e:
        print(f"✗ PromptVersion test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoint():
    """Test APIEndpoint."""
    print("\n" + "=" * 60)
    print("Testing API Endpoint")
    print("=" * 60)
    
    try:
        from services.agent_builder.api_integrator import (
            APIEndpoint,
            HTTPMethod
        )
        
        endpoint = APIEndpoint(
            path="/api/users/{user_id}",
            method=HTTPMethod.GET,
            operation_id="getUser",
            summary="Get user by ID",
            description="Retrieves a user by their ID",
            parameters=[
                {"name": "user_id", "in": "path", "required": True}
            ],
            tags=["users"]
        )
        
        print(f"✓ Path: {endpoint.path}")
        print(f"✓ Method: {endpoint.method.value}")
        print(f"✓ Operation ID: {endpoint.operation_id}")
        print(f"✓ Parameters: {len(endpoint.parameters)}")
        print(f"✓ Tags: {endpoint.tags}")
        
        return True
    except Exception as e:
        print(f"✗ APIEndpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("NEW FEATURES VERIFICATION")
    print("=" * 60)
    
    results = []
    
    # Test imports
    import_results = test_imports()
    results.append(("Imports", all(r[1] for r in import_results)))
    
    # Test enums
    results.append(("Enums", test_enums()))
    
    # Test model pricing
    results.append(("Model Pricing", test_model_pricing()))
    
    # Test approval request
    results.append(("Approval Request", test_approval_request()))
    
    # Test memory
    results.append(("Memory System", test_memory()))
    
    # Test prompt version
    results.append(("Prompt Version", test_prompt_version()))
    
    # Test API endpoint
    results.append(("API Endpoint", test_api_endpoint()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8s} - {name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
