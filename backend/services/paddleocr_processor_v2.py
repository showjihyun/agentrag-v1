"""
PaddleOCR Processor for Document Understanding

Based on official PaddleOCR GitHub repository:
https://github.com/PaddlePaddle/PaddleOCR

Features:
- Text Detection & Recognition (PP-OCRv4)
- Text Direction Classification
- Multi-language Support (80+ languages)
- GPU Acceleration
- High Accuracy (95%+ for printed text)

Installation:
    pip install paddlepaddle-gpu==3.0.0b1 -i https://www.paddlepaddle.org.cn/packages/stable/cu118/
    pip install paddleocr>=2.7.0

Usage:
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(use_angle_cls=True, lang='korean', use_gpu=True)
    result = ocr.ocr(img_path, cls=True)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class PaddleOCRProcessorV2:
    """
    PaddleOCR Processor using official GitHub API
    
    Based on: https://github.com/PaddlePaddle/PaddleOCR
    
    Features:
    - Text detection and recognition
    - Text direction classification
    - Multi-language support (Korean optimized)
    - GPU acceleration
    
    Example:
        processor = PaddleOCRProcessorV2(use_gpu=True, lang='korean')
        result = processor.process_image_bytes(image_bytes)
    """
    
    def __init__(
        self,
        use_gpu: bool = True,
        lang: str = 'korean',
        use_angle_cls: bool = True
    ):
        """
        Initialize PaddleOCR processor.
        
        Args:
            use_gpu: Use GPU for acceleration (default: True)
            lang: Language for OCR (default: 'korean')
                  Supported: 'ch', 'en', 'korean', 'japan', 'chinese_cht', 
                            'ta', 'te', 'ka', 'latin', 'arabic', 'cyrillic', 
                            'devanagari', etc. (80+ languages)
            use_angle_cls: Use angle classification for rotated text (default: True)
        """
        self.use_gpu = use_gpu
        self.lang = lang
        self.use_angle_cls = use_angle_cls
        
        # Initialize PaddleOCR
        self._init_paddleocr()
        
        logger.info(
            f"PaddleOCR initialized: lang={lang}, gpu={use_gpu}, "
            f"angle_cls={use_angle_cls}"
        )
    
    def _init_paddleocr(self):
        """Initialize PaddleOCR engine."""
        try:
            from paddleocr import PaddleOCR
            
            # Initialize with official API (minimal parameters)
            self.ocr = PaddleOCR(lang=self.lang)
            
            self.available = True
            logger.info("✅ PaddleOCR engine initialized successfully")
            
        except ImportError as e:
            logger.error(f"PaddleOCR not available: {e}")
            logger.error(
                "Install with: "
                "pip install paddlepaddle-gpu -i https://www.paddlepaddle.org.cn/packages/stable/cu118/ && "
                'pip install "paddleocr[all]"'
            )
            self.ocr = None
            self.available = False
            
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            self.ocr = None
            self.available = False
    
    def process_image_bytes(
        self,
        image_bytes: bytes,
        cls: bool = True
    ) -> Dict[str, Any]:
        """
        Process image bytes and extract text.
        
        Args:
            image_bytes: Image file content as bytes
            cls: Use angle classification (default: True)
        
        Returns:
            Dict containing:
                - text: Extracted text
                - boxes: List of text boxes with coordinates
                - confidence: Average confidence score
                - num_boxes: Number of detected text boxes
        
        Raises:
            RuntimeError: If PaddleOCR is not available
            ValueError: If image processing fails
        """
        if not self.available or self.ocr is None:
            raise RuntimeError(
                "PaddleOCR not available. Please install: "
                "pip install paddlepaddle-gpu==3.0.0b1 paddleocr>=2.7.0"
            )
        
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert to numpy array
            img_array = np.array(image)
            
            # Run OCR
            result = self.ocr.ocr(img_array, cls=cls)
            
            # Parse results
            if not result or not result[0]:
                return {
                    'text': '',
                    'boxes': [],
                    'confidence': 0.0,
                    'num_boxes': 0
                }
            
            # Extract text and metadata
            text_lines = []
            boxes = []
            confidences = []
            
            for line in result[0]:
                # line structure: [[[x1,y1], [x2,y2], [x3,y3], [x4,y4]], (text, confidence)]
                box_coords = line[0]
                text = line[1][0]
                confidence = line[1][1]
                
                text_lines.append(text)
                boxes.append({
                    'coordinates': box_coords,
                    'text': text,
                    'confidence': confidence
                })
                confidences.append(confidence)
            
            # Combine text
            full_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            logger.info(
                f"OCR completed: {len(boxes)} boxes, "
                f"avg confidence: {avg_confidence:.2%}"
            )
            
            return {
                'text': full_text,
                'boxes': boxes,
                'confidence': avg_confidence,
                'num_boxes': len(boxes)
            }
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise ValueError(f"Failed to process image: {e}")
    
    def process_image_file(
        self,
        image_path: str,
        cls: bool = True
    ) -> Dict[str, Any]:
        """
        Process image file and extract text.
        
        Args:
            image_path: Path to image file
            cls: Use angle classification (default: True)
        
        Returns:
            Dict containing extracted text and metadata
        """
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            return self.process_image_bytes(image_bytes, cls=cls)
            
        except FileNotFoundError:
            raise ValueError(f"Image file not found: {image_path}")
        except Exception as e:
            raise ValueError(f"Failed to read image file: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get processor statistics and capabilities.
        
        Returns:
            Dict containing processor information
        """
        return {
            'available': self.available,
            'use_gpu': self.use_gpu,
            'lang': self.lang,
            'use_angle_cls': self.use_angle_cls,
            'version': 'PaddleOCR v2.7+',
            'features': [
                'Text Detection',
                'Text Recognition',
                'Angle Classification',
                'Multi-language Support',
                'GPU Acceleration'
            ]
        }


# Singleton instance
_paddleocr_processor_v2: Optional[PaddleOCRProcessorV2] = None


def get_paddleocr_processor_v2(
    use_gpu: bool = True,
    lang: str = 'korean',
    use_angle_cls: bool = True
) -> Optional[PaddleOCRProcessorV2]:
    """
    Get or create PaddleOCR processor singleton.
    
    Args:
        use_gpu: Use GPU for acceleration
        lang: Language for OCR
        use_angle_cls: Use angle classification
    
    Returns:
        PaddleOCRProcessorV2 instance or None if not available
    """
    global _paddleocr_processor_v2
    
    if _paddleocr_processor_v2 is None:
        try:
            _paddleocr_processor_v2 = PaddleOCRProcessorV2(
                use_gpu=use_gpu,
                lang=lang,
                use_angle_cls=use_angle_cls
            )
        except Exception as e:
            logger.error(f"Failed to create PaddleOCR processor: {e}")
            return None
    
    return _paddleocr_processor_v2


def reset_paddleocr_processor_v2():
    """Reset the singleton instance (useful for testing)."""
    global _paddleocr_processor_v2
    _paddleocr_processor_v2 = None
