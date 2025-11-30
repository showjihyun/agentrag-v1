"""
Code execution and AI code generation API endpoints.
Enhanced Code Block 기능을 위한 API.
"""
import time
import uuid
import asyncio
import traceback
from typing import Any, Dict, List, Optional
from datetime import datetime
from io import StringIO
import sys
import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.auth_dependencies import get_current_user
from backend.db.models.user import User
from backend.db.database import get_db
from backend.models.error import ErrorResponse
from backend.config import settings

router = APIRouter(prefix="/api/workflow", tags=["code-execution"])


# ============== Request/Response Models ==============

class CodeTestRequest(BaseModel):
    """코드 테스트 실행 요청."""
    code: str = Field(..., description="실행할 코드")
    language: str = Field(default="python", description="프로그래밍 언어")
    input: Any = Field(default=None, description="입력 데이터")
    context: Dict[str, Any] = Field(default_factory=dict, description="컨텍스트 데이터")
    timeout: int = Field(default=30, ge=1, le=300, description="타임아웃 (초)")
    allow_imports: bool = Field(default=True, description="import 허용 여부")


class CodeTestResponse(BaseModel):
    """코드 테스트 실행 응답."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    executionTime: Optional[int] = None  # milliseconds
    logs: List[str] = Field(default_factory=list)


class CodeGenerateRequest(BaseModel):
    """AI 코드 생성 요청."""
    prompt: str = Field(..., description="코드 생성 프롬프트")
    language: str = Field(default="python", description="프로그래밍 언어")
    context: str = Field(default="workflow_node", description="코드 컨텍스트")


class CodeGenerateResponse(BaseModel):
    """AI 코드 생성 응답."""
    code: Optional[str] = None
    error: Optional[str] = None
    explanation: Optional[str] = None


# ============== Safe Code Execution ==============

# 허용된 Python 모듈
ALLOWED_MODULES = {
    'json', 'datetime', 'math', 'random', 're', 'collections',
    'itertools', 'functools', 'operator', 'string', 'textwrap',
    'csv', 'io', 'base64', 'hashlib', 'hmac', 'urllib.parse',
    'decimal', 'fractions', 'statistics', 'copy', 'pprint',
}

# 추가 허용 모듈 (allow_imports=True일 때)
EXTENDED_MODULES = {
    'requests', 'pandas', 'numpy', 'httpx', 'aiohttp',
}

# 금지된 내장 함수
BLOCKED_BUILTINS = {
    'exec', 'eval', 'compile', '__import__', 'open', 'input',
    'breakpoint', 'help', 'license', 'credits', 'copyright',
}


class SafeExecutionEnvironment:
    """안전한 코드 실행 환경."""
    
    def __init__(self, allow_imports: bool = True, timeout: int = 30):
        self.allow_imports = allow_imports
        self.timeout = timeout
        self.logs: List[str] = []
    
    def _create_safe_globals(self, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """안전한 전역 변수 생성."""
        import builtins
        
        # 안전한 내장 함수만 포함
        safe_builtins = {
            name: getattr(builtins, name)
            for name in dir(builtins)
            if not name.startswith('_') and name not in BLOCKED_BUILTINS
        }
        
        # 커스텀 print 함수 (로그 캡처)
        def safe_print(*args, **kwargs):
            output = StringIO()
            print(*args, file=output, **kwargs)
            self.logs.append(output.getvalue().rstrip())
        
        safe_builtins['print'] = safe_print
        
        # 안전한 import 함수
        def safe_import(name, *args, **kwargs):
            allowed = ALLOWED_MODULES.copy()
            if self.allow_imports:
                allowed.update(EXTENDED_MODULES)
            
            base_module = name.split('.')[0]
            if base_module not in allowed:
                raise ImportError(f"Module '{name}' is not allowed. Allowed modules: {sorted(allowed)}")
            
            return __import__(name, *args, **kwargs)
        
        safe_builtins['__import__'] = safe_import
        
        # 전역 변수 설정
        globals_dict = {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            'input': input_data,
            'context': context,
        }
        
        # 기본 모듈 미리 import
        try:
            import json as json_module
            import datetime as datetime_module
            import math as math_module
            import random as random_module
            import re as re_module
            
            globals_dict['json'] = json_module
            globals_dict['datetime'] = datetime_module
            globals_dict['math'] = math_module
            globals_dict['random'] = random_module
            globals_dict['re'] = re_module
            
            if self.allow_imports:
                try:
                    import requests
                    globals_dict['requests'] = requests
                except ImportError:
                    pass
                
                try:
                    import pandas as pd
                    globals_dict['pandas'] = pd
                    globals_dict['pd'] = pd
                except ImportError:
                    pass
                
                try:
                    import numpy as np
                    globals_dict['numpy'] = np
                    globals_dict['np'] = np
                except ImportError:
                    pass
        except Exception:
            pass
        
        return globals_dict
    
    async def execute_python(self, code: str, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Python 코드 실행."""
        self.logs = []
        start_time = time.time()
        
        try:
            # 전역 변수 생성
            globals_dict = self._create_safe_globals(input_data, context)
            locals_dict = {}
            
            # 코드 컴파일 (문법 검사)
            try:
                compiled = compile(code, '<user_code>', 'exec')
            except SyntaxError as e:
                return {
                    'success': False,
                    'error': f"Syntax Error at line {e.lineno}: {e.msg}",
                    'executionTime': int((time.time() - start_time) * 1000),
                    'logs': self.logs,
                }
            
            # 타임아웃과 함께 실행
            def run_code():
                exec(compiled, globals_dict, locals_dict)
                return locals_dict.get('__return__', globals_dict.get('__return__'))
            
            # asyncio를 사용한 타임아웃 실행
            loop = asyncio.get_event_loop()
            try:
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, run_code),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                return {
                    'success': False,
                    'error': f"Execution timeout ({self.timeout}s exceeded)",
                    'executionTime': int((time.time() - start_time) * 1000),
                    'logs': self.logs,
                }
            
            # return 문 결과 확인
            if result is None and 'return' in code:
                # 마지막 표현식 결과 찾기
                for key in ['result', 'output', 'data']:
                    if key in locals_dict:
                        result = locals_dict[key]
                        break
            
            execution_time = int((time.time() - start_time) * 1000)
            
            return {
                'success': True,
                'output': result,
                'executionTime': execution_time,
                'logs': self.logs,
            }
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_trace = traceback.format_exc()
            
            # 사용자 친화적 에러 메시지
            error_lines = error_trace.split('\n')
            user_error = str(e)
            
            # 라인 번호 추출 시도
            for line in error_lines:
                if 'line' in line.lower() and '<user_code>' in line:
                    user_error = f"{line.strip()}\n{e}"
                    break
            
            return {
                'success': False,
                'error': user_error,
                'executionTime': execution_time,
                'logs': self.logs,
            }
    
    async def execute_javascript(self, code: str, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """JavaScript 코드 실행 (제한적 지원)."""
        # JavaScript 실행은 보안상 서버에서 직접 실행하지 않음
        # 대신 구문 검사만 수행
        return {
            'success': False,
            'error': "JavaScript execution is not supported on server. Please test in browser console.",
            'executionTime': 0,
            'logs': [],
        }
    
    async def execute_sql(self, code: str, input_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """SQL 쿼리 검증 (실행하지 않음)."""
        # SQL은 실제 실행하지 않고 구문만 검증
        import re
        
        # 위험한 키워드 검사
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        code_upper = code.upper()
        
        warnings = []
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', code_upper):
                warnings.append(f"Warning: Query contains '{keyword}' statement")
        
        return {
            'success': True,
            'output': {
                'validated': True,
                'warnings': warnings,
                'message': 'SQL query validated (not executed)',
            },
            'executionTime': 0,
            'logs': warnings,
        }


# ============== API Endpoints ==============

@router.post(
    "/test-code",
    response_model=CodeTestResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def test_code(
    request: CodeTestRequest,
    current_user: User = Depends(get_current_user),
) -> CodeTestResponse:
    """
    코드 테스트 실행.
    
    안전한 샌드박스 환경에서 코드를 실행하고 결과를 반환합니다.
    """
    if not request.code.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code cannot be empty",
        )
    
    executor = SafeExecutionEnvironment(
        allow_imports=request.allow_imports,
        timeout=request.timeout,
    )
    
    if request.language == 'python':
        result = await executor.execute_python(request.code, request.input, request.context)
    elif request.language in ('javascript', 'typescript'):
        result = await executor.execute_javascript(request.code, request.input, request.context)
    elif request.language == 'sql':
        result = await executor.execute_sql(request.code, request.input, request.context)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language: {request.language}",
        )
    
    return CodeTestResponse(**result)


@router.post(
    "/generate-code",
    response_model=CodeGenerateResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def generate_code(
    request: CodeGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> CodeGenerateResponse:
    """
    AI를 사용한 코드 생성.
    
    자연어 프롬프트를 기반으로 코드를 생성합니다.
    """
    if not request.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt cannot be empty",
        )
    
    try:
        from backend.services.llm_manager import LLMManager
        
        llm_manager = LLMManager()
        
        # 언어별 시스템 프롬프트
        language_hints = {
            'python': """You are a Python code generator for workflow automation.
Generate clean, efficient Python code that:
- Uses the 'input' variable for input data
- Uses the 'context' variable for workflow context
- Returns a dictionary with 'output' and 'status' keys
- Handles errors gracefully
- Uses only allowed modules: json, datetime, math, random, re, requests, pandas, numpy""",
            
            'javascript': """You are a JavaScript code generator for workflow automation.
Generate clean, efficient JavaScript code that:
- Uses the 'input' variable for input data
- Uses the 'context' variable for workflow context
- Returns an object with 'output' and 'status' properties
- Handles errors with try-catch
- Uses modern ES6+ syntax""",
            
            'sql': """You are a SQL query generator.
Generate efficient SQL queries that:
- Use parameterized values with {{input.field}} syntax
- Include appropriate WHERE clauses
- Use JOINs efficiently
- Include LIMIT for safety""",
        }
        
        system_prompt = language_hints.get(request.language, language_hints['python'])
        
        user_prompt = f"""Generate {request.language} code for the following task:

{request.prompt}

Context: This code will run in a workflow node with access to 'input' (previous node output) and 'context' (workflow metadata).

Return ONLY the code without any explanation or markdown formatting."""
        
        # LLM 호출
        response = await llm_manager.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=2000,
            temperature=0.3,
        )
        
        # 코드 추출 (마크다운 코드 블록 제거)
        code = response.strip()
        if code.startswith('```'):
            lines = code.split('\n')
            # 첫 줄과 마지막 줄 제거
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            code = '\n'.join(lines)
        
        return CodeGenerateResponse(
            code=code,
            explanation=f"Generated {request.language} code for: {request.prompt[:100]}...",
        )
        
    except Exception as e:
        return CodeGenerateResponse(
            error=f"Code generation failed: {str(e)}",
        )


@router.get("/code-templates")
async def get_code_templates(
    language: str = "python",
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    언어별 코드 템플릿 목록 반환.
    """
    templates = {
        'python': {
            'basic': {
                'name': 'Basic Template',
                'description': '기본 Python 코드 템플릿',
                'code': '''def main(input_data, context):
    result = input_data
    return {"output": result, "status": "success"}

return main(input, context)''',
            },
            'dataTransform': {
                'name': 'Data Transform',
                'description': '데이터 변환 템플릿',
                'code': '''import json

def transform_data(input_data, context):
    data = input_data if isinstance(input_data, dict) else json.loads(input_data)
    
    transformed = {
        "items": [item.upper() if isinstance(item, str) else item for item in data.get("items", [])],
        "count": len(data.get("items", [])),
    }
    
    return {"output": transformed, "status": "success"}

return transform_data(input, context)''',
            },
            'apiCall': {
                'name': 'API Call',
                'description': 'HTTP API 호출 템플릿',
                'code': '''import requests

def call_api(input_data, context):
    url = input_data.get("url", "https://api.example.com/data")
    method = input_data.get("method", "GET")
    
    try:
        response = requests.request(method, url, timeout=30)
        return {"output": response.json(), "status": "success"}
    except Exception as e:
        return {"error": str(e), "status": "error"}

return call_api(input, context)''',
            },
            'dataValidation': {
                'name': 'Data Validation',
                'description': '데이터 검증 템플릿',
                'code': '''def validate_data(input_data, context):
    errors = []
    
    required_fields = ["name", "email"]
    for field in required_fields:
        if field not in input_data:
            errors.append(f"Missing: {field}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "status": "success" if not errors else "validation_failed"
    }

return validate_data(input, context)''',
            },
        },
        'javascript': {
            'basic': {
                'name': 'Basic Template',
                'description': '기본 JavaScript 코드 템플릿',
                'code': '''function main(inputData, context) {
  const result = inputData;
  return { output: result, status: "success" };
}

return main(input, context);''',
            },
            'dataTransform': {
                'name': 'Data Transform',
                'description': '데이터 변환 템플릿',
                'code': '''function transformData(inputData, context) {
  const data = typeof inputData === 'string' ? JSON.parse(inputData) : inputData;
  
  const transformed = {
    items: (data.items || []).map(item => 
      typeof item === 'string' ? item.toUpperCase() : item
    ),
    count: (data.items || []).length,
  };
  
  return { output: transformed, status: "success" };
}

return transformData(input, context);''',
            },
        },
        'sql': {
            'basic': {
                'name': 'Basic Query',
                'description': '기본 SELECT 쿼리',
                'code': '''SELECT * FROM table_name
WHERE column = '{{input.value}}'
LIMIT 100;''',
            },
            'aggregate': {
                'name': 'Aggregation',
                'description': '집계 쿼리 템플릿',
                'code': '''SELECT 
    category,
    COUNT(*) as count,
    SUM(amount) as total
FROM transactions
GROUP BY category
ORDER BY total DESC;''',
            },
        },
    }
    
    return {
        'language': language,
        'templates': templates.get(language, templates['python']),
    }
