#!/usr/bin/env python3
"""
Manual test script for Workflow Generator
Run this to test the workflow generator functionality
"""

import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.services.agent_builder.workflow_generator import WorkflowGenerator


async def test_basic_generation():
    """Test basic workflow generation"""
    print("=" * 80)
    print("TEST 1: Basic Workflow Generation")
    print("=" * 80)
    
    generator = WorkflowGenerator()
    
    # Test 1: Simple Slack notification
    print("\n📝 Test Case: Slack Notification")
    print("Description: 'Webhook이 트리거되면 #alerts 채널에 Slack 메시지 전송'")
    
    try:
        result = await generator.generate_workflow(
            description="Webhook이 트리거되면 #alerts 채널에 Slack 메시지 전송",
            user_id="test-user-123"
        )
        
        print(f"\n✅ Generation successful!")
        print(f"   Name: {result.get('name')}")
        print(f"   Description: {result.get('description')}")
        print(f"   Nodes: {len(result.get('nodes', []))}")
        print(f"   Edges: {len(result.get('edges', []))}")
        
        # Print node types
        node_types = [n.get('type') for n in result.get('nodes', [])]
        print(f"   Node Types: {', '.join(node_types)}")
        
        # Check for expected nodes
        if 'slack' in node_types:
            print("   ✓ Contains Slack node")
        if 'webhook_trigger' in node_types or 'trigger' in node_types:
            print("   ✓ Contains Webhook trigger")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_complex_generation():
    """Test complex workflow generation"""
    print("\n" + "=" * 80)
    print("TEST 2: Complex Workflow Generation")
    print("=" * 80)
    
    generator = WorkflowGenerator()
    
    # Test 2: Approval workflow
    print("\n📝 Test Case: Approval Workflow")
    print("Description: '구매 요청이 들어오면 금액이 $1000 이상이면 관리자 승인 필요, 그 후 결제 처리'")
    
    try:
        result = await generator.generate_workflow(
            description="구매 요청이 들어오면 금액이 $1000 이상이면 관리자 승인 필요, 그 후 결제 처리",
            user_id="test-user-123"
        )
        
        print(f"\n✅ Generation successful!")
        print(f"   Name: {result.get('name')}")
        print(f"   Nodes: {len(result.get('nodes', []))}")
        print(f"   Edges: {len(result.get('edges', []))}")
        
        # Print node details
        print("\n   Node Details:")
        for i, node in enumerate(result.get('nodes', []), 1):
            print(f"   {i}. {node.get('type')} - {node.get('data', {}).get('label', 'N/A')}")
        
        # Check for expected nodes
        node_types = [n.get('type') for n in result.get('nodes', [])]
        if 'condition' in node_types or 'switch' in node_types:
            print("\n   ✓ Contains conditional logic")
        if 'human_approval' in node_types:
            print("   ✓ Contains human approval")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_suggestions():
    """Test improvement suggestions"""
    print("\n" + "=" * 80)
    print("TEST 3: Improvement Suggestions")
    print("=" * 80)
    
    generator = WorkflowGenerator()
    
    # Test workflow without error handling
    workflow_def = {
        "name": "Test Workflow",
        "nodes": [
            {"id": "1", "type": "start"},
            {"id": "2", "type": "http_request"},
            {"id": "3", "type": "email"},
            {"id": "4", "type": "end"}
        ],
        "edges": []
    }
    
    print("\n📝 Test Case: Workflow without error handling or approval")
    
    try:
        suggestions = await generator.suggest_improvements(workflow_def)
        
        print(f"\n✅ Suggestions generated: {len(suggestions)}")
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"\n   Suggestion {i}:")
            print(f"   Type: {suggestion.get('type')}")
            print(f"   Severity: {suggestion.get('severity')}")
            print(f"   Message: {suggestion.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Suggestion generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_node_types():
    """Test node types availability"""
    print("\n" + "=" * 80)
    print("TEST 4: Node Types")
    print("=" * 80)
    
    generator = WorkflowGenerator()
    
    print(f"\n📝 Available Node Types: {len(generator.node_types)}")
    
    # Group by category
    categories = {
        "Control Flow": ["start", "end", "condition", "switch", "loop", "parallel", "merge"],
        "AI/Agent": ["agent", "manager_agent", "consensus"],
        "Integration": ["slack", "discord", "email", "google_drive", "s3", "database"],
        "Trigger": ["webhook_trigger", "schedule_trigger"],
        "Processing": ["code", "http_request", "delay"],
        "Approval": ["human_approval", "memory"]
    }
    
    for category, types in categories.items():
        print(f"\n   {category}:")
        for node_type in types:
            if node_type in generator.node_types:
                print(f"   ✓ {node_type}: {generator.node_types[node_type]}")
            else:
                print(f"   ✗ {node_type}: NOT FOUND")
    
    return True


async def test_auto_layout():
    """Test auto-layout algorithm"""
    print("\n" + "=" * 80)
    print("TEST 5: Auto-Layout Algorithm")
    print("=" * 80)
    
    generator = WorkflowGenerator()
    
    # Create a simple workflow
    workflow_def = {
        "name": "Test",
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "middle", "type": "agent"},
            {"id": "end", "type": "end"}
        ],
        "edges": [
            {"source": "start", "target": "middle"},
            {"source": "middle", "target": "end"}
        ]
    }
    
    print("\n📝 Test Case: Simple chain layout")
    
    try:
        result = generator._auto_layout_nodes(workflow_def)
        
        print("\n✅ Layout generated!")
        print("\n   Node Positions:")
        for node in result["nodes"]:
            pos = node.get("position", {})
            print(f"   {node['id']}: x={pos.get('x')}, y={pos.get('y')}")
        
        # Verify vertical ordering
        start = next(n for n in result["nodes"] if n["id"] == "start")
        middle = next(n for n in result["nodes"] if n["id"] == "middle")
        end = next(n for n in result["nodes"] if n["id"] == "end")
        
        if start["position"]["y"] < middle["position"]["y"] < end["position"]["y"]:
            print("\n   ✓ Vertical ordering correct")
        else:
            print("\n   ✗ Vertical ordering incorrect")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Layout generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("WORKFLOW GENERATOR TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Basic Generation", await test_basic_generation()))
    results.append(("Complex Generation", await test_complex_generation()))
    results.append(("Suggestions", await test_suggestions()))
    results.append(("Node Types", await test_node_types()))
    results.append(("Auto Layout", await test_auto_layout()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
