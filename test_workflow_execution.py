"""Test workflow execution endpoint."""
import requests
import json

# Configuration
API_URL = "http://localhost:8000"
TOKEN = None  # You need to get this from login

def test_workflow_execution():
    """Test workflow execution."""
    
    # First, we need to login to get a token
    print("⚠️  You need to provide a valid authentication token")
    print("Steps:")
    print("1. Login to the frontend")
    print("2. Open browser DevTools > Application > Local Storage")
    print("3. Copy the 'token' value")
    print("4. Set TOKEN variable in this script")
    print()
    
    if not TOKEN:
        print("❌ TOKEN not set. Please set TOKEN variable and run again.")
        return
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Get list of workflows
    print("📋 Fetching workflows...")
    response = requests.get(f"{API_URL}/api/agent-builder/workflows", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get workflows: {response.status_code}")
        print(response.text)
        return
    
    workflows = response.json().get("workflows", [])
    print(f"✅ Found {len(workflows)} workflows")
    
    if not workflows:
        print("⚠️  No workflows found. Please create a workflow first.")
        return
    
    # Execute first workflow
    workflow_id = workflows[0]["id"]
    workflow_name = workflows[0]["name"]
    print(f"\n🚀 Executing workflow: {workflow_name} ({workflow_id})")
    
    response = requests.post(
        f"{API_URL}/api/agent-builder/workflows/{workflow_id}/execute",
        headers=headers,
        json={"test": True}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ Workflow executed successfully!")
        execution_id = response.json().get("execution_id")
        print(f"Execution ID: {execution_id}")
    else:
        print(f"\n❌ Workflow execution failed!")

if __name__ == "__main__":
    test_workflow_execution()
