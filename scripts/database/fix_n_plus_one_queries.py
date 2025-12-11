#!/usr/bin/env python3
"""
N+1 쿼리 문제 자동 수정 스크립트

이 스크립트는 API 코드에서 N+1 쿼리를 발생시키는 패턴을 찾아
query_helpers.py의 최적화된 함수로 자동 교체합니다.

Usage:
    python scripts/fix_n_plus_one_queries.py --dry-run  # 미리보기
    python scripts/fix_n_plus_one_queries.py --apply    # 실제 적용
"""

import re
import os
from pathlib import Path
from typing import List, Tuple

# 수정 대상 파일 및 패턴
FIXES = [
    {
        "file": "backend/api/agent_builder/chat.py",
        "pattern": r'workflow = db\.query\(Workflow\)\.filter\(Workflow\.id == workflow_id\)\.first\(\)',
        "replacement": """from backend.db.query_helpers import get_workflow_with_relations
        workflow = get_workflow_with_relations(db, workflow_id)""",
        "import_line": "from backend.db.query_helpers import get_workflow_with_relations",
        "line_numbers": [65, 204, 263]
    },
    {
        "file": "backend/api/agent_builder/workflow_execution_stream.py",
        "pattern": r'workflow = db\.query\(Workflow\)\.filter\(Workflow\.id == workflow_id\)\.first\(\)',
        "replacement": """from backend.db.query_helpers import get_workflow_with_relations
        workflow = get_workflow_with_relations(db, workflow_id)""",
        "import_line": "from backend.db.query_helpers import get_workflow_with_relations",
        "line_numbers": [52, 193]
    },
    {
        "file": "backend/services/agent_builder/workflow_service.py",
        "pattern": r'return self\.db\.query\(Workflow\)\.filter\(Workflow\.id == workflow_id\)\.first\(\)',
        "replacement": """from backend.db.query_helpers import get_workflow_with_relations
        return get_workflow_with_relations(self.db, workflow_id)""",
        "import_line": "from backend.db.query_helpers import get_workflow_with_relations",
        "line_numbers": [136]
    },
    {
        "file": "backend/api/agent_builder/dashboard.py",
        "pattern": r'recent_executions = db\.query\(AgentExecution\)\\s*\.filter\(AgentExecution\.user_id == user_id\)\\s*\.order_by\(desc\(AgentExecution\.started_at\)\)\\s*\.limit\(limit\)\.all\(\)',
        "replacement": """from backend.db.query_helpers import get_dashboard_executions_optimized
        recent_executions = get_dashboard_executions_optimized(db, user_id, limit)""",
        "import_line": "from backend.db.query_helpers import get_dashboard_executions_optimized",
        "line_numbers": [139]
    }
]


def read_file(filepath: str) -> str:
    """파일 읽기"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def write_file(filepath: str, content: str):
    """파일 쓰기"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)


def add_import_if_missing(content: str, import_line: str) -> str:
    """import 문이 없으면 추가"""
    if import_line in content:
        return content
    
    # 첫 번째 import 블록 찾기
    lines = content.split('\n')
    import_index = -1
    
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            import_index = i
    
    if import_index >= 0:
        # 마지막 import 다음에 추가
        lines.insert(import_index + 1, import_line)
        return '\n'.join(lines)
    
    return content


def apply_fix(filepath: str, pattern: str, replacement: str, import_line: str) -> Tuple[bool, str]:
    """수정 적용"""
    try:
        content = read_file(filepath)
        original_content = content
        
        # 패턴 찾기
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        
        if not matches:
            return False, "패턴을 찾을 수 없습니다"
        
        # 교체
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        
        # import 추가
        content = add_import_if_missing(content, import_line)
        
        if content == original_content:
            return False, "변경 사항 없음"
        
        return True, f"{len(matches)}개 패턴 교체됨"
        
    except Exception as e:
        return False, f"오류: {str(e)}"


def preview_changes(dry_run: bool = True):
    """변경 사항 미리보기 또는 적용"""
    
    print("=" * 80)
    print("N+1 쿼리 자동 수정 스크립트")
    print("=" * 80)
    print()
    
    if dry_run:
        print("🔍 DRY RUN 모드 - 실제 파일은 수정되지 않습니다")
    else:
        print("⚠️  실제 파일을 수정합니다!")
    
    print()
    
    total_files = 0
    total_changes = 0
    
    for fix in FIXES:
        filepath = fix["file"]
        pattern = fix["pattern"]
        replacement = fix["replacement"]
        import_line = fix["import_line"]
        
        print(f"📄 파일: {filepath}")
        print(f"   라인: {fix['line_numbers']}")
        
        if not os.path.exists(filepath):
            print(f"   ❌ 파일을 찾을 수 없습니다")
            print()
            continue
        
        if dry_run:
            # 미리보기
            content = read_file(filepath)
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            
            if matches:
                print(f"   ✅ {len(matches)}개 패턴 발견")
                print(f"   📝 변경 예정:")
                print(f"      Before: {pattern[:50]}...")
                print(f"      After:  {replacement[:50]}...")
                total_files += 1
                total_changes += len(matches)
            else:
                print(f"   ℹ️  패턴을 찾을 수 없습니다")
        else:
            # 실제 적용
            success, message = apply_fix(filepath, pattern, replacement, import_line)
            
            if success:
                print(f"   ✅ {message}")
                write_file(filepath, read_file(filepath))  # 실제 저장
                total_files += 1
                total_changes += 1
            else:
                print(f"   ℹ️  {message}")
        
        print()
    
    print("=" * 80)
    print(f"📊 요약:")
    print(f"   수정된 파일: {total_files}개")
    print(f"   총 변경 사항: {total_changes}개")
    print("=" * 80)
    
    if dry_run:
        print()
        print("💡 실제 적용하려면: python scripts/fix_n_plus_one_queries.py --apply")
    else:
        print()
        print("✅ 수정 완료!")
        print("📝 다음 단계:")
        print("   1. git diff로 변경 사항 확인")
        print("   2. pytest backend/tests/integration/ 실행")
        print("   3. git commit -m 'fix: Use query helpers to prevent N+1 queries'")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        preview_changes(dry_run=False)
    else:
        preview_changes(dry_run=True)
