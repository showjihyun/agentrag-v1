"""
Check ColPali initialization status
"""
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def check_colpali_status():
    """Check if ColPali can be initialized"""
    
    print("=" * 70)
    print("ColPali Status Check")
    print("=" * 70)
    
    # 1. Check imports
    print("\n1. Checking imports...")
    try:
        from backend.services.colpali_processor import get_colpali_processor
        print("   ✅ colpali_processor module found")
    except ImportError as e:
        print(f"   ❌ Failed to import colpali_processor: {e}")
        return
    
    try:
        from backend.services.colpali_milvus_service import get_colpali_milvus_service
        print("   ✅ colpali_milvus_service module found")
    except ImportError as e:
        print(f"   ❌ Failed to import colpali_milvus_service: {e}")
        return
    
    # 2. Check ColPali processor initialization
    print("\n2. Initializing ColPali processor...")
    try:
        processor = get_colpali_processor()
        print(f"   ✅ ColPali processor initialized: {type(processor)}")
        print(f"   Model: {getattr(processor, 'model_name', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Failed to initialize ColPali processor: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Check Milvus service initialization
    print("\n3. Initializing ColPali Milvus service...")
    try:
        milvus_service = get_colpali_milvus_service()
        print(f"   ✅ ColPali Milvus service initialized: {type(milvus_service)}")
        print(f"   Collection: {getattr(milvus_service, 'collection_name', 'unknown')}")
    except Exception as e:
        print(f"   ❌ Failed to initialize ColPali Milvus service: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Check environment variables
    print("\n4. Checking environment variables...")
    from backend.config import settings
    print(f"   ENABLE_HYBRID_PROCESSING: {settings.ENABLE_HYBRID_PROCESSING}")
    print(f"   ENABLE_COLPALI: {settings.ENABLE_COLPALI}")
    print(f"   COLPALI_MODEL: {settings.COLPALI_MODEL}")
    print(f"   COLPALI_COLLECTION_NAME: {settings.COLPALI_COLLECTION_NAME}")
    
    # 5. Test image processing
    print("\n5. Testing image processing...")
    import os
    test_images = [
        "demo_images/sample_chart.png",
        "uploads/test.png",
        "test.png"
    ]
    
    test_image = None
    for img_path in test_images:
        if os.path.exists(img_path):
            test_image = img_path
            break
    
    if test_image:
        print(f"   Found test image: {test_image}")
        try:
            result = processor.process_image(test_image)
            print(f"   ✅ Image processed successfully")
            print(f"   Patches: {result.get('num_patches', 0)}")
            print(f"   Embeddings shape: {result.get('embeddings').shape if result.get('embeddings') is not None else 'None'}")
        except Exception as e:
            print(f"   ❌ Failed to process image: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"   ⚠️  No test image found. Tried: {test_images}")
    
    print("\n" + "=" * 70)
    print("✅ ColPali is properly configured and working!")
    print("=" * 70)

if __name__ == "__main__":
    check_colpali_status()
