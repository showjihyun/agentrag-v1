"""
Quick test script for Tool Execution API.
Run this after starting the backend server.
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/agent-builder/tool-execution"

def test_available_tools():
    """Test getting available tools."""
    print("\n" + "="*60)
    print("Testing: Get Available Tools")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/available-tools")
        
        if response.status_code == 200:
            tools = response.json()
            print(f"✅ Success! Found {sum(len(v) for v in tools.values())} tools")
            print(f"\nCategories: {list(tools.keys())}")
            for category, tool_list in tools.items():
                print(f"\n{category.upper()}:")
                for tool in tool_list:
                    print(f"  - {tool}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_duckduckgo_search():
    """Test DuckDuckGo search."""
    print("\n" + "="*60)
    print("Testing: DuckDuckGo Search")
    print("="*60)
    
    payload = {
        "tool_name": "duckduckgo_search",
        "parameters": {
            "query": "Python programming",
            "max_results": 3
        },
        "config": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"Execution time: {result.get('execution_time', 0):.3f}s")
            if result.get('success'):
                output = result.get('result', {})
                results = output.get('results', [])
                print(f"Found {len(results)} results:")
                for i, r in enumerate(results[:3], 1):
                    print(f"\n{i}. {r.get('title', 'N/A')}")
                    print(f"   {r.get('url', 'N/A')}")
            else:
                print(f"❌ Tool execution failed: {result.get('error')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_http_request():
    """Test HTTP request."""
    print("\n" + "="*60)
    print("Testing: HTTP Request")
    print("="*60)
    
    payload = {
        "tool_name": "http_request",
        "parameters": {
            "method": "GET",
            "url": "https://api.github.com/repos/python/cpython"
        },
        "config": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success!")
            print(f"Execution time: {result.get('execution_time', 0):.3f}s")
            if result.get('success'):
                output = result.get('result', {})
                print(f"Status: {output.get('status_code')}")
                body = output.get('body', {})
                if isinstance(body, dict):
                    print(f"Repo: {body.get('full_name')}")
                    print(f"Stars: {body.get('stargazers_count')}")
                    print(f"Description: {body.get('description', 'N/A')[:100]}")
            else:
                print(f"❌ Tool execution failed: {result.get('error')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


def test_validate():
    """Test validation."""
    print("\n" + "="*60)
    print("Testing: Validate Tool Config")
    print("="*60)
    
    payload = {
        "tool_name": "duckduckgo_search",
        "parameters": {
            "query": "test"
        },
        "config": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/validate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('valid'):
                print(f"✅ Valid configuration")
            else:
                print(f"❌ Invalid: {result.get('message')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Tool Execution API Test")
    print("="*60)
    print("\nMake sure the backend server is running:")
    print("  cd backend")
    print("  uvicorn main:app --reload --port 8000")
    print("\nPress Enter to start tests...")
    input()
    
    # Run tests
    test_available_tools()
    test_validate()
    test_duckduckgo_search()
    test_http_request()
    
    print("\n" + "="*60)
    print("Tests Complete!")
    print("="*60)
