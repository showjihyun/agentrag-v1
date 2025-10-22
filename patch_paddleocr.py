"""
PaddleOCR __init__.py 파일을 패치하여 PaddleX 의존성 제거
"""
import os
import sys

# PaddleOCR 설치 경로 찾기
try:
    import paddleocr
    paddleocr_path = os.path.dirname(paddleocr.__file__)
except:
    # paddleocr를 import할 수 없으면 경로를 직접 찾기
    import site
    site_packages_list = site.getsitepackages()
    # site-packages 디렉토리 찾기
    site_packages = [p for p in site_packages_list if 'site-packages' in p][0]
    paddleocr_path = os.path.join(site_packages, 'paddleocr')

init_file = os.path.join(paddleocr_path, '__init__.py')

print(f"PaddleOCR __init__.py 경로: {init_file}")

if not os.path.exists(init_file):
    print("❌ __init__.py 파일을 찾을 수 없습니다")
    sys.exit(1)

# 파일 읽기
with open(init_file, 'r', encoding='utf-8') as f:
    content = f.read()

# PaddleX import 주석 처리 및 mock benchmark 함수 추가
old_line = 'from paddlex.inference.utils.benchmark import benchmark'
new_lines = '''# from paddlex.inference.utils.benchmark import benchmark
# PaddleX 의존성 제거를 위한 mock benchmark 함수
def benchmark(func):
    """Mock benchmark decorator"""
    return func'''

if old_line in content:
    content = content.replace(old_line, new_lines)
    
    # 파일 쓰기
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ PaddleOCR __init__.py 파일 패치 완료!")
    print("   PaddleX 의존성이 제거되었습니다.")
else:
    print("⚠️  이미 패치되었거나 파일 구조가 변경되었습니다")

print("\n이제 PaddleOCR을 테스트할 수 있습니다:")
print("  python test-paddleocr-simple.py")
