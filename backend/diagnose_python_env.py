"""
Diagnose Python environment and ColPali installation
"""
import sys
import os

print("=" * 70)
print("Python Environment Diagnosis")
print("=" * 70)

# 1. Python executable
print("\n1. Python Executable:")
print(f"   Path: {sys.executable}")
print(f"   Version: {sys.version}")

# 2. Python paths
print("\n2. Python Search Paths:")
for i, path in enumerate(sys.path[:5], 1):
    print(f"   {i}. {path}")

# 3. Site packages
print("\n3. Site Packages:")
import site
for sp in site.getsitepackages():
    print(f"   - {sp}")

# 4. Check colpali_engine
print("\n4. ColPali Engine Check:")
try:
    import colpali_engine
    print(f"   ✅ Found: {colpali_engine.__file__}")
    print(f"   Version: {colpali_engine.__version__ if hasattr(colpali_engine, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"   ❌ Not found: {e}")
    
    # Check if it exists in site-packages
    print("\n   Searching in site-packages...")
    for sp in site.getsitepackages():
        colpali_path = os.path.join(sp, 'colpali_engine')
        if os.path.exists(colpali_path):
            print(f"   ⚠️  Found at: {colpali_path}")
            print(f"      But not importable!")
        else:
            print(f"   ❌ Not in: {sp}")

# 5. Check torch
print("\n5. PyTorch Check:")
try:
    import torch
    print(f"   ✅ Version: {torch.__version__}")
    print(f"   CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
except ImportError as e:
    print(f"   ❌ Not found: {e}")

# 6. Installed packages
print("\n6. Checking pip list for colpali:")
import subprocess
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list"],
        capture_output=True,
        text=True
    )
    for line in result.stdout.split('\n'):
        if 'colpali' in line.lower():
            print(f"   {line}")
    
    if 'colpali' not in result.stdout.lower():
        print("   ❌ colpali-engine not found in pip list")
except Exception as e:
    print(f"   ❌ Error running pip: {e}")

# 7. Recommendation
print("\n" + "=" * 70)
print("Recommendation:")
print("=" * 70)

try:
    import colpali_engine
    print("✅ ColPali is installed and importable")
except ImportError:
    print("❌ ColPali is NOT importable")
    print("\nTo fix, run:")
    print(f"   {sys.executable} -m pip install colpali-engine --no-cache-dir")
    print("\nOr if using this exact Python:")
    print(f"   python -m pip install colpali-engine --no-cache-dir")

print("=" * 70)
