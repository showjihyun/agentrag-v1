"""
Workflow Tools Live Integration Test
실제 도구들이 제대로 작동하는지 테스트합니다.
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend')))


class ToolTestRunner:
    """도구 테스트 실행기"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {"INFO": "ℹ️", "PASS": "✅", "FAIL": "❌", "WARN": "⚠️"}.get(level, "•")
        print(f"[{timestamp}] {icon} {message}")
        
    async def test_tool_registration(self):
        """도구 등록 테스트"""
        self.log("=== 도구 등록 테스트 ===")
        
        from backend.core.tools.init_tools import initialize_tools, get_tool_summary
        from backend.core.tools.registry import ToolRegistry
        
        # Initialize tools
        initialize_tools()
        
        summary = get_tool_summary()
        self.log(f"총 등록된 도구: {summary['total_tools']}개")
        
        for category, count in summary['by_category'].items():
            self.log(f"  {category}: {count}개")
        
        # Check minimum tool count
        if summary['total_tools'] >= 30:
            self.log("도구 등록 테스트 통과", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"도구 수 부족: {summary['total_tools']} < 30", "FAIL")
            self.failed += 1
            return False
    
    async def test_tool_config_retrieval(self):
        """도구 설정 조회 테스트"""
        self.log("=== 도구 설정 조회 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        test_tools = [
            'http_request',
            'openai_chat',
            'ai_agent',
            'tavily_search',
            'supabase_query',
            'discord',
            'telegram'
        ]
        
        success_count = 0
        for tool_id in test_tools:
            config = ToolRegistry.get_tool_config(tool_id)
            if config:
                self.log(f"  {tool_id}: {config.name} ({config.category})", "PASS")
                success_count += 1
            else:
                self.log(f"  {tool_id}: 설정 없음", "FAIL")
        
        if success_count >= len(test_tools) * 0.7:
            self.log(f"도구 설정 조회 테스트 통과 ({success_count}/{len(test_tools)})", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"도구 설정 조회 테스트 실패 ({success_count}/{len(test_tools)})", "FAIL")
            self.failed += 1
            return False
    
    async def test_http_tool_execution(self):
        """HTTP 도구 실행 테스트"""
        self.log("=== HTTP 도구 실행 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        try:
            result = await ToolRegistry.execute_tool(
                tool_id='http_request',
                params={
                    'url': 'https://jsonplaceholder.typicode.com/posts/1',
                    'method': 'GET',
                    'timeout': 10
                }
            )
            
            if result.get('success') or result.get('id'):
                self.log(f"HTTP GET 요청 성공: {json.dumps(result, indent=2)[:200]}...", "PASS")
                self.passed += 1
                return True
            else:
                self.log(f"HTTP 요청 실패: {result}", "FAIL")
                self.failed += 1
                return False
                
        except Exception as e:
            self.log(f"HTTP 도구 실행 오류: {e}", "FAIL")
            self.failed += 1
            return False
    
    async def test_tool_parameter_validation(self):
        """도구 파라미터 검증 테스트"""
        self.log("=== 파라미터 검증 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        # Test with missing required parameter
        try:
            result = await ToolRegistry.execute_tool(
                tool_id='http_request',
                params={}  # Missing 'url' parameter
            )
            # Should have failed or returned error
            if result.get('success') == False or result.get('error'):
                self.log("필수 파라미터 누락 시 에러 반환 확인", "PASS")
                self.passed += 1
                return True
        except Exception as e:
            # Expected behavior - validation error
            self.log(f"파라미터 검증 작동: {type(e).__name__}", "PASS")
            self.passed += 1
            return True
        
        self.log("파라미터 검증 미작동", "WARN")
        return False
    
    async def test_tool_categories(self):
        """도구 카테고리 테스트"""
        self.log("=== 도구 카테고리 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        expected_categories = ['ai', 'AI', 'communication', 'data', 'search', 'developer']
        by_category = ToolRegistry.list_by_category()
        
        found_categories = list(by_category.keys())
        self.log(f"발견된 카테고리: {found_categories}")
        
        # Check if we have at least 5 categories
        if len(found_categories) >= 5:
            self.log("카테고리 테스트 통과", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"카테고리 부족: {len(found_categories)} < 5", "FAIL")
            self.failed += 1
            return False
    
    async def test_ai_tool_config(self):
        """AI 도구 설정 테스트"""
        self.log("=== AI 도구 설정 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        ai_tools = ['openai_chat', 'anthropic_claude', 'google_gemini', 'ai_agent']
        
        for tool_id in ai_tools:
            config = ToolRegistry.get_tool_config(tool_id)
            if config:
                params = list(config.params.keys())
                self.log(f"  {tool_id}: params={params[:5]}")
        
        # Check ai_agent specifically
        ai_agent_config = ToolRegistry.get_tool_config('ai_agent')
        if ai_agent_config and 'task' in ai_agent_config.params:
            self.log("AI Agent 도구 설정 확인", "PASS")
            self.passed += 1
            return True
        else:
            self.log("AI Agent 도구 설정 누락", "FAIL")
            self.failed += 1
            return False
    
    async def test_search_tools(self):
        """검색 도구 테스트"""
        self.log("=== 검색 도구 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        search_tools = [
            'tavily_search', 'serper_search', 'exa_search',
            'wikipedia_search', 'arxiv_search', 'duckduckgo_search',
            'youtube_search'
        ]
        
        found = 0
        for tool_id in search_tools:
            config = ToolRegistry.get_tool_config(tool_id)
            if config:
                found += 1
                self.log(f"  {tool_id}: {config.name}")
        
        if found >= 5:
            self.log(f"검색 도구 테스트 통과 ({found}/{len(search_tools)})", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"검색 도구 부족 ({found}/{len(search_tools)})", "FAIL")
            self.failed += 1
            return False
    
    async def test_data_tools(self):
        """데이터 도구 테스트"""
        self.log("=== 데이터 도구 테스트 ===")
        
        from backend.core.tools.registry import ToolRegistry
        
        data_tools = [
            'supabase_query', 'pinecone_upsert', 'qdrant_insert',
            's3_upload', 'mongodb_insert', 'postgresql_query',
            'mysql_query', 'redis_set', 'elasticsearch_index', 'bigquery_query'
        ]
        
        found = 0
        for tool_id in data_tools:
            config = ToolRegistry.get_tool_config(tool_id)
            if config:
                found += 1
                self.log(f"  {tool_id}: {config.name}")
        
        if found >= 7:
            self.log(f"데이터 도구 테스트 통과 ({found}/{len(data_tools)})", "PASS")
            self.passed += 1
            return True
        else:
            self.log(f"데이터 도구 부족 ({found}/{len(data_tools)})", "FAIL")
            self.failed += 1
            return False
    
    async def run_all_tests(self):
        """모든 테스트 실행"""
        self.log("=" * 50)
        self.log("Workflow Tools 통합 테스트 시작")
        self.log("=" * 50)
        
        tests = [
            self.test_tool_registration,
            self.test_tool_config_retrieval,
            self.test_tool_categories,
            self.test_ai_tool_config,
            self.test_search_tools,
            self.test_data_tools,
            self.test_http_tool_execution,
            self.test_tool_parameter_validation,
        ]
        
        for test in tests:
            try:
                await test()
            except Exception as e:
                self.log(f"테스트 실행 오류: {test.__name__} - {e}", "FAIL")
                self.failed += 1
            print()
        
        self.log("=" * 50)
        self.log(f"테스트 결과: {self.passed} 통과, {self.failed} 실패")
        self.log("=" * 50)
        
        return self.failed == 0


async def main():
    runner = ToolTestRunner()
    success = await runner.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
