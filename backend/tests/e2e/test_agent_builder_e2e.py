"""
End-to-End tests for Agent Builder core features.

Tests the complete flow of creating, testing, and managing agents.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.RESET}")


class AgentBuilderE2ETest:
    """E2E test suite for Agent Builder."""
    
    def __init__(self):
        self.results = []
        self.mock_db = None
    
    async def setup(self):
        """Setup test environment."""
        print_info("Setting up test environment...")
        # Mock database session
        from unittest.mock import Mock
        self.mock_db = Mock()
        print_success("Test environment ready")
    
    async def test_human_in_loop_flow(self) -> bool:
        """Test complete Human-in-the-Loop flow."""
        print_header("Test 1: Human-in-the-Loop Flow")
        
        try:
            from backend.services.agent_builder.human_in_loop import (
                HumanInTheLoop,
                ApprovalPriority,
                ApprovalStatus
            )
            
            # Initialize
            hitl = HumanInTheLoop(self.mock_db)
            print_success("HumanInTheLoop initialized")
            
            # Create approval request
            request = await hitl.request_approval(
                agent_id="test_agent_001",
                execution_id="test_exec_001",
                action="Deploy to production",
                context={"environment": "production", "version": "1.0.0"},
                requester_id="user_001",
                approver_ids=["manager_001", "manager_002"],
                priority=ApprovalPriority.HIGH,
                timeout_seconds=3600
            )
            print_success(f"Approval request created: {request.request_id}")
            
            # Verify request state
            assert request.status == ApprovalStatus.PENDING
            assert request.priority == ApprovalPriority.HIGH
            assert len(request.approver_ids) == 2
            print_success("Request state verified")
            
            # Approve request
            await hitl.approve(
                request_id=request.request_id,
                approver_id="manager_001",
                comment="Looks good to deploy"
            )
            print_success("Request approved")
            
            # Verify approval
            assert request.status == ApprovalStatus.APPROVED
            assert request.approved_by == "manager_001"
            print_success("Approval verified")
            
            # Test feedback collection
            feedback_request = await hitl.collect_feedback(
                execution_id="test_exec_001",
                questions=[
                    {"id": "q1", "type": "rating", "question": "Quality?"},
                    {"id": "q2", "type": "text", "question": "Comments?"}
                ],
                responder_ids=["user_001", "user_002"]
            )
            print_success(f"Feedback request created: {feedback_request.request_id}")
            
            # Submit feedback
            await hitl.submit_feedback(
                request_id=feedback_request.request_id,
                responder_id="user_001",
                responses={"q1": 5, "q2": "Excellent!"}
            )
            print_success("Feedback submitted")
            
            # Get pending approvals
            pending = hitl.get_pending_approvals(approver_id="manager_002")
            print_success(f"Retrieved {len(pending)} pending approvals")
            
            return True
            
        except Exception as e:
            print_error(f"Human-in-the-Loop test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_cost_optimizer_flow(self) -> bool:
        """Test complete Cost Optimizer flow."""
        print_header("Test 2: Cost Optimizer Flow")
        
        try:
            from backend.services.agent_builder.cost_optimizer import (
                CostOptimizer,
                ModelPricing
            )
            
            # Initialize
            optimizer = CostOptimizer(self.mock_db)
            print_success("CostOptimizer initialized")
            
            # Test model pricing
            cost_gpt4 = ModelPricing.get_cost("gpt-4", 1000, 500)
            cost_gpt35 = ModelPricing.get_cost("gpt-3.5-turbo", 1000, 500)
            cost_local = ModelPricing.get_cost("llama2", 1000, 500)
            
            print_success(f"GPT-4 cost: ${cost_gpt4:.4f}")
            print_success(f"GPT-3.5 cost: ${cost_gpt35:.4f}")
            print_success(f"Llama2 cost: ${cost_local:.4f}")
            
            assert cost_gpt4 > cost_gpt35 > cost_local
            print_success("Cost hierarchy verified")
            
            # Optimize for cost
            recommendation = await optimizer.optimize_for_cost(
                task="Analyze customer feedback and extract insights",
                budget_usd=0.01,
                quality_threshold=0.8,
                max_tokens=2000
            )
            print_success(f"Recommended model: {recommendation['recommended_model']}")
            print_success(f"Estimated cost: ${recommendation['estimated_cost_usd']:.4f}")
            print_success(f"Within budget: {recommendation['within_budget']}")
            
            # Track execution
            await optimizer.track_execution(
                agent_id="test_agent_001",
                model="gpt-3.5-turbo",
                prompt_tokens=500,
                completion_tokens=300,
                cached=False
            )
            print_success("Execution tracked")
            
            # Get cost report
            report = optimizer.get_cost_report(agent_id="test_agent_001")
            print_success(f"Total cost: ${report['total_cost_usd']:.4f}")
            print_success(f"Total tokens: {report['total_tokens']}")
            print_success(f"Cache hit rate: {report['cache_hit_rate']:.2%}")
            
            # Test smart cache
            cache_result = await optimizer.smart_cache.get(
                query="What is AI?",
                model="gpt-3.5-turbo"
            )
            print_success(f"Cache lookup: {'HIT' if cache_result else 'MISS'}")
            
            # Cache a response
            await optimizer.smart_cache.set(
                query="What is AI?",
                model="gpt-3.5-turbo",
                response="AI is artificial intelligence...",
                ttl=3600
            )
            print_success("Response cached")
            
            return True
            
        except Exception as e:
            print_error(f"Cost Optimizer test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_hierarchical_memory_flow(self) -> bool:
        """Test complete Hierarchical Memory flow."""
        print_header("Test 3: Hierarchical Memory Flow")
        
        try:
            from services.agent_builder.hierarchical_memory import (
                HierarchicalMemory,
                MemoryType,
                MemoryImportance
            )
            
            # Initialize
            memory = HierarchicalMemory(self.mock_db)
            print_success("HierarchicalMemory initialized")
            
            # Store short-term memory
            mem1 = await memory.store(
                agent_id="test_agent_001",
                content="User prefers concise answers",
                memory_type=MemoryType.SHORT_TERM,
                session_id="session_001",
                importance=MemoryImportance.HIGH,
                tags=["preference", "style"]
            )
            print_success(f"Short-term memory stored: {mem1.memory_id}")
            
            # Store semantic memory
            mem2 = await memory.store(
                agent_id="test_agent_001",
                content="Python is a programming language",
                memory_type=MemoryType.SEMANTIC,
                importance=MemoryImportance.MEDIUM,
                tags=["knowledge", "programming"]
            )
            print_success(f"Semantic memory stored: {mem2.memory_id}")
            
            # Store episodic memory
            mem3 = await memory.store(
                agent_id="test_agent_001",
                content="Discussed project requirements on 2025-10-26",
                memory_type=MemoryType.EPISODIC,
                importance=MemoryImportance.HIGH,
                metadata={"date": "2025-10-26", "topic": "requirements"}
            )
            print_success(f"Episodic memory stored: {mem3.memory_id}")
            
            # Retrieve memories
            relevant = await memory.retrieve(
                agent_id="test_agent_001",
                query="user preferences",
                memory_types=[MemoryType.SHORT_TERM, MemoryType.SEMANTIC],
                top_k=5
            )
            print_success(f"Retrieved {len(relevant)} relevant memories")
            
            # Get memory stats
            stats = memory.get_memory_stats(
                agent_id="test_agent_001",
                session_id="session_001"
            )
            print_success(f"Short-term: {stats['short_term_count']}")
            print_success(f"Long-term: {stats['long_term_count']}")
            print_success(f"Episodic: {stats['episodic_count']}")
            print_success(f"Semantic: {stats['semantic_count']}")
            print_success(f"Total: {stats['total_count']}")
            
            # Test consolidation
            await memory.consolidate_memory(
                agent_id="test_agent_001",
                session_id="session_001"
            )
            print_success("Memory consolidated")
            
            # Test context compression
            long_context = "This is a very long context " * 100
            compressed = await memory.compress_context(
                context=long_context,
                max_length=500
            )
            print_success(f"Context compressed: {len(long_context)} → {len(compressed)} chars")
            
            return True
            
        except Exception as e:
            print_error(f"Hierarchical Memory test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_prompt_optimizer_flow(self) -> bool:
        """Test complete Prompt Optimizer flow."""
        print_header("Test 4: Prompt Optimizer Flow")
        
        try:
            from services.agent_builder.prompt_optimizer import (
                AutoPromptOptimizer,
                OptimizationStrategy
            )
            
            # Initialize
            optimizer = AutoPromptOptimizer(self.mock_db)
            print_success("AutoPromptOptimizer initialized")
            
            # Optimize prompt
            current_prompt = "You are a helpful assistant. Answer questions."
            performance_data = {
                "success_rate": 0.75,
                "avg_duration_ms": 6000,
                "avg_token_count": 3500,
                "avg_feedback_rating": 2.8,
                "common_errors": ["timeout", "incomplete_response"]
            }
            
            optimized = await optimizer.optimize_prompt(
                agent_id="test_agent_001",
                current_prompt=current_prompt,
                performance_data=performance_data,
                strategy=OptimizationStrategy.HYBRID
            )
            print_success(f"Prompt optimized ({len(optimized)} chars)")
            
            # Run A/B test
            variants = [
                "You are a helpful assistant. Provide clear answers.",
                "You are an expert assistant. Give detailed responses.",
                "You are a friendly assistant. Answer conversationally."
            ]
            
            test = await optimizer.run_ab_test(
                agent_id="test_agent_001",
                prompt_variants=variants,
                test_duration_hours=24,
                min_samples=100
            )
            print_success(f"A/B test started: {test['test_id']}")
            print_success(f"Testing {test['variants']} variants")
            
            # Track prompt performance
            await optimizer.track_prompt_performance(
                agent_id="test_agent_001",
                version_id="v1",
                execution_result={
                    "success": True,
                    "duration_ms": 2000,
                    "token_count": 500,
                    "feedback_rating": 4.5
                }
            )
            print_success("Performance tracked")
            
            # Get best version
            best = await optimizer.get_best_prompt_version(
                agent_id="test_agent_001",
                min_executions=1
            )
            if best:
                print_success(f"Best version: {best.version_id}")
                print_success(f"Performance score: {best.performance_score:.3f}")
            else:
                print_info("No qualified versions yet")
            
            return True
            
        except Exception as e:
            print_error(f"Prompt Optimizer test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_api_integrator_flow(self) -> bool:
        """Test complete API Integrator flow."""
        print_header("Test 5: API Integrator Flow")
        
        try:
            from services.agent_builder.api_integrator import (
                AutoAPIIntegrator,
                APIEndpoint,
                HTTPMethod,
                APIAuthType
            )
            
            # Initialize
            integrator = AutoAPIIntegrator(self.mock_db)
            print_success("AutoAPIIntegrator initialized")
            
            # Create API endpoint
            endpoint = APIEndpoint(
                path="/api/users/{user_id}",
                method=HTTPMethod.GET,
                operation_id="getUser",
                summary="Get user by ID",
                description="Retrieves a user by their ID",
                parameters=[
                    {"name": "user_id", "in": "path", "required": True, "type": "string"}
                ],
                tags=["users"]
            )
            print_success(f"Endpoint created: {endpoint.method.value} {endpoint.path}")
            
            # Generate tool from endpoint
            tool = integrator._generate_tool_from_endpoint(
                endpoint=endpoint,
                base_url="https://api.example.com",
                auth_config={
                    "type": APIAuthType.API_KEY,
                    "key_name": "X-API-Key",
                    "key_value": "test-key-123"
                }
            )
            print_success(f"Tool generated: {tool.name}")
            print_success(f"Tool ID: {tool.tool_id}")
            
            # Test auth header building
            headers = integrator._build_auth_headers({
                "type": APIAuthType.BEARER_TOKEN,
                "token": "test-token-123"
            })
            assert "Authorization" in headers
            print_success(f"Auth headers built: {list(headers.keys())}")
            
            # Close integrator
            await integrator.close()
            print_success("Integrator closed")
            
            return True
            
        except Exception as e:
            print_error(f"API Integrator test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_integration_scenario(self) -> bool:
        """Test integrated scenario using multiple features."""
        print_header("Test 6: Integration Scenario")
        
        try:
            from services.agent_builder.human_in_loop import HumanInTheLoop, ApprovalPriority
            from services.agent_builder.cost_optimizer import CostOptimizer
            from services.agent_builder.hierarchical_memory import (
                HierarchicalMemory,
                MemoryType,
                MemoryImportance
            )
            
            print_info("Scenario: Agent execution with approval, cost tracking, and memory")
            
            # Step 1: Request approval
            hitl = HumanInTheLoop(self.mock_db)
            approval = await hitl.request_approval(
                agent_id="prod_agent_001",
                execution_id="exec_integration_001",
                action="Execute high-cost agent",
                context={"estimated_cost": 0.05},
                requester_id="user_001",
                approver_ids=["manager_001"],
                priority=ApprovalPriority.MEDIUM
            )
            print_success("Step 1: Approval requested")
            
            # Step 2: Approve
            await hitl.approve(
                request_id=approval.request_id,
                approver_id="manager_001"
            )
            print_success("Step 2: Approved")
            
            # Step 3: Optimize cost
            optimizer = CostOptimizer(self.mock_db)
            recommendation = await optimizer.optimize_for_cost(
                task="Complex analysis task",
                budget_usd=0.05,
                quality_threshold=0.8
            )
            print_success(f"Step 3: Model selected - {recommendation['recommended_model']}")
            
            # Step 4: Track execution
            await optimizer.track_execution(
                agent_id="prod_agent_001",
                model=recommendation['recommended_model'],
                prompt_tokens=1000,
                completion_tokens=500,
                cached=False
            )
            print_success("Step 4: Execution tracked")
            
            # Step 5: Store memory
            memory = HierarchicalMemory(self.mock_db)
            await memory.store(
                agent_id="prod_agent_001",
                content="Successfully executed complex analysis",
                memory_type=MemoryType.EPISODIC,
                importance=MemoryImportance.HIGH,
                metadata={
                    "execution_id": "exec_integration_001",
                    "cost": recommendation['estimated_cost_usd'],
                    "model": recommendation['recommended_model']
                }
            )
            print_success("Step 5: Memory stored")
            
            # Step 6: Get reports
            cost_report = optimizer.get_cost_report(agent_id="prod_agent_001")
            memory_stats = memory.get_memory_stats(agent_id="prod_agent_001")
            
            print_success(f"Step 6: Reports generated")
            print_info(f"  Total cost: ${cost_report['total_cost_usd']:.4f}")
            print_info(f"  Total memories: {memory_stats['total_count']}")
            
            return True
            
        except Exception as e:
            print_error(f"Integration scenario failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_all_tests(self):
        """Run all E2E tests."""
        print_header("AGENT BUILDER E2E TESTS")
        
        await self.setup()
        
        tests = [
            ("Human-in-the-Loop Flow", self.test_human_in_loop_flow),
            ("Cost Optimizer Flow", self.test_cost_optimizer_flow),
            ("Hierarchical Memory Flow", self.test_hierarchical_memory_flow),
            ("Prompt Optimizer Flow", self.test_prompt_optimizer_flow),
            ("API Integrator Flow", self.test_api_integrator_flow),
            ("Integration Scenario", self.test_integration_scenario),
        ]
        
        for name, test_func in tests:
            result = await test_func()
            self.results.append((name, result))
        
        # Summary
        print_header("TEST SUMMARY")
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        
        for name, result in self.results:
            if result:
                print_success(f"{name}")
            else:
                print_error(f"{name}")
        
        print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
        
        if passed == total:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.RESET}\n")
            return True
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.RESET}\n")
            return False


async def main():
    """Main entry point."""
    test_suite = AgentBuilderE2ETest()
    success = await test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
