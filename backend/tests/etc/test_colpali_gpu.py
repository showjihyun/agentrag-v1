"""
Test ColPali GPU usage
"""
import sys
import torch

print("=" * 70)
print("ColPali GPU Test")
print("=" * 70)

# 1. Check PyTorch CUDA availability
print("\n1. PyTorch CUDA Check:")
print(f"   PyTorch version: {torch.__version__}")
print(f"   CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"   CUDA version: {torch.version.cuda}")
    print(f"   GPU count: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"\n   GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"      Total memory: {props.total_memory / 1024**3:.1f} GB")
        print(f"      Compute capability: {props.major}.{props.minor}")
        print(f"      Multi-processors: {props.multi_processor_count}")
else:
    print("   ⚠️  No GPU detected - ColPali will use CPU")
    print("   CPU processing is slower but still functional")

# 2. Test ColPali initialization
print("\n2. ColPali Initialization Test:")
try:
    sys.path.insert(0, '.')
    from backend.services.colpali_processor import get_colpali_processor
    from backend.config import settings
    
    print(f"   Settings:")
    print(f"      COLPALI_USE_GPU: {settings.COLPALI_USE_GPU}")
    print(f"      COLPALI_MODEL: {settings.COLPALI_MODEL}")
    print(f"      COLPALI_ENABLE_BINARIZATION: {settings.COLPALI_ENABLE_BINARIZATION}")
    print(f"      COLPALI_ENABLE_POOLING: {settings.COLPALI_ENABLE_POOLING}")
    
    print("\n   Initializing ColPali processor...")
    processor = get_colpali_processor(
        model_name=settings.COLPALI_MODEL,
        use_gpu=settings.COLPALI_USE_GPU,
        enable_binarization=settings.COLPALI_ENABLE_BINARIZATION,
        enable_pooling=settings.COLPALI_ENABLE_POOLING,
        pooling_factor=settings.COLPALI_POOLING_FACTOR
    )
    
    if processor:
        model_info = processor.get_model_info()
        print(f"\n   ✅ ColPali initialized successfully!")
        print(f"      Device: {model_info['device']}")
        print(f"      GPU available: {model_info['gpu_available']}")
        print(f"      GPU used: {model_info['gpu_used']}")
        print(f"      Binarization: {model_info['binarization']}")
        print(f"      Pooling: {model_info['pooling']}")
        
        # Check actual model device
        if hasattr(processor, 'model') and processor.model is not None:
            actual_device = next(processor.model.parameters()).device
            actual_dtype = next(processor.model.parameters()).dtype
            print(f"      Actual device: {actual_device}")
            print(f"      Actual dtype: {actual_dtype}")
            
            if torch.cuda.is_available() and 'cuda' in str(actual_device):
                print(f"\n   🎮 GPU is being used! Processing will be 5-10x faster.")
            else:
                print(f"\n   💻 Using CPU. Consider enabling GPU for faster processing.")
    else:
        print("   ❌ ColPali processor returned None")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Test Complete")
print("=" * 70)
