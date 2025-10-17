import re

text = "cs @bigvalue. co. kr"

print(f"원본: '{text}'")

# @ 제거
text = re.sub(r'\s*@\s*', '@', text)
print(f"@ 처리 후: '{text}'")

# . 제거 (앞)
text = re.sub(r'\.\s+(?=[a-z0-9])', '.', text)
print(f". 앞 공백 제거 후: '{text}'")

# . 제거 (뒤)
text = re.sub(r'(?<=[a-z0-9])\s+\.', '.', text)
print(f". 뒤 공백 제거 후: '{text}'")
