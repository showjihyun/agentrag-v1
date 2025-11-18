#!/usr/bin/env python3
"""
HTTP Request Tool 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_http_request(test_name, parameters):
    """HTTP Request 도구 테스트"""
    print(f"\n{'='*60}")
    print(f"테스트: {test_name}")
    print(f"{'='*60}")
    print(f"Parameters: {json.dumps(parameters, indent=2)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent-builder/tools/execute",
            json={
                "tool_id": "http_request",
                "parameters": parameters
            },
            timeout=30
        )
        
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Duration: {result.get('duration_ms')}ms")
            print(f"\nResult:")
            print(json.dumps(result.get('result'), indent=2))
            return True
        else:
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"Exception: {e}")
        return False


def main():
    """메인 테스트 함수"""
    
    tests = [
        # 테스트 1: 간단한 GET
        ("Simple GET Request", {
            "url": "https://api.github.com/users/octocat",
            "method": "GET"
        }),
        
        # 테스트 2: Headers 포함
        ("GET with Headers", {
            "url": "https://api.github.com/users/octocat",
            "method": "GET",
            "headers": {
                "Accept": "application/json",
                "User-Agent": "AgenticRAG-Test"
            }
        }),
        
        # 테스트 3: Query Parameters
        ("GET with Query Parameters", {
            "url": "https://httpbin.org/get",
            "method": "GET",
            "query_parameters": {
                "page": "1",
                "limit": "10"
            }
        }),
        
        # 테스트 4: POST with Body
        ("POST with JSON Body", {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": {
                "name": "Test User",
                "email": "test@example.com"
            }
        }),
        
        # 테스트 5: Timeout (짧은 시간)
        ("Timeout Test", {
            "url": "https://httpbin.org/delay/2",
            "method": "GET",
            "timeout": 5
        }),
    ]
    
    results = []
    for test_name, parameters in tests:
        success = test_http_request(test_name, parameters)
        results.append((test_name, success))
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("테스트 결과 요약")
    print(f"{'='*60}")
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total = len(results)
    passed = sum(1 for _, success in results if success)
    print(f"\n총 {total}개 테스트 중 {passed}개 성공 ({passed/total*100:.1f}%)")


if __name__ == "__main__":
    main()
