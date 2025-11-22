"""
Python Code Executor 샌드박스 보안 테스트 (독립 실행)

실행: python test_python_sandbox.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from services.tools.code.python_executor import PythonCodeExecutor


async def test_security():
    """보안 테스트"""
    executor = PythonCodeExecutor(tool_id='python_code', tool_name='Python Code')
    
    print("=" * 70)
    print("Python Code Executor - 보안 테스트")
    print("=" * 70)
    
    tests = [
        # 차단되어야 하는 코드
        ("❌ Import 차단", "import os", False),
        ("❌ From Import 차단", "from os import system", False),
        ("❌ Open 차단", "open('/etc/passwd')", False),
        ("❌ Eval 차단", "eval('1+1')", False),
        ("❌ Exec 차단", "exec('print(1)')", False),
        ("❌ __import__ 차단", "__import__('os')", False),
        
        # 허용되어야 하는 코드
        ("✅ 간단한 계산", "2 + 2", True),
        ("✅ 리스트 컴프리헨션", "[x * 2 for x in range(5)]", True),
        ("✅ JSON 사용", "json.dumps({'a': 1})", True),
        ("✅ Math 사용", "math.sqrt(16)", True),
        ("✅ Datetime 사용", "from datetime import datetime; datetime.now().year", True),
        ("✅ 정규표현식", "re.findall(r'\\d+', 'abc123')", True),
        ("✅ Statistics", "statistics.mean([1,2,3,4,5])", True),
    ]
    
    passed = 0
    failed = 0
    
    for name, code, should_succeed in tests:
        print(f"\n{name}")
        print(f"  코드: {code}")
        
        result = await executor.execute(code, mode='simple')
        
        success = result['success']
        expected = should_succeed
        
        if success == expected:
            print(f"  ✅ PASS - {'성공' if success else '차단됨'}")
            passed += 1
        else:
            print(f"  ❌ FAIL - 예상: {'성공' if expected else '차단'}, 실제: {'성공' if success else '차단'}")
            if not success:
                print(f"  에러: {result.get('error', 'Unknown')}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"결과: {passed} 통과, {failed} 실패")
    print("=" * 70)


async def test_advanced_features():
    """고급 기능 테스트"""
    executor = PythonCodeExecutor(tool_id='python_code', tool_name='Python Code')
    
    print("\n" + "=" * 70)
    print("고급 기능 테스트")
    print("=" * 70)
    
    # 1. 입력 데이터 처리
    print("\n1. 입력 데이터 처리")
    code = """
items = input['items']
filtered = [x for x in items if x['value'] > 20]
result = {
    'total': len(items),
    'filtered': len(filtered),
    'sum': sum(x['value'] for x in filtered)
}
"""
    input_data = {
        'items': [
            {'value': 10},
            {'value': 25},
            {'value': 30},
            {'value': 15},
        ]
    }
    result = await executor.execute(code, input_data=input_data, mode='advanced')
    print(f"  성공: {result['success']}")
    if result['success']:
        print(f"  결과: {result['output']['result']}")
    
    # 2. 통계 계산
    print("\n2. 통계 계산")
    code = """
from statistics import mean, median, stdev
from collections import Counter

data = input['numbers']
result = {
    'count': len(data),
    'mean': mean(data),
    'median': median(data),
    'stdev': stdev(data) if len(data) > 1 else 0,
    'min': min(data),
    'max': max(data)
}
"""
    input_data = {'numbers': [10, 20, 30, 40, 50]}
    result = await executor.execute(code, input_data=input_data, mode='advanced')
    print(f"  성공: {result['success']}")
    if result['success']:
        print(f"  결과: {result['output']['result']}")
    
    # 3. JSON 처리
    print("\n3. JSON 처리")
    code = """
import json

# JSON 파싱
data = json.loads(input['json_string'])

# 변환
result = {
    'keys': list(data.keys()),
    'values': list(data.values()),
    'count': len(data)
}
"""
    input_data = {'json_string': '{"name": "John", "age": 30, "city": "Seoul"}'}
    result = await executor.execute(code, input_data=input_data, mode='advanced')
    print(f"  성공: {result['success']}")
    if result['success']:
        print(f"  결과: {result['output']['result']}")
    
    # 4. 날짜/시간 처리
    print("\n4. 날짜/시간 처리")
    code = """
from datetime import datetime, timedelta

now = datetime(2024, 1, 1, 12, 0, 0)
tomorrow = now + timedelta(days=1)
next_week = now + timedelta(weeks=1)

result = {
    'now': now.isoformat(),
    'tomorrow': tomorrow.isoformat(),
    'next_week': next_week.isoformat(),
    'day_of_week': now.strftime('%A')
}
"""
    result = await executor.execute(code, mode='advanced')
    print(f"  성공: {result['success']}")
    if result['success']:
        print(f"  결과: {result['output']['result']}")
    
    # 5. 정규표현식
    print("\n5. 정규표현식")
    code = """
import re

text = input['text']
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}', text)
phones = re.findall(r'\\d{3}-\\d{4}-\\d{4}', text)

result = {
    'emails': emails,
    'phones': phones,
    'email_count': len(emails),
    'phone_count': len(phones)
}
"""
    input_data = {
        'text': 'Contact: john@example.com, jane@test.com, Phone: 010-1234-5678'
    }
    result = await executor.execute(code, input_data=input_data, mode='advanced')
    print(f"  성공: {result['success']}")
    if result['success']:
        print(f"  결과: {result['output']['result']}")


async def test_performance():
    """성능 테스트"""
    executor = PythonCodeExecutor(tool_id='python_code', tool_name='Python Code')
    
    print("\n" + "=" * 70)
    print("성능 테스트")
    print("=" * 70)
    
    # 1. 간단한 계산 (빠름)
    print("\n1. 간단한 계산")
    code = "sum(range(1000))"
    result = await executor.execute(code, mode='simple')
    print(f"  성공: {result['success']}")
    print(f"  실행 시간: {result.get('execution_time', 0):.4f}초")
    
    # 2. 복잡한 계산 (느림)
    print("\n2. 복잡한 데이터 처리")
    code = """
data = [{'id': i, 'value': i * 2} for i in range(1000)]
filtered = [x for x in data if x['value'] % 3 == 0]
result = {
    'total': len(data),
    'filtered': len(filtered),
    'sum': sum(x['value'] for x in filtered)
}
"""
    result = await executor.execute(code, mode='advanced')
    print(f"  성공: {result['success']}")
    print(f"  실행 시간: {result.get('execution_time', 0):.4f}초")
    if result['success']:
        print(f"  결과: {result['output']['result']}")


async def main():
    """메인 함수"""
    try:
        await test_security()
        await test_advanced_features()
        await test_performance()
        
        print("\n" + "=" * 70)
        print("✅ 모든 테스트 완료!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
