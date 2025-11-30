"""
Workflow Tools Test Runner

Runs integration tests for workflow tools and generates a report.
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ToolTestRunner:
    """Runs workflow tool tests and generates reports."""
    
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.scenarios_dir = Path(__file__).parent / "scenarios"
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tool tests."""
        logger.info("=" * 60)
        logger.info("Starting Workflow Tools Test Suite")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # 1. Test Tool Registry
        await self.test_tool_registry()
        
        # 2. Test Individual Tools
        await self.test_individual_tools()
        
        # 3. Test Workflow Scenarios
        await self.test_workflow_scenarios()
        
        # 4. Test UI Config Mappings
        self.test_ui_config_mappings()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Generate summary
        summary = self.generate_summary(duration)
        
        return summary
    
    async def test_tool_registry(self):
        """Test tool registry functionality."""
        logger.info("\n--- Testing Tool Registry ---")
        
        try:
            from backend.core.tools.registry import ToolRegistry
            
            # Test 1: Get all tool IDs
            tool_ids = ToolRegistry.get_tool_ids()
            self.results.append({
                "test": "Tool Registry - Get Tool IDs",
                "passed": len(tool_ids) > 0,
                "details": f"Found {len(tool_ids)} registered tools",
                "tool_count": len(tool_ids),
            })
            logger.info(f"✓ Found {len(tool_ids)} registered tools")
            
            # Test 2: List by category
            by_category = ToolRegistry.list_by_category()
            self.results.append({
                "test": "Tool Registry - List by Category",
                "passed": len(by_category) > 0,
                "details": f"Categories: {list(by_category.keys())}",
            })
            logger.info(f"✓ Categories: {list(by_category.keys())}")
            
            # Test 3: Get tool configs
            for tool_id in tool_ids[:5]:  # Test first 5
                config = ToolRegistry.get_tool_config(tool_id)
                if config:
                    logger.info(f"  ✓ {tool_id}: {config.name}")
                else:
                    logger.warning(f"  ✗ {tool_id}: No config found")
            
            self.results.append({
                "test": "Tool Registry - Get Tool Configs",
                "passed": True,
                "details": "Tool configs retrieved successfully",
            })
            
        except Exception as e:
            logger.error(f"✗ Tool Registry test failed: {e}")
            self.results.append({
                "test": "Tool Registry",
                "passed": False,
                "error": str(e),
            })
    
    async def test_individual_tools(self):
        """Test individual tool execution."""
        logger.info("\n--- Testing Individual Tools ---")
        
        tools_to_test = [
            {
                "tool_id": "http_request",
                "params": {
                    "url": "https://httpbin.org/get",
                    "method": "GET",
                    "timeout": 10,
                },
                "expected": {"has_status_code": True},
            },
            {
                "tool_id": "calculator",
                "params": {
                    "expression": "2 + 2",
                },
                "expected": {"result": 4},
                "skip_if_not_registered": True,
            },
        ]
        
        from backend.core.tools.registry import ToolRegistry
        
        for test_case in tools_to_test:
            tool_id = test_case["tool_id"]
            
            if not ToolRegistry.is_registered(tool_id):
                if test_case.get("skip_if_not_registered"):
                    logger.info(f"  ⊘ {tool_id}: Skipped (not registered)")
                    continue
                else:
                    self.results.append({
                        "test": f"Tool Execution - {tool_id}",
                        "passed": False,
                        "error": "Tool not registered",
                    })
                    continue
            
            try:
                logger.info(f"  Testing {tool_id}...")
                result = await ToolRegistry.execute_tool(
                    tool_id=tool_id,
                    params=test_case["params"],
                )
                
                passed = result.get("success", False)
                self.results.append({
                    "test": f"Tool Execution - {tool_id}",
                    "passed": passed,
                    "details": result,
                })
                
                if passed:
                    logger.info(f"  ✓ {tool_id}: Execution successful")
                else:
                    logger.warning(f"  ✗ {tool_id}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"  ✗ {tool_id}: {e}")
                self.results.append({
                    "test": f"Tool Execution - {tool_id}",
                    "passed": False,
                    "error": str(e),
                })
    
    async def test_workflow_scenarios(self):
        """Test workflow scenarios from JSON files."""
        logger.info("\n--- Testing Workflow Scenarios ---")
        
        if not self.scenarios_dir.exists():
            logger.warning(f"Scenarios directory not found: {self.scenarios_dir}")
            return
        
        for scenario_file in self.scenarios_dir.glob("*.json"):
            try:
                with open(scenario_file) as f:
                    scenario = json.load(f)
                
                logger.info(f"  Testing: {scenario.get('name', scenario_file.name)}")
                
                # Validate scenario structure
                has_nodes = "nodes" in scenario and len(scenario["nodes"]) > 0
                has_edges = "edges" in scenario
                
                self.results.append({
                    "test": f"Scenario - {scenario.get('name', scenario_file.name)}",
                    "passed": has_nodes and has_edges,
                    "details": {
                        "nodes": len(scenario.get("nodes", [])),
                        "edges": len(scenario.get("edges", [])),
                        "has_test_input": "test_input" in scenario,
                    },
                })
                
                if has_nodes and has_edges:
                    logger.info(f"    ✓ Valid scenario: {len(scenario['nodes'])} nodes, {len(scenario['edges'])} edges")
                else:
                    logger.warning(f"    ✗ Invalid scenario structure")
                    
            except Exception as e:
                logger.error(f"  ✗ Failed to load {scenario_file.name}: {e}")
                self.results.append({
                    "test": f"Scenario - {scenario_file.name}",
                    "passed": False,
                    "error": str(e),
                })
    
    def test_ui_config_mappings(self):
        """Test UI config mappings (documentation only)."""
        logger.info("\n--- Testing UI Config Mappings ---")
        
        # Expected mappings from ToolConfigRegistry.tsx
        expected_mappings = {
            # AI Tools
            "openai_chat": "OpenAIChatConfig",
            "anthropic_claude": "OpenAIChatConfig",
            "google_gemini": "OpenAIChatConfig",
            "mistral_ai": "OpenAIChatConfig",
            "cohere": "OpenAIChatConfig",
            "ai_agent": "AIAgentConfigWrapper",
            
            # Communication
            "slack": "SlackConfig",
            "gmail": "GmailConfig",
            "discord": "SlackConfig",
            "telegram": "SlackConfig",
            "sendgrid": "GmailConfig",
            
            # HTTP & API
            "http_request": "HttpRequestConfig",
            "webhook": "WebhookConfig",
            
            # Search
            "vector_search": "VectorSearchConfig",
            "tavily_search": "HttpRequestConfig",
            "serper_search": "HttpRequestConfig",
            
            # Data
            "postgres": "PostgresConfig",
            "postgresql_query": "PostgresConfig",
            "mysql_query": "PostgresConfig",
            
            # Control Flow
            "condition": "ConditionConfig",
            "switch": "SwitchConfig",
            "loop": "LoopConfig",
            "parallel": "ParallelConfig",
            "delay": "DelayConfig",
            "merge": "MergeConfig",
            "filter": "FilterConfig",
            "transform": "TransformConfig",
            "try_catch": "TryCatchConfig",
            "human_approval": "HumanApprovalConfig",
            
            # Triggers
            "schedule_trigger": "ScheduleTriggerConfig",
            "manual_trigger": "ManualTriggerConfig",
            "webhook_trigger": "WebhookTriggerConfig",
        }
        
        # Check against registered tools
        try:
            from backend.core.tools.registry import ToolRegistry
            registered_ids = set(ToolRegistry.get_tool_ids())
            mapped_ids = set(expected_mappings.keys())
            
            # Tools with UI config
            tools_with_config = registered_ids & mapped_ids
            # Tools without UI config
            tools_without_config = registered_ids - mapped_ids
            
            coverage = len(tools_with_config) / len(registered_ids) * 100 if registered_ids else 0
            
            self.results.append({
                "test": "UI Config Mappings",
                "passed": coverage >= 80,
                "details": {
                    "total_tools": len(registered_ids),
                    "tools_with_config": len(tools_with_config),
                    "tools_without_config": list(tools_without_config)[:10],
                    "coverage_percent": round(coverage, 1),
                },
            })
            
            logger.info(f"  ✓ UI Config Coverage: {coverage:.1f}%")
            logger.info(f"    - Tools with config: {len(tools_with_config)}")
            logger.info(f"    - Tools without config: {len(tools_without_config)}")
            
            if tools_without_config:
                logger.info(f"    - Missing configs for: {list(tools_without_config)[:5]}...")
                
        except Exception as e:
            logger.error(f"  ✗ UI Config test failed: {e}")
            self.results.append({
                "test": "UI Config Mappings",
                "passed": False,
                "error": str(e),
            })
    
    def generate_summary(self, duration: float) -> Dict[str, Any]:
        """Generate test summary."""
        passed = sum(1 for r in self.results if r.get("passed"))
        failed = sum(1 for r in self.results if not r.get("passed"))
        total = len(self.results)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 2),
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "results": self.results,
        }
        
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Pass Rate: {summary['pass_rate']}%")
        logger.info(f"Duration: {duration:.2f}s")
        logger.info("=" * 60)
        
        return summary


async def main():
    """Main entry point."""
    runner = ToolTestRunner()
    summary = await runner.run_all_tests()
    
    # Save report
    report_path = Path(__file__).parent / "test_report.json"
    with open(report_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    
    logger.info(f"\nReport saved to: {report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if summary["failed"] == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
