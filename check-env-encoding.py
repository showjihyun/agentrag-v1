#!/usr/bin/env python3
# Check .env file encoding issues

with open('.env', 'rb') as f:
    data = f.read()
    
print(f"File size: {len(data)} bytes")
print(f"\nBytes around position 6702-6703:")
print(f"Position 6700-6710: {data[6700:6710]}")
print(f"As hex: {data[6700:6710].hex()}")

# Try to find the problematic character
try:
    data.decode('utf-8')
    print("\n✓ File is valid UTF-8")
except UnicodeDecodeError as e:
    print(f"\n✗ UTF-8 decode error at position {e.start}-{e.end}")
    print(f"Problematic bytes: {data[e.start:e.end]}")
    print(f"As hex: {data[e.start:e.end].hex()}")
    print(f"\nContext (50 chars before):")
    print(data[max(0, e.start-50):e.start].decode('utf-8', errors='replace'))
    print(f"\nProblematic part:")
    print(data[e.start:e.end])
    print(f"\nContext (50 chars after):")
    print(data[e.end:e.end+50].decode('utf-8', errors='replace'))
