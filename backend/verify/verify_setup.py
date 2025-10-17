"""Quick verification script for GPU and ColPali"""
import sys

try:
    # Check PyTorch
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    
    # Check ColPali
    from colpali_engine.models import ColPali
    print("ColPali: OK")
    
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
