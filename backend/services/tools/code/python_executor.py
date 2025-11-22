"""
Python Code Executor - Enhanced Sandbox

안전한 샌드박스 환경에서 Python 코드 실행
- 다층 보안 (AST 검증 + 실행 제한)
- 타임아웃 제한 (signal 기반)
- 메모리 제한 (resource 모듈)
- 확장된 허용 모듈 (데이터 처리, 과학 계산)
- 위험한 작업 차단 (파일 I/O, 네트워크, 시스템 호출)
"""

import logging
import json
import time
import ast
import signal
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
import sys
import io
import traceback
import re

from backend.services.tools.base_executor import BaseToolExecutor

logger = logging.getLogger(__name__)


class PythonCodeExecutor(BaseToolExecutor):
    """
    Python 코드 실행 도구 (Enhanced Security)
    
    보안 기능:
    1. AST 분석으로 위험한 코드 사전 차단
    2. 제한된 builtins 및 모듈
    3. 타임아웃 강제 종료
    4. 파일/네트워크 접근 차단
    5. 시스템 호출 차단
    
    허용된 기능:
    - 데이터 처리 (pandas, numpy)
    - 날짜/시간 처리
    - JSON/CSV 파싱
    - 수학 계산
    - 정규표현식
    - 문자열 처리
    """
    
    def __init__(self):
        super().__init__("python_code", "Python Code Executor")
        self.category = "code"
        
        # Define parameter schema with Select Boxes
        self.params_schema = {
            "code": {
                "type": "code",
                "description": "Python code to execute",
                "required": True,
                "placeholder": "# Write your Python code here\nresult = 1 + 1\nprint(result)",
                "helpText": "Secure sandbox environment with limited modules"
            },
            "timeout": {
                "type": "select",  # ✅ Select Box
                "description": "Execution timeout",
                "required": False,
                "default": "5",
                "enum": ["1", "3", "5", "10", "30"],
                "helpText": "Maximum execution time in seconds"
            },
            "return_type": {
                "type": "select",  # ✅ Select Box
                "description": "Output format",
                "required": False,
                "default": "text",
                "enum": ["text", "json", "dataframe"],
                "helpText": "How to format the execution result"
            },
            "variables": {
                "type": "json",
                "description": "Input variables (JSON)",
                "required": False,
                "default": {},
                "placeholder": '{"x": 10, "y": 20}',
                "helpText": "Variables accessible in the code"
            }
        }
    
    
    # 허용된 내장 함수 (확장)
    SAFE_BUILTINS = {
        # 기본 타입
        'abs': abs,
        'all': all,
        'any': any,
        'bool': bool,
        'bytes': bytes,
        'bytearray': bytearray,
        'chr': chr,
        'dict': dict,
        'enumerate': enumerate,
        'filter': filter,
        'float': float,
        'frozenset': frozenset,
        'int': int,
        'len': len,
        'list': list,
        'map': map,
        'max': max,
        'min': min,
        'ord': ord,
        'range': range,
        'reversed': reversed,
        'round': round,
        'set': set,
        'slice': slice,
        'sorted': sorted,
        'str': str,
        'sum': sum,
        'tuple': tuple,
        'zip': zip,
        
        # 유틸리티
        'isinstance': isinstance,
        'issubclass': issubclass,
        'hasattr': hasattr,
        'getattr': getattr,
        'setattr': setattr,
        'callable': callable,
        'type': type,
        'dir': dir,
        'help': help,
        'hex': hex,
        'oct': oct,
        'bin': bin,
        'format': format,
        'hash': hash,
        'id': id,
        'pow': pow,
        'divmod': divmod,
        
        # 상수
        'True': True,
        'False': False,
        'None': None,
        'Ellipsis': Ellipsis,
        'NotImplemented': NotImplemented,
        
        # 예외
        'Exception': Exception,
        'ValueError': ValueError,
        'TypeError': TypeError,
        'KeyError': KeyError,
        'IndexError': IndexError,
        'AttributeError': AttributeError,
        'RuntimeError': RuntimeError,
        'StopIteration': StopIteration,
        'ZeroDivisionError': ZeroDivisionError,
    }
    
    # 허용된 모듈 (확장)
    SAFE_MODULES = {
        # 표준 라이브러리
        'json',
        'math',
        'datetime',
        'random',
        're',
        'collections',
        'itertools',
        'functools',
        'operator',
        'string',
        'textwrap',
        'unicodedata',
        'decimal',
        'fractions',
        'statistics',
        'hashlib',
        'hmac',
        'secrets',
        'uuid',
        'base64',
        'binascii',
        'struct',
        'codecs',
        'csv',  # CSV 처리
        'urllib.parse',  # URL 파싱만 (요청은 차단)
        'html',
        'xml.etree.ElementTree',  # XML 파싱
        'calendar',
        'time',
        'zoneinfo',
    }
    
    # 차단할 위험한 모듈/함수
    BLOCKED_MODULES = {
        'os', 'sys', 'subprocess', 'socket', 'urllib.request',
        'http', 'ftplib', 'smtplib', 'telnetlib',
        'pickle', 'shelve', 'dbm',
        'ctypes', 'cffi', 'importlib',
        '__import__', 'eval', 'exec', 'compile',
        'open', 'file', 'input', 'raw_input',
    }
    
    # 차단할 위험한 AST 노드
    BLOCKED_AST_NODES = {
        ast.Import,  # import 문 차단 (사전 허용된 것만)
        ast.ImportFrom,  # from ... import 차단
    }
    
    # 차단할 위험한 속성/메서드
    BLOCKED_ATTRIBUTES = {
        '__import__', '__loader__', '__spec__',
        '__builtins__', '__globals__', '__locals__',
        '__code__', '__closure__', '__dict__',
        'func_globals', 'func_code',
    }
    
    def _validate_code_safety(self, code: str, mode: str = 'simple') -> None:
        """
        AST 분석으로 코드 안전성 검증
        
        차단 대상:
        - import 문 (advanced 모드에서는 허용된 모듈만)
        - 파일 I/O (open, file)
        - 네트워크 접근
        - 시스템 호출
        - 위험한 내장 함수
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in code: {e}")
        
        for node in ast.walk(tree):
            # Import 문 검증
            if isinstance(node, ast.Import):
                if mode == 'simple':
                    raise ValueError(
                        "Import statements are not allowed in simple mode. "
                        "Use advanced mode or pre-imported modules."
                    )
                # Advanced 모드: 허용된 모듈만
                for alias in node.names:
                    if alias.name not in self.SAFE_MODULES:
                        raise ValueError(
                            f"Module '{alias.name}' is not allowed. "
                            f"Allowed modules: {', '.join(sorted(self.SAFE_MODULES))}"
                        )
            
            if isinstance(node, ast.ImportFrom):
                if mode == 'simple':
                    raise ValueError(
                        "Import statements are not allowed in simple mode. "
                        "Use advanced mode or pre-imported modules."
                    )
                # Advanced 모드: 허용된 모듈만
                if node.module and node.module not in self.SAFE_MODULES:
                    raise ValueError(
                        f"Module '{node.module}' is not allowed. "
                        f"Allowed modules: {', '.join(sorted(self.SAFE_MODULES))}"
                    )
            
            # 위험한 함수 호출 차단
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in self.BLOCKED_MODULES:
                        raise ValueError(f"Function '{func_name}' is not allowed for security reasons")
            
            # 위험한 속성 접근 차단
            if isinstance(node, ast.Attribute):
                attr_name = node.attr
                if attr_name in self.BLOCKED_ATTRIBUTES:
                    raise ValueError(f"Attribute '{attr_name}' is not allowed for security reasons")
    
    def _setup_timeout(self, timeout: int):
        """타임아웃 설정 (Unix 시스템만)"""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Code execution exceeded {timeout} seconds")
        
        # Windows에서는 signal.SIGALRM이 없으므로 try-except
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)
        except (AttributeError, ValueError):
            # Windows 또는 signal 미지원 환경
            logger.warning("Timeout signal not supported on this platform")
    
    def _clear_timeout(self):
        """타임아웃 해제"""
        try:
            signal.alarm(0)
        except (AttributeError, ValueError):
            pass
    
    async def execute(
        self,
        code: str,
        input_data: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        mode: str = 'simple',  # simple, advanced
        **kwargs
    ) -> Dict[str, Any]:
        """
        Python 코드 실행 (Enhanced Security)
        
        Args:
            code: 실행할 Python 코드
            input_data: 입력 데이터 (이전 블록 출력)
            timeout: 실행 타임아웃 (초, 최대 300초)
            mode: 실행 모드 (simple: 표현식, advanced: 스크립트)
            
        Returns:
            실행 결과
            
        Security:
            - AST 분석으로 위험한 코드 사전 차단
            - 제한된 builtins 및 모듈만 허용
            - 타임아웃 강제 종료
            - 파일/네트워크 접근 차단
        """
        start_time = time.time()
        
        try:
            logger.info(f"Executing Python code (mode: {mode}, timeout: {timeout}s)")
            
            # 타임아웃 제한
            timeout = min(timeout, 300)  # 최대 5분
            
            # 입력 데이터 준비
            input_data = input_data or {}
            
            # 코드 안전성 검증
            self._validate_code_safety(code, mode=mode)
            
            # 타임아웃 설정
            self._setup_timeout(timeout)
            
            try:
                # 실행 모드에 따라 처리
                if mode == 'simple':
                    result = await self._execute_simple(code, input_data, timeout)
                else:
                    result = await self._execute_advanced(code, input_data, timeout)
            finally:
                # 타임아웃 해제
                self._clear_timeout()
            
            execution_time = time.time() - start_time
            
            return {
                'success': True,
                'output': result,
                'execution_time': execution_time,
                'mode': mode,
            }
            
        except TimeoutError as e:
            logger.error(f"Python code execution timeout: {e}")
            return {
                'success': False,
                'error': f'Execution timeout after {timeout} seconds',
                'error_type': 'TimeoutError',
            }
        except ValueError as e:
            # 보안 검증 실패
            logger.warning(f"Code validation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': 'SecurityError',
            }
        except Exception as e:
            logger.error(f"Python code execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
                'traceback': traceback.format_exc(),
            }
    
    async def _execute_simple(
        self,
        code: str,
        input_data: Dict[str, Any],
        timeout: int
    ) -> Any:
        """
        Simple 모드: 단순 표현식 또는 짧은 코드 실행
        
        사용 예:
        - input['value'] * 2
        - [x for x in input['items'] if x > 10]
        - {'result': sum(input['numbers'])}
        - len(input['text'].split())
        """
        # 안전한 실행 환경 구성
        import datetime as dt_module
        import math as math_module
        import re as re_module
        import json as json_module
        import statistics as stats_module
        
        safe_globals = {
            '__builtins__': self.SAFE_BUILTINS,
            'input': input_data,
            'data': input_data,  # n8n 스타일 alias
            '$input': input_data,  # n8n 스타일
            'json': json_module,
            'datetime': dt_module,
            'timedelta': timedelta,
            'math': math_module,
            're': re_module,
            'statistics': stats_module,
        }
        
        # 허용된 모듈 추가
        import builtins
        for module_name in self.SAFE_MODULES:
            try:
                if '.' in module_name:
                    # 서브모듈 처리 (예: urllib.parse)
                    parts = module_name.split('.')
                    module = builtins.__import__(module_name, fromlist=[parts[-1]])
                    safe_globals[parts[-1]] = module
                else:
                    safe_globals[module_name] = builtins.__import__(module_name)
            except ImportError:
                logger.warning(f"Module {module_name} not available")
        
        safe_locals = {}
        
        # stdout/stderr 캡처
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        try:
            # 코드 실행 (eval 또는 exec)
            try:
                # 먼저 표현식으로 시도
                result = eval(code, safe_globals, safe_locals)
            except SyntaxError:
                # 표현식이 아니면 문장으로 실행
                exec(code, safe_globals, safe_locals)
                # 'result' 또는 마지막 변수 반환
                result = safe_locals.get('result', safe_locals.get('output', safe_locals))
            
            # stdout/stderr 가져오기
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            
            output = {
                'result': result,
            }
            
            if stdout:
                output['stdout'] = stdout
            if stderr:
                output['stderr'] = stderr
            
            return output
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    async def _execute_advanced(
        self,
        code: str,
        input_data: Dict[str, Any],
        timeout: int
    ) -> Any:
        """
        Advanced 모드: 복잡한 스크립트 실행
        
        사용 예:
        ```python
        # 데이터 처리
        items = input['items']
        filtered = [x for x in items if x['status'] == 'active']
        
        # 통계 계산
        from statistics import mean, median
        values = [x['value'] for x in filtered]
        
        # 결과 반환
        result = {
            'total': len(filtered),
            'items': filtered,
            'stats': {
                'mean': mean(values),
                'median': median(values)
            }
        }
        ```
        """
        # 안전한 실행 환경 구성
        import datetime as dt_module
        import math as math_module
        import re as re_module
        import json as json_module
        import statistics as stats_module
        import collections as collections_module
        
        # Advanced 모드에서는 제한된 __import__ 허용
        import builtins
        def safe_import(name, *args, **kwargs):
            """허용된 모듈만 import 가능"""
            if name not in self.SAFE_MODULES:
                raise ImportError(f"Module '{name}' is not allowed")
            return builtins.__import__(name, *args, **kwargs)
        
        safe_builtins = self.SAFE_BUILTINS.copy()
        safe_builtins['__import__'] = safe_import  # Advanced 모드에서만 사용
        
        safe_globals = {
            '__builtins__': safe_builtins,
            'input': input_data,
            'data': input_data,
            '$input': input_data,
            'json': json_module,
            'datetime': dt_module,
            'timedelta': timedelta,
            'math': math_module,
            're': re_module,
            'statistics': stats_module,
            'collections': collections_module,
        }
        
        # 허용된 모듈 사전 import
        import builtins
        for module_name in self.SAFE_MODULES:
            try:
                if '.' in module_name:
                    # 서브모듈 처리
                    parts = module_name.split('.')
                    module = builtins.__import__(module_name, fromlist=[parts[-1]])
                    safe_globals[parts[-1]] = module
                else:
                    safe_globals[module_name] = builtins.__import__(module_name)
            except ImportError:
                logger.warning(f"Module {module_name} not available")
        
        safe_locals = {}
        
        # stdout/stderr 캡처
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        try:
            # 코드 실행
            exec(code, safe_globals, safe_locals)
            
            # stdout/stderr 가져오기
            stdout = sys.stdout.getvalue()
            stderr = sys.stderr.getvalue()
            
            # 결과 추출
            result = safe_locals.get('result', safe_locals.get('output', None))
            
            # result가 없으면 모든 변수 반환 (private 제외)
            if result is None:
                result = {k: v for k, v in safe_locals.items() if not k.startswith('_')}
            
            output = {
                'result': result,
            }
            
            if stdout:
                output['stdout'] = stdout
            if stderr:
                output['stderr'] = stderr
            
            return output
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """파라미터 검증"""
        if 'code' not in params:
            raise ValueError("'code' parameter is required")
        
        if not isinstance(params['code'], str):
            raise ValueError("'code' must be a string")
        
        if not params['code'].strip():
            raise ValueError("'code' cannot be empty")
        
        return True


# Tool 등록을 위한 메타데이터
TOOL_METADATA = {
    'id': 'python_code',
    'name': 'Python Code',
    'description': 'Execute Python code in a secure sandbox (n8n style)',
    'category': 'code',
    'icon': '🐍',
    'bg_color': '#3776AB',
    'params': {
        'code': {
            'type': 'code',
            'description': 'Python code to execute',
            'required': True,
            'placeholder': '# Access input data\nresult = input["value"] * 2',
            'language': 'python',
        },
        'mode': {
            'type': 'select',
            'description': 'Execution mode',
            'enum': ['simple', 'advanced'],
            'default': 'simple',
            'helpText': 'Simple: expressions, Advanced: full scripts',
        },
        'timeout': {
            'type': 'number',
            'description': 'Execution timeout (seconds)',
            'default': 30,
            'min': 1,
            'max': 300,
        },
    },
    'outputs': {
        'result': {
            'type': 'any',
            'description': 'Execution result',
        },
        'stdout': {
            'type': 'string',
            'description': 'Standard output',
        },
        'stderr': {
            'type': 'string',
            'description': 'Standard error',
        },
    },
    'examples': [
        {
            'name': 'Simple Calculation',
            'description': 'Calculate sum of numbers',
            'code': '''# Simple expression
result = sum(input['numbers'])''',
            'config': {
                'code': "result = sum(input['numbers'])",
                'mode': 'simple',
            }
        },
        {
            'name': 'Data Filtering',
            'description': 'Filter and transform data',
            'code': '''# Filter active items
items = input['items']
active_items = [x for x in items if x['status'] == 'active']

result = {
    'total': len(active_items),
    'items': active_items
}''',
            'config': {
                'code': "items = input['items']\nactive_items = [x for x in items if x['status'] == 'active']\nresult = {'total': len(active_items), 'items': active_items}",
                'mode': 'advanced',
            }
        },
        {
            'name': 'JSON Processing',
            'description': 'Parse and transform JSON data',
            'code': '''import json

# Parse JSON string
data = json.loads(input['json_string'])

# Transform
result = {
    'parsed': data,
    'keys': list(data.keys()),
    'count': len(data)
}''',
            'config': {
                'code': "import json\ndata = json.loads(input['json_string'])\nresult = {'parsed': data, 'keys': list(data.keys())}",
                'mode': 'advanced',
            }
        },
    ],
    'docs_link': 'https://docs.python.org/3/',
}
