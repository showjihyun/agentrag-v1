"""
Code Analyzer API endpoints for Enhanced Code Block.
Phase 2: 실시간 에러 분석
"""
import ast
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

router = APIRouter(prefix="/api/workflow", tags=["code-analyzer"])


# ============== Request/Response Models ==============

class AnalyzeCodeRequest(BaseModel):
    """코드 분석 요청."""
    code: str
    language: str = "python"


class CodeError(BaseModel):
    """코드 에러."""
    line: int
    column: Optional[int] = None
    severity: str = "error"  # error, warning, info
    message: str
    code: Optional[str] = None
    source: str = "analyzer"


class AnalyzeCodeResponse(BaseModel):
    """코드 분석 응답."""
    errors: List[CodeError] = Field(default_factory=list)
    warnings: List[CodeError] = Field(default_factory=list)
    info: List[CodeError] = Field(default_factory=list)


# ============== Python Analyzer ==============

class PythonAnalyzer:
    """Python 코드 분석기."""
    
    # 일반적인 코딩 패턴 경고
    WARNING_PATTERNS = [
        (r'except\s*:', "Bare except clause - consider catching specific exceptions", "W001"),
        (r'import\s+\*', "Wildcard import - consider importing specific names", "W002"),
        (r'==\s*None', "Use 'is None' instead of '== None'", "W003"),
        (r'!=\s*None', "Use 'is not None' instead of '!= None'", "W004"),
        (r'type\s*\(\s*\w+\s*\)\s*==', "Use isinstance() instead of type() comparison", "W005"),
        (r'print\s*\(', "Print statement found - consider using logging", "W006"),
        (r'TODO|FIXME|XXX|HACK', "TODO/FIXME comment found", "W007"),
    ]
    
    # 보안 관련 경고
    SECURITY_PATTERNS = [
        (r'eval\s*\(', "eval() is dangerous - avoid if possible", "S001"),
        (r'exec\s*\(', "exec() is dangerous - avoid if possible", "S002"),
        (r'__import__\s*\(', "Dynamic import - potential security risk", "S003"),
        (r'pickle\.loads?\s*\(', "Pickle can execute arbitrary code", "S004"),
        (r'subprocess\..*shell\s*=\s*True', "Shell=True is a security risk", "S005"),
    ]
    
    def analyze(self, code: str) -> List[CodeError]:
        """Python 코드 분석."""
        errors = []
        
        # 1. 구문 분석 (Syntax check)
        syntax_errors = self._check_syntax(code)
        errors.extend(syntax_errors)
        
        # 구문 에러가 있으면 추가 분석 스킵
        if syntax_errors:
            return errors
        
        # 2. AST 기반 분석
        ast_errors = self._analyze_ast(code)
        errors.extend(ast_errors)
        
        # 3. 패턴 기반 경고
        pattern_warnings = self._check_patterns(code)
        errors.extend(pattern_warnings)
        
        # 4. 보안 검사
        security_warnings = self._check_security(code)
        errors.extend(security_warnings)
        
        return errors
    
    def _check_syntax(self, code: str) -> List[CodeError]:
        """구문 검사."""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(CodeError(
                line=e.lineno or 1,
                column=e.offset,
                severity="error",
                message=f"Syntax Error: {e.msg}",
                code="E001",
                source="syntax"
            ))
        return errors
    
    def _analyze_ast(self, code: str) -> List[CodeError]:
        """AST 기반 분석."""
        errors = []
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 미사용 변수 감지 (간단한 버전)
                if isinstance(node, ast.Name) and node.id.startswith('_'):
                    if isinstance(node.ctx, ast.Store):
                        errors.append(CodeError(
                            line=node.lineno,
                            column=node.col_offset,
                            severity="info",
                            message=f"Variable '{node.id}' starts with underscore",
                            code="I001",
                            source="ast"
                        ))
                
                # 빈 함수 감지
                if isinstance(node, ast.FunctionDef):
                    if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                        errors.append(CodeError(
                            line=node.lineno,
                            severity="warning",
                            message=f"Empty function '{node.name}'",
                            code="W008",
                            source="ast"
                        ))
                    
                    # 너무 많은 인자
                    if len(node.args.args) > 7:
                        errors.append(CodeError(
                            line=node.lineno,
                            severity="warning",
                            message=f"Function '{node.name}' has too many arguments ({len(node.args.args)})",
                            code="W009",
                            source="ast"
                        ))
                
                # 너무 깊은 중첩
                # (간단한 구현 - 실제로는 더 정교한 분석 필요)
                
        except Exception:
            pass
        
        return errors
    
    def _check_patterns(self, code: str) -> List[CodeError]:
        """패턴 기반 경고."""
        errors = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, message, error_code in self.WARNING_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(CodeError(
                        line=i,
                        severity="warning",
                        message=message,
                        code=error_code,
                        source="pattern"
                    ))
        
        return errors
    
    def _check_security(self, code: str) -> List[CodeError]:
        """보안 검사."""
        errors = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, message, error_code in self.SECURITY_PATTERNS:
                if re.search(pattern, line):
                    errors.append(CodeError(
                        line=i,
                        severity="warning",
                        message=f"Security: {message}",
                        code=error_code,
                        source="security"
                    ))
        
        return errors


# ============== JavaScript Analyzer ==============

class JavaScriptAnalyzer:
    """JavaScript 코드 분석기 (기본)."""
    
    WARNING_PATTERNS = [
        (r'var\s+', "Use 'let' or 'const' instead of 'var'", "W101"),
        (r'==(?!=)', "Use '===' instead of '=='", "W102"),
        (r'!=(?!=)', "Use '!==' instead of '!='", "W103"),
        (r'console\.log', "console.log found - remove in production", "W104"),
        (r'debugger', "debugger statement found", "W105"),
        (r'eval\s*\(', "eval() is dangerous", "S101"),
    ]
    
    def analyze(self, code: str) -> List[CodeError]:
        """JavaScript 코드 분석."""
        errors = []
        lines = code.split('\n')
        
        # 기본 구문 검사 (간단한 괄호 매칭)
        open_braces = 0
        open_parens = 0
        open_brackets = 0
        
        for i, line in enumerate(lines, 1):
            # 문자열 제외하고 카운트
            clean_line = re.sub(r'"[^"]*"|\'[^\']*\'|`[^`]*`', '', line)
            open_braces += clean_line.count('{') - clean_line.count('}')
            open_parens += clean_line.count('(') - clean_line.count(')')
            open_brackets += clean_line.count('[') - clean_line.count(']')
            
            # 패턴 검사
            for pattern, message, error_code in self.WARNING_PATTERNS:
                if re.search(pattern, line):
                    errors.append(CodeError(
                        line=i,
                        severity="warning",
                        message=message,
                        code=error_code,
                        source="pattern"
                    ))
        
        # 괄호 불일치 검사
        if open_braces != 0:
            errors.append(CodeError(
                line=len(lines),
                severity="error",
                message="Unmatched braces {}",
                code="E101",
                source="syntax"
            ))
        if open_parens != 0:
            errors.append(CodeError(
                line=len(lines),
                severity="error",
                message="Unmatched parentheses ()",
                code="E102",
                source="syntax"
            ))
        
        return errors


# ============== SQL Analyzer ==============

class SQLAnalyzer:
    """SQL 쿼리 분석기."""
    
    WARNING_PATTERNS = [
        (r'SELECT\s+\*', "Avoid SELECT * - specify columns explicitly", "W201"),
        (r'DELETE\s+FROM\s+\w+\s*$', "DELETE without WHERE clause", "W202"),
        (r'UPDATE\s+\w+\s+SET.*(?!WHERE)', "UPDATE without WHERE clause", "W203"),
        (r'DROP\s+TABLE', "DROP TABLE statement - use with caution", "W204"),
        (r'TRUNCATE', "TRUNCATE statement - use with caution", "W205"),
    ]
    
    DANGEROUS_PATTERNS = [
        (r';\s*DROP', "Potential SQL injection pattern", "S201"),
        (r';\s*DELETE', "Potential SQL injection pattern", "S202"),
        (r'--\s*$', "SQL comment at end of line", "S203"),
    ]
    
    def analyze(self, code: str) -> List[CodeError]:
        """SQL 쿼리 분석."""
        errors = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, message, error_code in self.WARNING_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(CodeError(
                        line=i,
                        severity="warning",
                        message=message,
                        code=error_code,
                        source="pattern"
                    ))
            
            for pattern, message, error_code in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    errors.append(CodeError(
                        line=i,
                        severity="error",
                        message=f"Security: {message}",
                        code=error_code,
                        source="security"
                    ))
        
        return errors


# ============== Analyzer Factory ==============

def get_analyzer(language: str):
    """언어별 분석기 반환."""
    analyzers = {
        'python': PythonAnalyzer(),
        'javascript': JavaScriptAnalyzer(),
        'typescript': JavaScriptAnalyzer(),  # TypeScript도 JS 분석기 사용
        'sql': SQLAnalyzer(),
    }
    return analyzers.get(language, PythonAnalyzer())


# ============== API Endpoints ==============

@router.post("/analyze-code", response_model=AnalyzeCodeResponse)
async def analyze_code(
    request: AnalyzeCodeRequest,
    current_user: User = Depends(get_current_user),
) -> AnalyzeCodeResponse:
    """코드 분석 및 린팅."""
    analyzer = get_analyzer(request.language)
    all_errors = analyzer.analyze(request.code)
    
    # 심각도별 분류
    errors = [e for e in all_errors if e.severity == "error"]
    warnings = [e for e in all_errors if e.severity == "warning"]
    info = [e for e in all_errors if e.severity == "info"]
    
    return AnalyzeCodeResponse(
        errors=errors,
        warnings=warnings,
        info=info
    )
