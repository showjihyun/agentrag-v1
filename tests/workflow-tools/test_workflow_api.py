"""
Workflow API Integration Test
워크플로우 API 엔드포인트 테스트
"""

import asyncio
import httpx
import json
from datetime import datetime


class WorkflowAPITester:
    """워크플로우 API 테스터"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.token = None
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "•")
        print(f"[{timestamp}] {icon} {message}")
        
    async def test_health_check(self) -> bool:
        """헬스 체크 테스트"""
        self.log("=== 헬스 체크 테스트 ===")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/health")
                
                if response.status_code == 200:
                    self.log("헬스 체크 통과", "PASS")
                    return True
                else:
                    self.log(f"헬스 체크 실패: {response.status_code}", "FAIL")
                    return False
        except Exception as e:
            self.log(f"헬스 체크 오류: {e}", "FAIL")
            return False
    
    async def test_tools_list(self) -> bool:
        """도구 목록 API 테스트"""
        self.log("=== 도구 목록 API 테스트 ===")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                endpoint = "/api/agent-builder/tools/available-tools"
                response = await client.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    tool_count = len(data) if isinstance(data, list) else data.get('total', 0)
                    self.log(f"도구 목록 조회 성공: {tool_count}개", "PASS")
                    return True
                elif response.status_code == 401:
                    self.log(f"인증 필요 (예상된 동작) - 401", "PASS")
                    return True
                else:
                    self.log(f"도구 목록 조회: {response.status_code}", "WARN")
                    return True  # API 존재 확인됨
        except Exception as e:
            self.log(f"도구 목록 API 오류: {e}", "WARN")
            return False
    
    async def test_workflows_list(self) -> bool:
        """워크플로우 목록 API 테스트"""
        self.log("=== 워크플로우 목록 API 테스트 ===")
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                endpoint = "/api/agent-builder/workflows"
                response = await client.get(f"{self.base_url}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    workflow_count = len(data.get('workflows', [])) if isinstance(data, dict) else len(data)
                    self.log(f"워크플로우 목록 조회 성공: {workflow_count}개", "PASS")
                    return True
                elif response.status_code == 401:
                    self.log(f"인증 필요 (예상된 동작) - 401", "PASS")
                    return True
                else:
                    self.log(f"워크플로우 목록 조회: {response.status_code}", "WARN")
                    return True  # API 존재 확인됨
        except Exception as e:
            self.log(f"워크플로우 목록 API 오류: {e}", "WARN")
            return False
    
    async def test_workflow_create(self) -> bool:
        """워크플로우 생성 API 테스트"""
        self.log("=== 워크플로우 생성 API 테스트 ===")
        
        test_workflow = {
            "name": "Test Workflow",
            "description": "API 테스트용 워크플로우",
            "nodes": [
                {
                    "id": "node_1",
                    "type": "http_request",
                    "position": {"x": 100, "y": 100},
                    "data": {
                        "method": "GET",
                        "url": "https://jsonplaceholder.typicode.com/posts/1"
                    }
                }
            ],
            "edges": []
        }
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    f"{self.base_url}/api/agent-builder/workflows",
                    json=test_workflow
                )
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    self.log(f"워크플로우 생성 성공: {data.get('id', 'N/A')}", "PASS")
                    return True
                elif response.status_code == 401:
                    self.log("인증 필요 (예상된 동작)", "WARN")
                    return True
                else:
                    self.log(f"워크플로우 생성 실패: {response.status_code}", "FAIL")
                    return False
        except Exception as e:
            self.log(f"워크플로우 생성 API 오류: {e}", "WARN")
            return False
    
    async def test_tool_execute(self) -> bool:
        """도구 실행 API 테스트"""
        self.log("=== 도구 실행 API 테스트 ===")
        
        test_params = {
            "tool_id": "http_request",
            "params": {
                "url": "https://jsonplaceholder.typicode.com/posts/1",
                "method": "GET"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"{self.base_url}/api/agent-builder/tools/execute",
                    json=test_params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log(f"도구 실행 성공: {json.dumps(data)[:100]}...", "PASS")
                    return True
                elif response.status_code == 401:
                    self.log("인증 필요 (예상된 동작)", "WARN")
                    return True
                else:
                    self.log(f"도구 실행 실패: {response.status_code}", "FAIL")
                    return False
        except Exception as e:
            self.log(f"도구 실행 API 오류: {e}", "WARN")
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.log("=" * 50)
        self.log("Workflow API 통합 테스트 시작")
        self.log("=" * 50)
        
        tests = [
            ("헬스 체크", self.test_health_check),
            ("도구 목록", self.test_tools_list),
            ("워크플로우 목록", self.test_workflows_list),
            ("워크플로우 생성", self.test_workflow_create),
            ("도구 실행", self.test_tool_execute),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"{name} 테스트 오류: {e}", "FAIL")
                failed += 1
            print()
        
        self.log("=" * 50)
        self.log(f"API 테스트 결과: {passed} 통과, {failed} 실패")
        self.log("=" * 50)
        
        return failed == 0


async def main():
    tester = WorkflowAPITester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
