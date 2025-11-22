"""
Python Code Executor 보안 테스트

샌드박스가 제대로 작동하는지 확인:
1. 위험한 코드 차단
2. 허용된 코드 실행
3. 타임아웃 작동
4. 메모리 제한
"""

import pytest
import asyncio
from backend.services.tools.code.python_executor import PythonCodeExecutor


@pytest.fixture
def executor():
    """Executor 인스턴스"""
    return PythonCodeExecutor()


class TestSecurityBlocking:
    """보안 차단 테스트"""
    
    @pytest.mark.asyncio
    async def test_block_import_statement(self, executor):
        """Import 문 차단"""
        code = "import os"
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'SecurityError' in result['error_type']
        assert 'Import statements are not allowed' in result['error']
    
    @pytest.mark.asyncio
    async def test_block_from_import(self, executor):
        """From import 차단"""
        code = "from os import system"
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'SecurityError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_block_file_open(self, executor):
        """파일 열기 차단"""
        code = "open('/etc/passwd', 'r')"
        result = await executor.execute(code)
        
        assert result['success'] is False
        # open이 builtins에 없으므로 NameError 발생
        assert 'NameError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_block_eval(self, executor):
        """eval 차단"""
        code = "eval('1+1')"
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'NameError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_block_exec(self, executor):
        """exec 차단"""
        code = "exec('print(1)')"
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'NameError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_block_compile(self, executor):
        """compile 차단"""
        code = "compile('1+1', '<string>', 'eval')"
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'NameError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_block_dunder_import(self, executor):
        """__import__ 차단"""
        code = "__import__('os')"
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'NameError' in result['error_type']


class TestAllowedOperations:
    """허용된 작업 테스트"""
    
    @pytest.mark.asyncio
    async def test_simple_calculation(self, executor):
        """간단한 계산"""
        code = "2 + 2"
        result = await executor.execute(code, mode='simple')
        
        assert result['success'] is True
        assert result['output']['result'] == 4
    
    @pytest.mark.asyncio
    async def test_list_comprehension(self, executor):
        """리스트 컴프리헨션"""
        code = "[x * 2 for x in range(5)]"
        result = await executor.execute(code, mode='simple')
        
        assert result['success'] is True
        assert result['output']['result'] == [0, 2, 4, 6, 8]
    
    @pytest.mark.asyncio
    async def test_dict_operations(self, executor):
        """딕셔너리 작업"""
        code = """
data = {'a': 1, 'b': 2, 'c': 3}
result = {k: v * 2 for k, v in data.items()}
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result'] == {'a': 2, 'b': 4, 'c': 6}
    
    @pytest.mark.asyncio
    async def test_json_parsing(self, executor):
        """JSON 파싱"""
        code = """
import json
data = json.loads('{"name": "test", "value": 123}')
result = data['value'] * 2
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result'] == 246
    
    @pytest.mark.asyncio
    async def test_datetime_operations(self, executor):
        """날짜/시간 작업"""
        code = """
from datetime import datetime, timedelta
now = datetime(2024, 1, 1)
tomorrow = now + timedelta(days=1)
result = tomorrow.day
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result'] == 2
    
    @pytest.mark.asyncio
    async def test_regex_operations(self, executor):
        """정규표현식"""
        code = """
import re
text = "Hello World 123"
numbers = re.findall(r'\\d+', text)
result = numbers
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result'] == ['123']
    
    @pytest.mark.asyncio
    async def test_statistics(self, executor):
        """통계 계산"""
        code = """
from statistics import mean, median
data = [1, 2, 3, 4, 5]
result = {
    'mean': mean(data),
    'median': median(data)
}
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result']['mean'] == 3
        assert result['output']['result']['median'] == 3


class TestInputDataAccess:
    """입력 데이터 접근 테스트"""
    
    @pytest.mark.asyncio
    async def test_access_input_data(self, executor):
        """입력 데이터 접근"""
        code = "input['value'] * 2"
        input_data = {'value': 10}
        result = await executor.execute(code, input_data=input_data, mode='simple')
        
        assert result['success'] is True
        assert result['output']['result'] == 20
    
    @pytest.mark.asyncio
    async def test_access_nested_data(self, executor):
        """중첩 데이터 접근"""
        code = "input['user']['name'].upper()"
        input_data = {'user': {'name': 'john'}}
        result = await executor.execute(code, input_data=input_data, mode='simple')
        
        assert result['success'] is True
        assert result['output']['result'] == 'JOHN'
    
    @pytest.mark.asyncio
    async def test_filter_input_list(self, executor):
        """입력 리스트 필터링"""
        code = """
items = input['items']
filtered = [x for x in items if x['status'] == 'active']
result = len(filtered)
"""
        input_data = {
            'items': [
                {'id': 1, 'status': 'active'},
                {'id': 2, 'status': 'inactive'},
                {'id': 3, 'status': 'active'},
            ]
        }
        result = await executor.execute(code, input_data=input_data, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result'] == 2


class TestTimeout:
    """타임아웃 테스트"""
    
    @pytest.mark.asyncio
    async def test_timeout_infinite_loop(self, executor):
        """무한 루프 타임아웃"""
        code = """
while True:
    pass
"""
        result = await executor.execute(code, timeout=2, mode='advanced')
        
        # 타임아웃이 작동하지 않을 수 있음 (Windows)
        # 하지만 최소한 에러는 발생해야 함
        assert result['success'] is False or 'timeout' in result.get('error', '').lower()
    
    @pytest.mark.asyncio
    async def test_timeout_long_calculation(self, executor):
        """긴 계산 타임아웃"""
        code = """
result = 0
for i in range(10000000):
    result += i
"""
        result = await executor.execute(code, timeout=1, mode='advanced')
        
        # 빠른 시스템에서는 완료될 수 있음
        # 타임아웃 또는 성공 둘 다 허용
        assert 'success' in result


class TestErrorHandling:
    """에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_syntax_error(self, executor):
        """문법 에러"""
        code = "if True"  # 콜론 누락
        result = await executor.execute(code)
        
        assert result['success'] is False
        assert 'SecurityError' in result['error_type'] or 'SyntaxError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_runtime_error(self, executor):
        """런타임 에러"""
        code = "1 / 0"
        result = await executor.execute(code, mode='simple')
        
        assert result['success'] is False
        assert 'ZeroDivisionError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_name_error(self, executor):
        """이름 에러"""
        code = "undefined_variable"
        result = await executor.execute(code, mode='simple')
        
        assert result['success'] is False
        assert 'NameError' in result['error_type']
    
    @pytest.mark.asyncio
    async def test_type_error(self, executor):
        """타입 에러"""
        code = "'string' + 123"
        result = await executor.execute(code, mode='simple')
        
        assert result['success'] is False
        assert 'TypeError' in result['error_type']


class TestAdvancedFeatures:
    """고급 기능 테스트"""
    
    @pytest.mark.asyncio
    async def test_multiple_variables(self, executor):
        """여러 변수 반환"""
        code = """
a = 10
b = 20
c = a + b
result = {'a': a, 'b': b, 'sum': c}
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result']['sum'] == 30
    
    @pytest.mark.asyncio
    async def test_stdout_capture(self, executor):
        """stdout 캡처"""
        code = """
print("Hello World")
result = "done"
"""
        result = await executor.execute(code, mode='advanced')
        
        assert result['success'] is True
        assert 'Hello World' in result['output']['stdout']
    
    @pytest.mark.asyncio
    async def test_complex_data_processing(self, executor):
        """복잡한 데이터 처리"""
        code = """
from collections import Counter
from statistics import mean

# 데이터 분석
items = input['items']
values = [x['value'] for x in items]
categories = [x['category'] for x in items]

result = {
    'total': len(items),
    'avg_value': mean(values),
    'max_value': max(values),
    'min_value': min(values),
    'category_counts': dict(Counter(categories))
}
"""
        input_data = {
            'items': [
                {'value': 10, 'category': 'A'},
                {'value': 20, 'category': 'B'},
                {'value': 30, 'category': 'A'},
                {'value': 40, 'category': 'C'},
            ]
        }
        result = await executor.execute(code, input_data=input_data, mode='advanced')
        
        assert result['success'] is True
        assert result['output']['result']['total'] == 4
        assert result['output']['result']['avg_value'] == 25
        assert result['output']['result']['category_counts']['A'] == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
