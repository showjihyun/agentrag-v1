#!/usr/bin/env python
"""Check if SECRET_ENCRYPTION_KEY is in Settings class."""

lines = open('backend/config.py', encoding='utf-8').readlines()

class_started = False
class_indent = None
secret_key_line = None

for i, line in enumerate(lines, 1):
    if 'class Settings' in line:
        class_started = True
        class_indent = len(line) - len(line.lstrip())
        print(f"Line {i}: Settings class starts (indent={class_indent})")
        continue
    
    if class_started:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Check if we've left the class (non-empty line with same or less indentation)
        if stripped and current_indent <= class_indent:
            print(f"Line {i}: Settings class ends")
            print(f"  Line content: {line.rstrip()[:60]}")
            break
        
        # Check for SECRET_ENCRYPTION_KEY
        if 'SECRET_ENCRYPTION_KEY' in line:
            secret_key_line = i
            print(f"Line {i}: Found SECRET_ENCRYPTION_KEY (indent={current_indent})")

if secret_key_line:
    print(f"\n✓ SECRET_ENCRYPTION_KEY found at line {secret_key_line}")
else:
    print(f"\n✗ SECRET_ENCRYPTION_KEY not found in Settings class")
