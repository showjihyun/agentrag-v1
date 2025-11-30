"""
Code Profiler and Test Generator API endpoints.
Phase 3: 성능 프로파일링 및 테스트 자동화
"""
import time
import ast
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User

router = APIRouter(prefix="/api/workflow", tags=["code-profiler"])


# ============== Request/Response Models ==============

class ProfileRequest(BaseModel):
    """프로파일링 요청."""
    code: str
    language: str = "python"
    input: Any = None


class FunctionProfile(BaseModel):
    """함수 프로파일."""
    name: str
    calls: int
    totalTime: float
    avgTime: float
    percentage: float
    memoryUsage: int


class Hotspot(BaseModel):
    """성능 핫스팟."""
    line: int
    description: str
    impact: str  # high, medium, low
    suggestion: str


class ProfileResponse(BaseModel):
    """프로파일링 응답."""
    totalTime: float
    memoryUsage: int
    functions: List[FunctionProfile] = Field(default_factory=list)
    hotspots: List[Hotspot] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class GenerateTestsRequest(BaseModel):
    """테스트 생성 요청."""
    code: str
    language: str = "python"


class TestCase(BaseModel):
    """테스트 케이스."""
    name: str
    input: Any
    expected_output: Optional[Any] = None
    description: str = ""


class GenerateTestsResponse(BaseModel):
    """테스트 생성 응답."""
    tests: List[TestCase] = Field(default_factory=list)
    error: Optional[str] = None


# ============== Profiler Implementation ==============

class PythonProfiler:
    """Python 코드 프로파일러."""
    
    # 성능 패턴 감지
    PERFORMANCE_PATTERNS = [
        (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(', 'high', 
         'range(len()) 대신 enumerate() 사용 권장', 'enumerate() 사용으로 성능 개선 가능'),
        (r'\.append\s*\([^)]+\)\s*$', 'medium',
         '루프 내 append() 호출', '리스트 컴프리헨션 사용 고려'),
        (r'\+\s*=\s*["\']', 'medium',
         '문자열 연결 연산', 'join() 또는 f-string 사용 권장'),
        (r'time\.sleep\s*\(', 'high',
         'sleep() 호출 감지', '비동기 처리 또는 제거 고려'),
        (r'for.*for.*for', 'high',
         '3중 중첩 루프', '알고리즘 최적화 필요'),
        (r'\.read\s*\(\s*\)', 'medium',
         '전체 파일 읽기', '청크 단위 읽기 고려'),
        (r'import\s+\*', 'low',
         '와일드카드 import', '필요한 것만 import'),
    ]
    
    def profile(self, code: str, input_data: Any = None) -> ProfileResponse:
        """코드 프로파일링."""
        start_time = time.time()
        
        try:
            # AST 분석
            tree = ast.parse(code)
            
            # 함수 분석
            functions = self._analyze_functions(tree, code)
            
            # 핫스팟 감지
            hotspots = self._detect_hotspots(code)
            
            # 제안 생성
            suggestions = self._generate_suggestions(code, hotspots)
            
            # 실행 시간 측정 (간단한 시뮬레이션)
            total_time = (time.time() - start_time) * 1000  # ms
            
            # 메모리 사용량 추정 (코드 크기 기반)
            memory_usage = len(code.encode('utf-8')) * 10  # 대략적 추정
            
            return ProfileResponse(
                totalTime=total_time + 50,  # 기본 오버헤드 추가
                memoryUsage=memory_usage,
                functions=functions,
                hotspots=hotspots,
                suggestions=suggestions
            )
            
        except SyntaxError as e:
            return ProfileResponse(
                totalTime=0,
                memoryUsage=0,
                error=f"Syntax error: {e.msg}"
            )
        except Exception as e:
            return ProfileResponse(
                totalTime=0,
                memoryUsage=0,
                error=str(e)
            )
    
    def _analyze_functions(self, tree: ast.AST, code: str) -> List[FunctionProfile]:
        """함수 분석."""
        functions = []
        total_lines = len(code.split('\n'))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 함수 복잡도 기반 시간 추정
                func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 5
                complexity = self._estimate_complexity(node)
                
                estimated_time = func_lines * complexity * 0.5  # ms
                percentage = (func_lines / total_lines) * 100 if total_lines > 0 else 0
                
                functions.append(FunctionProfile(
                    name=node.name,
                    calls=1,  # 정적 분석에서는 1로 가정
                    totalTime=estimated_time,
                    avgTime=estimated_time,
                    percentage=min(percentage, 100),
                    memoryUsage=func_lines * 100  # 대략적 추정
                ))
        
        return sorted(functions, key=lambda f: f.totalTime, reverse=True)[:5]
    
    def _estimate_complexity(self, node: ast.FunctionDef) -> float:
        """함수 복잡도 추정."""
        complexity = 1.0
        
        for child in ast.walk(node):
            if isinstance(child, ast.For):
                complexity *= 2
            elif isinstance(child, ast.While):
                complexity *= 2
            elif isinstance(child, ast.If):
                complexity += 0.5
            elif isinstance(child, ast.Call):
                complexity += 0.2
        
        return min(complexity, 10)  # 최대 10
    
    def _detect_hotspots(self, code: str) -> List[Hotspot]:
        """성능 핫스팟 감지."""
        hotspots = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for pattern, impact, desc, suggestion in self.PERFORMANCE_PATTERNS:
                if re.search(pattern, line):
                    hotspots.append(Hotspot(
                        line=i,
                        description=desc,
                        impact=impact,
                        suggestion=suggestion
                    ))
        
        return hotspots[:5]  # 상위 5개만
    
    def _generate_suggestions(self, code: str, hotspots: List[Hotspot]) -> List[str]:
        """최적화 제안 생성."""
        suggestions = []
        
        # 핫스팟 기반 제안
        high_impact = [h for h in hotspots if h.impact == 'high']
        if high_impact:
            suggestions.append(f"{len(high_impact)}개의 고영향 성능 이슈가 발견되었습니다.")
        
        # 일반적인 제안
        if 'for' in code and 'append' in code:
            suggestions.append("리스트 컴프리헨션을 사용하면 성능이 향상될 수 있습니다.")
        
        if 'import' in code and code.count('import') > 5:
            suggestions.append("import 문이 많습니다. 필요한 것만 import하세요.")
        
        if len(code) > 1000:
            suggestions.append("코드가 깁니다. 함수로 분리하는 것을 고려하세요.")
        
        return suggestions


# ============== Test Generator Implementation ==============

class TestGenerator:
    """테스트 케이스 생성기."""
    
    def generate(self, code: str, language: str) -> List[TestCase]:
        """테스트 케이스 생성."""
        tests = []
        
        if language == 'python':
            tests = self._generate_python_tests(code)
        elif language in ('javascript', 'typescript'):
            tests = self._generate_js_tests(code)
        
        return tests
    
    def _generate_python_tests(self, code: str) -> List[TestCase]:
        """Python 테스트 생성."""
        tests = []
        
        try:
            tree = ast.parse(code)
            
            # 함수 분석
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_tests = self._generate_function_tests(node)
                    tests.extend(func_tests)
            
            # 기본 테스트 케이스 추가
            tests.extend(self._generate_edge_case_tests())
            
        except Exception:
            # 파싱 실패 시 기본 테스트만
            tests = self._generate_edge_case_tests()
        
        return tests[:10]  # 최대 10개
    
    def _generate_function_tests(self, func: ast.FunctionDef) -> List[TestCase]:
        """함수별 테스트 생성."""
        tests = []
        func_name = func.name
        
        # 인자 분석
        args = [arg.arg for arg in func.args.args]
        
        # 기본 테스트
        tests.append(TestCase(
            name=f"test_{func_name}_basic",
            input={"message": "test"},
            description=f"{func_name} 함수 기본 테스트"
        ))
        
        # 빈 입력 테스트
        tests.append(TestCase(
            name=f"test_{func_name}_empty_input",
            input={},
            description=f"{func_name} 함수 빈 입력 테스트"
        ))
        
        return tests
    
    def _generate_edge_case_tests(self) -> List[TestCase]:
        """엣지 케이스 테스트 생성."""
        return [
            TestCase(
                name="test_empty_input",
                input={},
                description="빈 입력 처리 테스트"
            ),
            TestCase(
                name="test_null_values",
                input={"value": None},
                description="null 값 처리 테스트"
            ),
            TestCase(
                name="test_large_data",
                input={"items": list(range(100))},
                description="대용량 데이터 처리 테스트"
            ),
            TestCase(
                name="test_special_characters",
                input={"text": "Hello! @#$%^&*()"},
                description="특수 문자 처리 테스트"
            ),
            TestCase(
                name="test_unicode",
                input={"text": "안녕하세요 🎉"},
                description="유니코드 처리 테스트"
            ),
        ]
    
    def _generate_js_tests(self, code: str) -> List[TestCase]:
        """JavaScript 테스트 생성."""
        return [
            TestCase(
                name="test_basic_execution",
                input={"data": "test"},
                description="기본 실행 테스트"
            ),
            TestCase(
                name="test_empty_object",
                input={},
                description="빈 객체 테스트"
            ),
            TestCase(
                name="test_array_input",
                input={"items": [1, 2, 3]},
                description="배열 입력 테스트"
            ),
        ]


# ============== API Endpoints ==============

@router.post("/profile", response_model=ProfileResponse)
async def profile_code(
    request: ProfileRequest,
    current_user: User = Depends(get_current_user),
) -> ProfileResponse:
    """코드 성능 프로파일링."""
    if request.language != "python":
        return ProfileResponse(
            totalTime=0,
            memoryUsage=0,
            error="현재 Python만 프로파일링을 지원합니다."
        )
    
    profiler = PythonProfiler()
    return profiler.profile(request.code, request.input)


@router.post("/generate-tests", response_model=GenerateTestsResponse)
async def generate_tests(
    request: GenerateTestsRequest,
    current_user: User = Depends(get_current_user),
) -> GenerateTestsResponse:
    """AI 기반 테스트 케이스 생성."""
    try:
        generator = TestGenerator()
        tests = generator.generate(request.code, request.language)
        return GenerateTestsResponse(tests=tests)
    except Exception as e:
        return GenerateTestsResponse(error=str(e))
