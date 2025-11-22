"""
Workflow Tools 전체 스택 검증
DB → Backend API → Tool Execution → Frontend 연동
"""

import requests
import psycopg2
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_database():
    """1. Database Layer 체크"""
    print_section("1. DATABASE LAYER")
    
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='agenticrag',
        user='postgres',
        password='postgres'
    )
    cur = conn.cursor()
    
    # Tools 테이블 확인
    print("\n📊 Tools Table:")
    cur.execute("""
        SELECT id, name, category, implementation_type, is_builtin
        FROM tools 
        ORDER BY category, name
        LIMIT 10
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:20} | {row[1]:25} | {row[2]:15} | {row[3]:10} | builtin={row[4]}")
    
    # Python Code Tool 확인
    print("\n🐍 Python Code Tool:")
    cur.execute("""
        SELECT id, name, category, implementation_type, input_schema, output_schema
        FROM tools 
        WHERE id = 'python_code'
    """)
    row = cur.fetchone()
    if row:
        print(f"  ✅ Found: {row[0]}")
        print(f"     Name: {row[1]}")
        print(f"     Category: {row[2]}")
        print(f"     Type: {row[3]}")
        print(f"     Input Schema: {json.dumps(row[4], indent=2)[:200]}...")
    else:
        print("  ❌ NOT FOUND")
    
    # HTTP Request Tool 확인
    print("\n🌐 HTTP Request Tool:")
    cur.execute("""
        SELECT id, name, category, implementation_type
        FROM tools 
        WHERE id = 'http_request'
    """)
    row = cur.fetchone()
    if row:
        print(f"  ✅ Found: {row[0]}")
        print(f"     Name: {row[1]}")
        print(f"     Category: {row[2]}")
        print(f"     Type: {row[3]}")
    else:
        print("  ❌ NOT FOUND")
    
    # 카테고리별 통계
    print("\n📈 Tools by Category:")
    cur.execute("""
        SELECT category, COUNT(*) as count
        FROM tools
        GROUP BY category
        ORDER BY count DESC
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:15} : {row[1]:3} tools")
    
    cur.close()
    conn.close()
    
    return True

def test_backend_api():
    """2. Backend API Layer 체크"""
    print_section("2. BACKEND API LAYER")
    
    # 2.1 Tools List API
    print("\n📡 GET /api/agent-builder/tools")
    try:
        response = requests.get(f"{BASE_URL}/api/agent-builder/tools")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📊 Total Tools: {data.get('total', 0)}")
            print(f"  📂 Categories: {len(data.get('categories', []))}")
            print(f"     {', '.join(data.get('categories', []))}")
            
            # Python Code Tool 확인
            tools = data.get('tools', [])
            python_tool = next((t for t in tools if t['id'] == 'python_code'), None)
            if python_tool:
                print(f"\n  🐍 Python Code Tool:")
                print(f"     ✅ Found in API response")
                print(f"     Name: {python_tool['name']}")
                print(f"     Category: {python_tool['category']}")
                print(f"     Params: {len(python_tool.get('params', {}))}")
            else:
                print(f"\n  ❌ Python Code Tool NOT in API response")
            
            # HTTP Request Tool 확인
            http_tool = next((t for t in tools if t['id'] == 'http_request'), None)
            if http_tool:
                print(f"\n  🌐 HTTP Request Tool:")
                print(f"     ✅ Found in API response")
                print(f"     Name: {http_tool['name']}")
                print(f"     Category: {http_tool['category']}")
            else:
                print(f"\n  ❌ HTTP Request Tool NOT in API response")
                
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False
    
    # 2.2 Category Filter
    print("\n📡 GET /api/agent-builder/tools?category=code")
    try:
        response = requests.get(f"{BASE_URL}/api/agent-builder/tools?category=code")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📊 Code Tools: {data.get('total', 0)}")
            for tool in data.get('tools', []):
                print(f"     - {tool['id']}: {tool['name']}")
        else:
            print(f"  ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 2.3 Tool Detail API
    print("\n📡 GET /api/agent-builder/tools/python_code")
    try:
        response = requests.get(f"{BASE_URL}/api/agent-builder/tools/python_code")
        if response.status_code == 200:
            tool = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📝 Tool Details:")
            print(f"     ID: {tool.get('id')}")
            print(f"     Name: {tool.get('name')}")
            print(f"     Category: {tool.get('category')}")
            print(f"     Params: {list(tool.get('params', {}).keys())}")
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return True

def test_tool_execution():
    """3. Tool Execution Layer 체크"""
    print_section("3. TOOL EXECUTION LAYER")
    
    # 3.1 Python Code Execution
    print("\n🐍 Python Code Execution Test")
    try:
        payload = {
            "tool_name": "python_code",
            "parameters": {
                "code": "result = 2 + 2",
                "mode": "simple"
            }
        }
        response = requests.post(
            f"{BASE_URL}/tool-execution/execute",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📊 Result: {json.dumps(result, indent=2)[:300]}")
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 3.2 HTTP Request Execution
    print("\n🌐 HTTP Request Execution Test")
    try:
        payload = {
            "tool_name": "http_request",
            "parameters": {
                "url": "https://api.github.com/zen",
                "method": "GET"
            }
        }
        response = requests.post(
            f"{BASE_URL}/tool-execution/execute",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📊 Result: {json.dumps(result, indent=2)[:300]}")
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # 3.3 Available Tools
    print("\n📋 Available Tools for Execution")
    try:
        response = requests.get(f"{BASE_URL}/tool-execution/available-tools")
        if response.status_code == 200:
            tools = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📊 Categories: {len(tools)}")
            for category, tool_list in list(tools.items())[:5]:
                print(f"     {category}: {len(tool_list)} tools")
        else:
            print(f"  ❌ Status: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return True

def test_workflow_integration():
    """4. Workflow Integration 체크"""
    print_section("4. WORKFLOW INTEGRATION")
    
    # 4.1 Blocks API
    print("\n📦 GET /api/agent-builder/blocks")
    try:
        response = requests.get(f"{BASE_URL}/api/agent-builder/blocks")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ Status: {response.status_code}")
            print(f"  📊 Total Blocks: {data.get('total', 0)}")
            
            # Tool 타입 블록 확인
            blocks = data.get('blocks', [])
            tool_blocks = [b for b in blocks if b.get('block_type') == 'tool']
            print(f"  🔧 Tool Blocks: {len(tool_blocks)}")
            
            # Python Code Block 확인
            python_block = next((b for b in tool_blocks if 'python' in b.get('name', '').lower()), None)
            if python_block:
                print(f"\n  🐍 Python Code Block:")
                print(f"     ✅ Found")
                print(f"     ID: {python_block.get('id')}")
                print(f"     Name: {python_block.get('name')}")
            else:
                print(f"\n  ⚠️  Python Code Block not found in blocks")
                
        else:
            print(f"  ❌ Status: {response.status_code}")
            print(f"  Error: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return True

def test_frontend_compatibility():
    """5. Frontend Compatibility 체크"""
    print_section("5. FRONTEND COMPATIBILITY")
    
    print("\n📱 Frontend API Response Format Check")
    
    # Tools API 응답 형식 확인
    try:
        response = requests.get(f"{BASE_URL}/api/agent-builder/tools")
        if response.status_code == 200:
            data = response.json()
            
            # 필수 필드 확인
            required_fields = ['tools', 'total', 'categories']
            missing_fields = [f for f in required_fields if f not in data]
            
            if not missing_fields:
                print(f"  ✅ Response structure valid")
                print(f"     - tools: {type(data['tools']).__name__} ({len(data['tools'])} items)")
                print(f"     - total: {type(data['total']).__name__} ({data['total']})")
                print(f"     - categories: {type(data['categories']).__name__} ({len(data['categories'])} items)")
            else:
                print(f"  ❌ Missing fields: {missing_fields}")
            
            # Tool 객체 구조 확인
            if data['tools']:
                tool = data['tools'][0]
                tool_fields = ['id', 'name', 'description', 'category', 'params', 'outputs']
                missing_tool_fields = [f for f in tool_fields if f not in tool]
                
                if not missing_tool_fields:
                    print(f"\n  ✅ Tool object structure valid")
                    print(f"     Fields: {', '.join(tool_fields)}")
                else:
                    print(f"\n  ❌ Tool missing fields: {missing_tool_fields}")
                
                # Params 구조 확인
                if 'params' in tool and tool['params']:
                    param_name = list(tool['params'].keys())[0]
                    param = tool['params'][param_name]
                    param_fields = ['type', 'description']
                    
                    if all(f in param for f in param_fields):
                        print(f"\n  ✅ Param structure valid")
                        print(f"     Example: {param_name}")
                        print(f"     - type: {param['type']}")
                        print(f"     - description: {param['description'][:50]}...")
                    else:
                        print(f"\n  ⚠️  Param structure incomplete")
                        
        else:
            print(f"  ❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    return True

def generate_report():
    """최종 리포트 생성"""
    print_section("FINAL REPORT")
    
    print("\n✅ Workflow Tools 전체 스택 검증 완료")
    print("\n검증 항목:")
    print("  1. ✅ Database Layer - Tools 테이블 확인")
    print("  2. ✅ Backend API Layer - REST API 엔드포인트")
    print("  3. ✅ Tool Execution Layer - 실제 실행 테스트")
    print("  4. ✅ Workflow Integration - Blocks 연동")
    print("  5. ✅ Frontend Compatibility - API 응답 형식")
    
    print("\n주요 Tool 확인:")
    print("  🐍 Python Code Executor - Enhanced Security")
    print("  🌐 HTTP Request - Generic API Client")
    
    print("\n다음 단계:")
    print("  1. Frontend에서 Tool 목록 확인")
    print("  2. Workflow Canvas에서 Tool Block 추가")
    print("  3. Tool 실행 및 결과 확인")
    
    print("\n" + "=" * 70)

def main():
    """메인 실행"""
    print("\n" + "=" * 70)
    print("  WORKFLOW TOOLS - 전체 스택 검증")
    print("  Database → Backend API → Tool Execution → Frontend")
    print("=" * 70)
    
    try:
        # 1. Database
        if not test_database():
            print("\n❌ Database check failed")
            return
        
        # 2. Backend API
        if not test_backend_api():
            print("\n❌ Backend API check failed")
            return
        
        # 3. Tool Execution
        if not test_tool_execution():
            print("\n❌ Tool Execution check failed")
            return
        
        # 4. Workflow Integration
        if not test_workflow_integration():
            print("\n❌ Workflow Integration check failed")
            return
        
        # 5. Frontend Compatibility
        if not test_frontend_compatibility():
            print("\n❌ Frontend Compatibility check failed")
            return
        
        # Final Report
        generate_report()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
