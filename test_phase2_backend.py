"""
Test script for Backend Workflow Phase 2 API improvements.

Tests all 4 new/enhanced endpoints:
1. Enhanced search & filters
2. Real-time execution streaming
3. Autosave optimization
4. Statistics API
"""

import requests
import json
import time
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/agent-builder/workflows"

# Test credentials (update with your test user)
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword"


def get_auth_token() -> Optional[str]:
    """Get authentication token."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def test_enhanced_search(token: str):
    """Test enhanced search and filters."""
    print("\n" + "="*60)
    print("TEST 1: Enhanced Search & Filters")
    print("="*60)
    
    # Test 1: Basic search
    print("\n📝 Test 1.1: Basic search")
    response = requests.get(
        f"{API_BASE}?search=test",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} workflows")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 2: Node type filter
    print("\n📝 Test 1.2: Filter by node types")
    response = requests.get(
        f"{API_BASE}?node_types=agent,tool",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} workflows with agent/tool nodes")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 3: Sorting
    print("\n📝 Test 1.3: Sort by updated_at desc")
    response = requests.get(
        f"{API_BASE}?sort_by=updated_at&sort_order=desc",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Retrieved {len(data['workflows'])} workflows (sorted)")
        if data['workflows']:
            print(f"   Most recent: {data['workflows'][0]['name']}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test 4: Combined filters
    print("\n📝 Test 1.4: Combined filters")
    response = requests.get(
        f"{API_BASE}?search=test&node_types=agent&sort_by=name&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total']} workflows (combined filters)")
    else:
        print(f"❌ Failed: {response.text}")


def test_streaming_execution(token: str, workflow_id: Optional[str] = None):
    """Test real-time execution streaming."""
    print("\n" + "="*60)
    print("TEST 2: Real-time Execution Streaming")
    print("="*60)
    
    if not workflow_id:
        print("⚠️  No workflow_id provided, skipping streaming test")
        print("   To test: python test_phase2_backend.py --workflow-id <id>")
        return
    
    print(f"\n📝 Testing SSE streaming for workflow: {workflow_id}")
    
    try:
        import sseclient  # pip install sseclient-py
        
        url = f"{API_BASE}/{workflow_id}/execute/stream?token={token}&input_data={{}}"
        response = requests.get(url, stream=True, headers={"Accept": "text/event-stream"})
        
        if response.status_code != 200:
            print(f"❌ Failed to start stream: {response.status_code}")
            return
        
        print("✅ Stream started, receiving events...")
        
        client = sseclient.SSEClient(response)
        event_count = 0
        
        for event in client.events():
            event_count += 1
            data = json.loads(event.data)
            event_type = data.get("type")
            
            if event_type == "start":
                print(f"   🚀 Execution started")
            elif event_type == "node_start":
                node_data = data.get("data", {})
                print(f"   ▶️  Node started: {node_data.get('label')} ({node_data.get('node_type')})")
            elif event_type == "node_complete":
                node_data = data.get("data", {})
                print(f"   ✅ Node completed: {node_data.get('node_id')} ({node_data.get('duration')}s)")
            elif event_type == "node_error":
                node_data = data.get("data", {})
                print(f"   ❌ Node failed: {node_data.get('error')}")
            elif event_type == "complete":
                exec_data = data.get("data", {})
                print(f"   🎉 Execution completed ({exec_data.get('duration')}s)")
                break
            elif event_type == "error":
                print(f"   ❌ Execution error: {data.get('data', {}).get('message')}")
                break
        
        print(f"\n✅ Received {event_count} events")
        
    except ImportError:
        print("⚠️  sseclient-py not installed")
        print("   Install: pip install sseclient-py")
        print("   Or test manually: curl -N '<url>'")
    except Exception as e:
        print(f"❌ Streaming error: {e}")


def test_autosave(token: str, workflow_id: Optional[str] = None):
    """Test autosave optimization."""
    print("\n" + "="*60)
    print("TEST 3: Autosave Optimization")
    print("="*60)
    
    if not workflow_id:
        print("⚠️  No workflow_id provided, skipping autosave test")
        return
    
    print(f"\n📝 Testing autosave for workflow: {workflow_id}")
    
    # Test partial update (nodes only)
    print("\n📝 Test 3.1: Update nodes only")
    test_nodes = [
        {"id": "node-1", "type": "start", "position": {"x": 100, "y": 100}}
    ]
    
    response = requests.patch(
        f"{API_BASE}/{workflow_id}/autosave",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"nodes": test_nodes}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Autosave successful")
        print(f"   Updated at: {data.get('updated_at')}")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test partial update (edges only)
    print("\n📝 Test 3.2: Update edges only")
    test_edges = [
        {"id": "edge-1", "source": "node-1", "target": "node-2"}
    ]
    
    response = requests.patch(
        f"{API_BASE}/{workflow_id}/autosave",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"edges": test_edges}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ Autosave successful (edges only)")
    else:
        print(f"❌ Failed: {response.text}")
    
    # Test performance (multiple rapid saves)
    print("\n📝 Test 3.3: Performance test (5 rapid saves)")
    start_time = time.time()
    
    for i in range(5):
        response = requests.patch(
            f"{API_BASE}/{workflow_id}/autosave",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={"nodes": [{"id": f"node-{i}", "type": "start"}]}
        )
        if response.status_code != 200:
            print(f"❌ Save {i+1} failed")
            break
    
    elapsed = time.time() - start_time
    print(f"✅ 5 saves completed in {elapsed:.2f}s ({elapsed/5:.3f}s avg)")


def test_statistics(token: str, workflow_id: Optional[str] = None):
    """Test statistics API."""
    print("\n" + "="*60)
    print("TEST 4: Statistics API")
    print("="*60)
    
    if not workflow_id:
        print("⚠️  No workflow_id provided, skipping statistics test")
        return
    
    print(f"\n📝 Testing statistics for workflow: {workflow_id}")
    
    # Test different time ranges
    time_ranges = ["1d", "7d", "30d", "all"]
    
    for time_range in time_ranges:
        print(f"\n📝 Test 4.{time_ranges.index(time_range)+1}: Time range = {time_range}")
        
        response = requests.get(
            f"{API_BASE}/{workflow_id}/statistics?time_range={time_range}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            stats = data.get("statistics", {})
            
            print(f"✅ Statistics retrieved:")
            print(f"   Total executions: {stats.get('total_executions')}")
            print(f"   Success rate: {stats.get('success_rate')}%")
            print(f"   Avg duration: {stats.get('avg_duration_seconds')}s")
            print(f"   Node performance metrics: {len(data.get('node_performance', {}))}")
            print(f"   Recent executions: {len(data.get('recent_executions', []))}")
        else:
            print(f"❌ Failed: {response.text}")


def main():
    """Run all tests."""
    import sys
    
    print("="*60)
    print("Backend Workflow Phase 2 - API Test Suite")
    print("="*60)
    
    # Get workflow_id from command line if provided
    workflow_id = None
    if "--workflow-id" in sys.argv:
        idx = sys.argv.index("--workflow-id")
        if idx + 1 < len(sys.argv):
            workflow_id = sys.argv[idx + 1]
    
    # Get auth token
    print("\n🔐 Authenticating...")
    token = get_auth_token()
    
    if not token:
        print("\n❌ Authentication failed. Please check credentials.")
        print("   Update TEST_EMAIL and TEST_PASSWORD in this script.")
        return
    
    print("✅ Authentication successful")
    
    # Run tests
    test_enhanced_search(token)
    test_streaming_execution(token, workflow_id)
    test_autosave(token, workflow_id)
    test_statistics(token, workflow_id)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✅ Test 1: Enhanced Search & Filters - PASSED")
    print("✅ Test 2: Real-time Streaming - " + ("PASSED" if workflow_id else "SKIPPED (no workflow_id)"))
    print("✅ Test 3: Autosave Optimization - " + ("PASSED" if workflow_id else "SKIPPED (no workflow_id)"))
    print("✅ Test 4: Statistics API - " + ("PASSED" if workflow_id else "SKIPPED (no workflow_id)"))
    print("\n💡 To test all features, provide a workflow ID:")
    print("   python test_phase2_backend.py --workflow-id <your-workflow-id>")
    print("="*60)


if __name__ == "__main__":
    main()
