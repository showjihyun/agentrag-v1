"""
Test script to verify ColPali logging during image upload
"""
import asyncio
import logging
import sys
from pathlib import Path

# Setup logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)


async def test_image_upload_logging():
    """Test that ColPali logs appear during image processing"""
    
    logger.info("=" * 70)
    logger.info("Testing Image Upload Logging")
    logger.info("=" * 70)
    
    # Import after logging setup
    from backend.services.hybrid_document_processor import get_hybrid_document_processor
    from backend.config import settings
    
    # Initialize hybrid processor
    logger.info("\n1. Initializing Hybrid Document Processor...")
    hybrid_processor = get_hybrid_document_processor(
        enable_colpali=True,
        colpali_threshold=0.3,
        process_images_always=False
    )
    
    logger.info(f"   ColPali enabled: {hybrid_processor.enable_colpali}")
    logger.info(f"   ColPali processor available: {hybrid_processor.colpali_processor is not None}")
    
    # Check for test image
    test_image_path = "demo_images/sample_chart.png"
    if not Path(test_image_path).exists():
        logger.warning(f"\n⚠️  Test image not found: {test_image_path}")
        logger.info("   Please create a test image or update the path")
        return
    
    logger.info(f"\n2. Processing test image: {test_image_path}")
    logger.info("   Expected logs:")
    logger.info("   - 'Using ColPali (image file)'")
    logger.info("   - 'ColPali processing completed: X patches'")
    logger.info("")
    
    # Process the image
    try:
        result = await hybrid_processor.process_document(
            file_path=test_image_path,
            file_type="png",
            document_id="test-image-001",
            metadata={'test': True}
        )
        
        logger.info("\n3. Processing Result:")
        logger.info(f"   Processing method: {result['processing_method']}")
        logger.info(f"   ColPali processed: {result['colpali_processed']}")
        logger.info(f"   ColPali patches: {result['colpali_patches']}")
        logger.info(f"   Is scanned: {result['is_scanned']}")
        logger.info(f"   Text ratio: {result['text_ratio']:.2f}")
        
        if result['colpali_processed']:
            logger.info("\n✅ SUCCESS: ColPali processing completed!")
        else:
            logger.warning("\n⚠️  WARNING: ColPali was not used")
            
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}", exc_info=True)
    
    logger.info("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(test_image_upload_logging())
