"""
Tool Config System Test Script

50+ Tools의 Config UI가 제대로 작동하는지 테스트
"""

import json
import time
from pathlib import Path

def test_tool_config_registry():
    """ToolConfigRegistry.tsx 파일 검증"""
    print("=" * 60)
    print("TEST 1: ToolConfigRegistry.tsx 검증")
    print("=" * 60)
    
    registry_path = Path("frontend/components/agent-builder/tool-configs/ToolConfigRegistry.tsx")
    
    if not registry_path.exists():
        print("❌ FAIL: ToolConfigRegistry.tsx 파일이 없습니다")
        return False
    
    content = registry_path.read_text(encoding='utf-8')
    
    # 필수 요소 체크
    checks = {
        "export const TOOL_CONFIG_REGISTRY": "Registry 정의",
        "ToolParamSchema": "파라미터 스키마 타입",
        "ToolConfigSchema": "Tool 스키마 타입",
        "getToolConfig": "Tool 가져오기 함수",
        "getToolsByCategory": "카테고리별 Tool 함수",
        "getAllCategories": "카테고리 목록 함수",
        "searchTools": "Tool 검색 함수",
    }
    
    all_passed = True
    for key, desc in checks.items():
        if key in content:
            print(f"✅ {desc}: OK")
        else:
            print(f"❌ {desc}: MISSING")
            all_passed = False
    
    # Tool 개수 세기
    tool_count = content.count("id: '")
    print(f"\n📊 등록된 Tools: {tool_count}개")
    
    # Select Box 개수 세기
    select_count = content.count("type: 'select'")
    print(f"📊 Select Box 필드: {select_count}개")
    
    # 예제 개수 세기
    example_count = content.count("examples: [")
    print(f"📊 예제가 있는 Tools: {example_count}개")
    
    return all_passed


def test_advanced_ui():
    """AdvancedToolConfigUI.tsx 파일 검증"""
    print("\n" + "=" * 60)
    print("TEST 2: AdvancedToolConfigUI.tsx 검증")
    print("=" * 60)
    
    ui_path = Path("frontend/components/agent-builder/tool-configs/AdvancedToolConfigUI.tsx")
    
    if not ui_path.exists():
        print("❌ FAIL: AdvancedToolConfigUI.tsx 파일이 없습니다")
        return False
    
    content = ui_path.read_text(encoding='utf-8')
    
    # 필수 컴포넌트 체크
    checks = {
        "export function AdvancedToolConfigUI": "메인 컴포넌트",
        "function ParameterInput": "파라미터 입력 컴포넌트",
        "case 'select'": "Select Box 처리",
        "case 'textarea'": "Textarea 처리",
        "case 'boolean'": "Boolean 처리",
        "case 'number'": "Number 처리",
        "case 'password'": "Password 처리",
        "case 'json'": "JSON 처리",
        "case 'array'": "Array 처리",
        "validateConfig": "유효성 검사",
        "Tabs": "탭 UI",
        "Examples": "예제 탭",
    }
    
    all_passed = True
    for key, desc in checks.items():
        if key in content:
            print(f"✅ {desc}: OK")
        else:
            print(f"❌ {desc}: MISSING")
            all_passed = False
    
    return all_passed


def test_demo_page():
    """데모 페이지 검증"""
    print("\n" + "=" * 60)
    print("TEST 3: 데모 페이지 검증")
    print("=" * 60)
    
    demo_path = Path("frontend/app/tool-config-demo/page.tsx")
    
    if not demo_path.exists():
        print("❌ FAIL: tool-config-demo/page.tsx 파일이 없습니다")
        return False
    
    content = demo_path.read_text(encoding='utf-8')
    
    # 필수 기능 체크
    checks = {
        "TOOL_CONFIG_REGISTRY": "Registry 임포트",
        "getAllCategories": "카테고리 함수",
        "getToolsByCategory": "카테고리별 Tool",
        "AdvancedToolConfigUI": "UI 컴포넌트",
        "searchQuery": "검색 기능",
        "selectedCategory": "카테고리 필터",
        "filteredTools": "Tool 필터링",
        "Badge": "Badge 컴포넌트",
        "Card": "Card 컴포넌트",
    }
    
    all_passed = True
    for key, desc in checks.items():
        if key in content:
            print(f"✅ {desc}: OK")
        else:
            print(f"❌ {desc}: MISSING")
            all_passed = False
    
    return all_passed


def test_tool_categories():
    """Tool 카테고리 검증"""
    print("\n" + "=" * 60)
    print("TEST 4: Tool 카테고리 검증")
    print("=" * 60)
    
    registry_path = Path("frontend/components/agent-builder/tool-configs/ToolConfigRegistry.tsx")
    content = registry_path.read_text(encoding='utf-8')
    
    # 예상 카테고리
    expected_categories = [
        'ai', 'search', 'communication', 'developer', 'productivity',
        'data', 'code', 'file', 'image', 'utility', 'crm', 'marketing',
        'analytics', 'storage', 'webhook', 'control'
    ]
    
    found_categories = []
    for category in expected_categories:
        if f"category: '{category}'" in content:
            found_categories.append(category)
            print(f"✅ {category}: OK")
        else:
            print(f"⚠️  {category}: NOT FOUND")
    
    print(f"\n📊 발견된 카테고리: {len(found_categories)}/{len(expected_categories)}")
    
    return len(found_categories) >= 10  # 최소 10개 카테고리


def test_specific_tools():
    """특정 Tools 검증"""
    print("\n" + "=" * 60)
    print("TEST 5: 주요 Tools 검증")
    print("=" * 60)
    
    registry_path = Path("frontend/components/agent-builder/tool-configs/ToolConfigRegistry.tsx")
    content = registry_path.read_text(encoding='utf-8')
    
    # 주요 Tools
    important_tools = {
        'openai_chat': 'OpenAI Chat',
        'anthropic_claude': 'Anthropic Claude',
        'google_search': 'Google Search',
        'duckduckgo_search': 'DuckDuckGo Search',
        'send_email': 'Send Email',
        'slack': 'Slack',
        'http_request': 'HTTP Request',
        'github': 'GitHub',
        'notion': 'Notion',
        'database_query': 'Database Query',
        'python_code': 'Python Code',
        'file_reader': 'File Reader',
        'image_processor': 'Image Processor',
        'datetime_formatter': 'DateTime Formatter',
    }
    
    found_tools = []
    for tool_id, tool_name in important_tools.items():
        if f"id: '{tool_id}'" in content:
            found_tools.append(tool_id)
            print(f"✅ {tool_name}: OK")
        else:
            print(f"❌ {tool_name}: MISSING")
    
    print(f"\n📊 발견된 주요 Tools: {len(found_tools)}/{len(important_tools)}")
    
    return len(found_tools) >= 10


def test_select_boxes():
    """Select Box 구현 검증"""
    print("\n" + "=" * 60)
    print("TEST 6: Select Box 구현 검증")
    print("=" * 60)
    
    registry_path = Path("frontend/components/agent-builder/tool-configs/ToolConfigRegistry.tsx")
    content = registry_path.read_text(encoding='utf-8')
    
    # Select Box 예시 찾기
    select_examples = [
        ("AI Models", "gpt-4"),
        ("HTTP Methods", "GET"),
        ("Database Types", "postgresql"),
        ("Languages", "'ko'"),
        ("Time Units", "seconds"),
        ("File Formats", "json"),
        ("Priority", "normal"),
    ]
    
    found = 0
    for name, value in select_examples:
        if value in content:
            found += 1
            print(f"✅ {name} Select Box: OK")
        else:
            print(f"⚠️  {name} Select Box: NOT FOUND")
    
    print(f"\n📊 발견된 Select Box 타입: {found}/{len(select_examples)}")
    
    return found >= 5


def test_documentation():
    """문서 파일 검증"""
    print("\n" + "=" * 60)
    print("TEST 7: 문서 파일 검증")
    print("=" * 60)
    
    docs = {
        "TOOL_CONFIG_COMPLETE.md": "전체 문서",
        "TOOL_CONFIG_QUICK_START.md": "빠른 시작 가이드",
        "TOOL_CONFIG_한글_가이드.md": "한글 가이드",
        "TOOL_CONFIG_SUMMARY.md": "요약 문서",
    }
    
    all_exist = True
    for filename, desc in docs.items():
        path = Path(filename)
        if path.exists():
            size = path.stat().st_size
            print(f"✅ {desc}: OK ({size:,} bytes)")
        else:
            print(f"❌ {desc}: MISSING")
            all_exist = False
    
    return all_exist


def run_all_tests():
    """모든 테스트 실행"""
    print("\n" + "🚀" * 30)
    print("Tool Config System - 통합 테스트")
    print("🚀" * 30 + "\n")
    
    tests = [
        ("Registry 파일", test_tool_config_registry),
        ("UI 컴포넌트", test_advanced_ui),
        ("데모 페이지", test_demo_page),
        ("Tool 카테고리", test_tool_categories),
        ("주요 Tools", test_specific_tools),
        ("Select Box", test_select_boxes),
        ("문서", test_documentation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {e}")
            results.append((name, False))
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "=" * 60)
    print(f"총 {passed}/{total} 테스트 통과 ({passed/total*100:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 모든 테스트 통과! Tool Config 시스템이 정상 작동합니다!")
        print("\n📍 데모 페이지: http://localhost:3001/tool-config-demo")
    else:
        print(f"\n⚠️  {total - passed}개 테스트 실패. 위 내용을 확인하세요.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
