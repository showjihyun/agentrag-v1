"""
Test ColPali GPU usage
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from backend.config import settings

print("=" * 70)
print("ColPali GPU Test")
print("=" * 70)

# 1. Check PyTorch GPU
print("\n1. PyTorch GPU Status:")
print(f"   PyTorch version: {torch.__version__}")
print(f"   CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"   CUDA version: {torch.version.cuda}")
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

# 2. Check settings
print("\n2. ColPali Settings:")
print(f"   ENABLE_COLPALI: {settings.ENABLE_COLPALI}")
print(f"   COLPALI_MODEL: {settings.COLPALI_MODEL}")
print(f"   COLPALI_USE_GPU: {settings.COLPALI_USE_GPU}")
print(f"   COLPALI_ENABLE_BINARIZATION: {settings.COLPALI_ENABLE_BINARIZATION}")
print(f"   COLPALI_ENABLE_POOLING: {settings.COLPALI_ENABLE_POOLING}")

# 3. Initialize ColPali
print("\n3. Initializing ColPali:")
try:
    from backend.services.colpali_processor import get_colpali_processor
    
    processor = get_colpali_processor(
        model_name=settings.COLPALI_MODEL,
        use_gpu=settings.COLPALI_USE_GPU,
        enable_binarization=settings.COLPALI_ENABLE_BINARIZATION,
        enable_pooling=settings.COLPALI_ENABLE_POOLING
    )
    
    if processor:
        print(f"   [OK] ColPali initialized successfully")
        print(f"   Model: {processor.model_name}")
        print(f"   Device: {processor.device}")
        print(f"   Use GPU: {processor.use_gpu}")
        
        # Check actual model device
        if processor.model:
            actual_device = next(processor.model.parameters()).device
            actual_dtype = next(processor.model.parameters()).dtype
            print(f"   Actual device: {actual_device}")
            print(f"   Actual dtype: {actual_dtype}")
            
            if actual_device.type == 'cuda':
                print(f"   [GPU] Model is on GPU!")
            else:
                print(f"   [CPU] Model is on CPU")
    else:
        print(f"   [FAIL] ColPali initialization failed")
        
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
