#!/usr/bin/env python3
"""
Backend 코딩 스타일 점검 스크립트

PEP 8, 타입 힌팅, docstring, 네이밍 등을 점검합니다.
"""

import os
import ast
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


class CodeStyleChecker:
    """코드 스타일 점검기"""
    
    def __init__(self, backend_dir: str = "backend"):
        self.backend_dir = Path(backend_dir)
        self.issues = defaultdict(list)
        self.stats = {
            'total_files': 0,
            'total_lines': 0,
            'total_functions': 0,
            'total_classes': 0,
            'issues_found': 0
        }
    
    def check_all(self):
        """모든 Python 파일 점검"""
        print("=" * 80)
        print("Backend 코딩 스타일 점검 시작")
        print("=" * 80)
        
        # Python 파일 찾기
        python_files = list(self.backend_dir.rglob("*.py"))
        
        # __pycache__, venv 제외
        python_files = [
            f for f in python_files 
            if '__pycache__' not in str(f) and 'venv' not in str(f)
        ]
        
        self.stats['total_files'] = len(python_files)
        
        print(f"\n점검 대상: {len(python_files)}개 파일\n")
        
        for file_path in python_files:
            self.check_file(file_path)
        
        self.print_report()
    
    def check_file(self, file_path: Path):
        """개별 파일 점검"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            self.stats['total_lines'] += len(lines)
            
            # AST 파싱
            try:
                tree = ast.parse(content)
                self.check_ast(file_path, tree, content, lines)
            except SyntaxError as e:
                self.add_issue(file_path, 'syntax', f"Syntax error: {e}")
            
            # 텍스트 기반 점검
            self.check_text_style(file_path, lines)
            
        except Exception as e:
            self.add_issue(file_path, 'error', f"Failed to check: {e}")
    
    def check_ast(self, file_path: Path, tree: ast.AST, content: str, lines: List[str]):
        """AST 기반 점검"""
        for node in ast.walk(tree):
            # 함수 점검
            if isinstance(node, ast.FunctionDef):
                self.stats['total_functions'] += 1
                self.check_function(file_path, node, lines)
            
            # 클래스 점검
            elif isinstance(node, ast.ClassDef):
                self.stats['total_classes'] += 1
                self.check_class(file_path, node, lines)
    
    def check_function(self, file_path: Path, node: ast.FunctionDef, lines: List[str]):
        """함수 점검"""
        func_name = node.name
        
        # 1. Docstring 점검
        docstring = ast.get_docstring(node)
        if not docstring and not func_name.startswith('_'):
            # Public 함수는 docstring 필요
            if len(node.body) > 3:  # 간단한 함수는 제외
                self.add_issue(
                    file_path, 
                    'docstring',
                    f"Function '{func_name}' (line {node.lineno}) missing docstring"
                )
        
        # 2. 타입 힌팅 점검
        if not node.returns and not func_name.startswith('_'):
            # Public 함수는 반환 타입 힌팅 권장
            pass  # Warning level
        
        # 3. 함수 길이 점검
        func_length = len(node.body)
        if func_length > 50:
            self.add_issue(
                file_path,
                'complexity',
                f"Function '{func_name}' (line {node.lineno}) is too long ({func_length} statements)"
            )
        
        # 4. 네이밍 점검
        if not func_name.startswith('_') and not func_name.islower():
            if '_' not in func_name:
                self.add_issue(
                    file_path,
                    'naming',
                    f"Function '{func_name}' (line {node.lineno}) should use snake_case"
                )
    
    def check_class(self, file_path: Path, node: ast.ClassDef, lines: List[str]):
        """클래스 점검"""
        class_name = node.name
        
        # 1. Docstring 점검
        docstring = ast.get_docstring(node)
        if not docstring:
            self.add_issue(
                file_path,
                'docstring',
                f"Class '{class_name}' (line {node.lineno}) missing docstring"
            )
        
        # 2. 네이밍 점검 (PascalCase)
        if not class_name[0].isupper():
            self.add_issue(
                file_path,
                'naming',
                f"Class '{class_name}' (line {node.lineno}) should use PascalCase"
            )
    
    def check_text_style(self, file_path: Path, lines: List[str]):
        """텍스트 기반 스타일 점검"""
        for i, line in enumerate(lines, 1):
            # 1. 줄 길이 점검 (PEP 8: 79자, 관대하게 120자)
            if len(line) > 120:
                self.add_issue(
                    file_path,
                    'line_length',
                    f"Line {i} exceeds 120 characters ({len(line)} chars)"
                )
            
            # 2. 후행 공백 점검
            if line.endswith(' ') or line.endswith('\t'):
                self.add_issue(
                    file_path,
                    'whitespace',
                    f"Line {i} has trailing whitespace"
                )
            
            # 3. TODO/FIXME 점검
            if 'TODO' in line or 'FIXME' in line:
                self.add_issue(
                    file_path,
                    'todo',
                    f"Line {i} contains TODO/FIXME: {line.strip()}"
                )
    
    def add_issue(self, file_path: Path, category: str, message: str):
        """이슈 추가"""
        rel_path = file_path.relative_to(self.backend_dir)
        self.issues[category].append({
            'file': str(rel_path),
            'message': message
        })
        self.stats['issues_found'] += 1
    
    def print_report(self):
        """리포트 출력"""
        print("\n" + "=" * 80)
        print("점검 결과")
        print("=" * 80)
        
        # 통계
        print(f"\n📊 통계:")
        print(f"  - 파일 수: {self.stats['total_files']}")
        print(f"  - 총 라인 수: {self.stats['total_lines']:,}")
        print(f"  - 함수 수: {self.stats['total_functions']}")
        print(f"  - 클래스 수: {self.stats['total_classes']}")
        print(f"  - 발견된 이슈: {self.stats['issues_found']}")
        
        # 카테고리별 이슈
        if self.issues:
            print(f"\n⚠️  이슈 상세:")
            
            for category, issues in sorted(self.issues.items()):
                print(f"\n  [{category.upper()}] ({len(issues)}개)")
                
                # 상위 5개만 표시
                for issue in issues[:5]:
                    print(f"    - {issue['file']}: {issue['message']}")
                
                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more")
        else:
            print("\n✅ 이슈 없음!")
        
        # 개선 권장사항
        self.print_recommendations()
    
    def print_recommendations(self):
        """개선 권장사항 출력"""
        print("\n" + "=" * 80)
        print("💡 개선 권장사항")
        print("=" * 80)
        
        recommendations = []
        
        # Docstring 이슈
        if 'docstring' in self.issues:
            count = len(self.issues['docstring'])
            recommendations.append(
                f"1. Docstring 추가 ({count}개 함수/클래스)\n"
                f"   - 모든 public 함수와 클래스에 docstring 추가\n"
                f"   - Google/NumPy 스타일 docstring 사용 권장"
            )
        
        # 복잡도 이슈
        if 'complexity' in self.issues:
            count = len(self.issues['complexity'])
            recommendations.append(
                f"2. 함수 복잡도 개선 ({count}개 함수)\n"
                f"   - 긴 함수를 작은 함수로 분리\n"
                f"   - 단일 책임 원칙(SRP) 적용"
            )
        
        # 네이밍 이슈
        if 'naming' in self.issues:
            count = len(self.issues['naming'])
            recommendations.append(
                f"3. 네이밍 컨벤션 통일 ({count}개)\n"
                f"   - 함수/변수: snake_case\n"
                f"   - 클래스: PascalCase\n"
                f"   - 상수: UPPER_SNAKE_CASE"
            )
        
        # 줄 길이 이슈
        if 'line_length' in self.issues:
            count = len(self.issues['line_length'])
            recommendations.append(
                f"4. 줄 길이 조정 ({count}개 라인)\n"
                f"   - 120자 이내로 제한\n"
                f"   - 긴 문자열은 여러 줄로 분리"
            )
        
        # TODO 이슈
        if 'todo' in self.issues:
            count = len(self.issues['todo'])
            recommendations.append(
                f"5. TODO/FIXME 처리 ({count}개)\n"
                f"   - 미완성 작업 완료\n"
                f"   - 또는 이슈 트래커로 이동"
            )
        
        if recommendations:
            for rec in recommendations:
                print(f"\n{rec}")
        else:
            print("\n✅ 코드 스타일이 우수합니다!")
        
        # 추가 권장사항
        print("\n" + "-" * 80)
        print("추가 권장사항:")
        print("-" * 80)
        print("""
1. 타입 힌팅 강화
   - 모든 함수 파라미터와 반환값에 타입 힌팅 추가
   - mypy로 타입 체크 자동화

2. 린터 도구 사용
   - pylint: 코드 품질 점검
   - flake8: PEP 8 준수 점검
   - black: 자동 포맷팅

3. 문서화 개선
   - 복잡한 알고리즘에 주석 추가
   - README에 아키텍처 다이어그램 추가

4. 테스트 커버리지
   - 단위 테스트 추가
   - pytest-cov로 커버리지 측정

5. 코드 리뷰
   - PR 템플릿 사용
   - 코드 리뷰 체크리스트 작성
        """)


def main():
    """메인 함수"""
    checker = CodeStyleChecker("backend")
    checker.check_all()
    
    print("\n" + "=" * 80)
    print("점검 완료!")
    print("=" * 80)


if __name__ == "__main__":
    main()
