"""Test tools API to check if python_code is visible."""
import requests

# Test tools API
response = requests.get('http://localhost:8000/api/agent-builder/tools')

if response.status_code == 200:
    data = response.json()
    tools = data.get('tools', [])
    
    print(f"Total tools: {len(tools)}")
    print(f"\nCategories: {data.get('categories', [])}")
    
    # Check for Python Code tool
    print("\n=== Code Category Tools ===")
    code_tools = [t for t in tools if t.get('category') == 'code']
    for tool in code_tools:
        print(f"  {tool['id']} | {tool['name']}")
    
    # Check for HTTP Request tool
    print("\n=== Developer Category Tools ===")
    dev_tools = [t for t in tools if t.get('category') == 'developer']
    for tool in dev_tools:
        print(f"  {tool['id']} | {tool['name']}")
    
    # Check if python_code exists
    python_code = next((t for t in tools if t['id'] == 'python_code'), None)
    if python_code:
        print(f"\n✅ python_code found!")
        print(f"   Name: {python_code['name']}")
        print(f"   Category: {python_code['category']}")
        print(f"   Description: {python_code['description']}")
    else:
        print("\n❌ python_code NOT found in API response")
        
else:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
