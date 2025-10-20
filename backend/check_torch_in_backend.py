"""
Check if torch can detect GPU in backend environment
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 70)
print("Torch GPU Check in Backend Environment")
print("=" * 70)

# Check torch import
try:
    import torch
    print(f"\n1. Torch imported successfully")
    print(f"   Version: {torch.__version__}")
    print(f"   Location: {torch.__file__}")
except ImportError as e:
    print(f"\n1. Failed to import torch: {e}")
    sys.exit(1)

# Check CUDA
print(f"\n2. CUDA Status:")
print(f"   CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"   CUDA version: {torch.version.cuda}")
    print(f"   GPU count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"   GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print(f"   No CUDA GPU detected")
    print(f"\n   Possible reasons:")
    print(f"   - PyTorch CPU-only version installed")
    print(f"   - CUDA drivers not installed")
    print(f"   - GPU not available")

# Check environment variables
print(f"\n3. Environment Variables:")
cuda_visible = os.environ.get('CUDA_VISIBLE_DEVICES', 'Not set')
print(f"   CUDA_VISIBLE_DEVICES: {cuda_visible}")

# Try to create a tensor on GPU
print(f"\n4. GPU Tensor Test:")
try:
    if torch.cuda.is_available():
        x = torch.tensor([1.0, 2.0, 3.0]).cuda()
        print(f"   [OK] Created tensor on GPU: {x.device}")
    else:
        print(f"   [SKIP] No GPU available")
except Exception as e:
    print(f"   [FAIL] Error: {e}")

print("\n" + "=" * 70)
