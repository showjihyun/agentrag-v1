"""
Korean Document Processing Pipeline

한글 문서 처리 통합 파이프라인:
1. 파일 타입 감지
2. 텍스트 추출
3. 전처리 (정규화)
4. 청킹 (의미 단위)
5. 메타데이터 추출
"""

import logging
from typing import Dict, List, Optional, BinaryIO
from datetime import datetime

from backend.services.document_processor import DocumentProcessor
from backend.services.korean_preprocessor import get_korean_preprocessor
from backend.services.korean_chunking_strategy import (
    get_korean_chunking_strategy,
    ChunkConfig
)
from backend.services.hwp_processor_wrapper import get_hwp_processor_wrapper
from backend.services.korean_text_processor import get_korean_text_processor

logger = logging.getLogger(__name__)


class KoreanDocumentPipeline:
    """
    한글 문서 처리 통합 파이프라인
    
    Features:
    - 자동 파일 타입 감지
    - 최적화된 전처리
    - 의미 기반 청킹
    - 메타데이터 추출
    - 성능 모니터링
    """
    
    def __init__(
        self,
        chunk_config: Optional[ChunkConfig] = None,
        use_advanced_parser: bool = True,
        use_morpheme_analysis: bool = False  # 기본값 False (성능 우선)
    ):
        # 기본 문서 프로세서
        self.doc_processor = DocumentProcessor()
        
        # 한글 전처리기
        self.preprocessor = get_korean_preprocessor()
        
        # 한글 청킹 전략
        self.chunking_strategy = get_korean_chunking_strategy(chunk_config)
        
        # HWP 프로세서
        self.hwp_processor = get_hwp_processor_wrapper(
            document_processor=self.doc_processor,
            use_advanced_parser=use_advanced_parser,
            use_korean_processor=True
        )
        
        # 한글 텍스트 프로세서 (형태소 분석 - 선택적)
        self.korean_processor = get_korean_text_processor(
            use_morpheme_analysis=use_morpheme_analysis
        )
        
        self.use_morpheme_analysis = use_morpheme_analysis
        
        logger.info(
            f"KoreanDocumentPipeline initialized: "
            f"advanced_parser={use_advanced_parser}, "
            f"morpheme_analysis={use_morpheme_analysis}"
        )
    
    def process_document(
        self,
        file_content: bytes,
        filename: str,
        fast_mode: bool = False
    ) -> Dict:
        """
        문서 처리 메인 파이프라인
        
        Args:
            file_content: 파일 바이트
            filename: 파일명
            fast_mode: 빠른 모드 (최소 처리)
        
        Returns:
            {
                'text': str,
                'chunks': List[Dict],
                'metadata': Dict,
                'stats': Dict
            }
        """
        start_time = datetime.now()
        
        try:
            # 1. 파일 타입 감지
            file_type = self.doc_processor.detect_file_type(filename)
            logger.info(f"Processing {file_type} file: {filename}")
            
            # 2. 텍스트 추출
            text = self._extract_text(file_content, file_type, filename)
            
            if not text or not text.strip():
                raise ValueError("No text extracted from document")
            
            # 3. 전처리
            preprocessed = self.preprocessor.preprocess(
                text,
                doc_type=file_type,
                fast_mode=fast_mode
            )
            
            processed_text = preprocessed['text']
            is_korean = preprocessed['is_korean']
            
            # 4. 형태소 분석 (선택적, 한글 문서만)
            keywords = []
            if not fast_mode and is_korean and self.use_morpheme_analysis:
                korean_result = self.korean_processor.process_korean_text(processed_text)
                keywords = korean_result.get('keywords', [])
            
            # 5. 청킹
            chunks = self.chunking_strategy.chunk_text(
                processed_text,
                metadata={
                    'filename': filename,
                    'file_type': file_type,
                    'is_korean': is_korean
                }
            )
            
            # 6. 청크 최적화
            if not fast_mode:
                chunks = self.chunking_strategy.optimize_chunks(chunks)
            
            # 7. 메타데이터
            metadata = {
                'filename': filename,
                'file_type': file_type,
                'is_korean': is_korean,
                'keywords': keywords,
                'processed_at': datetime.now().isoformat()
            }
            
            # 8. 통계
            processing_time = (datetime.now() - start_time).total_seconds()
            stats = {
                **preprocessed['stats'],
                'chunk_count': len(chunks),
                'processing_time': processing_time,
                'fast_mode': fast_mode
            }
            
            logger.info(
                f"Document processed: {len(chunks)} chunks, "
                f"{processing_time:.2f}s, "
                f"{'Korean' if is_korean else 'Non-Korean'}"
            )
            
            return {
                'text': processed_text,
                'chunks': chunks,
                'metadata': metadata,
                'stats': stats
            }
            
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise
    
    def _extract_text(
        self,
        file_content: bytes,
        file_type: str,
        filename: str
    ) -> str:
        """파일 타입별 텍스트 추출"""
        
        # HWP/HWPX는 전용 프로세서 사용
        if file_type == 'hwp':
            result = self.hwp_processor.process_hwp(file_content, filename)
            return result['text']
        
        elif file_type == 'hwpx':
            result = self.hwp_processor.process_hwpx(file_content, filename)
            return result['text']
        
        # 나머지는 기본 프로세서 사용
        elif file_type == 'pdf':
            return self.doc_processor.extract_text_from_pdf(file_content)
        
        elif file_type == 'txt':
            return self.doc_processor.extract_text_from_txt(file_content)
        
        elif file_type == 'docx':
            return self.doc_processor.extract_text_from_docx(file_content)
        
        elif file_type == 'pptx':
            return self.doc_processor.extract_text_from_pptx(file_content)
        
        elif file_type == 'xlsx':
            return self.doc_processor.extract_text_from_xlsx(file_content)
        
        elif file_type == 'csv':
            return self.doc_processor.extract_text_from_csv(file_content)
        
        elif file_type == 'json':
            return self.doc_processor.extract_text_from_json(file_content)
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def batch_process(
        self,
        files: List[Dict],
        fast_mode: bool = False
    ) -> List[Dict]:
        """
        배치 문서 처리
        
        Args:
            files: [{'content': bytes, 'filename': str}, ...]
            fast_mode: 빠른 모드
        
        Returns:
            List[Dict]: 처리 결과 리스트
        """
        results = []
        
        for file_info in files:
            try:
                result = self.process_document(
                    file_content=file_info['content'],
                    filename=file_info['filename'],
                    fast_mode=fast_mode
                )
                results.append({
                    'success': True,
                    'filename': file_info['filename'],
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to process {file_info['filename']}: {e}")
                results.append({
                    'success': False,
                    'filename': file_info['filename'],
                    'error': str(e)
                })
        
        return results


# Global instance
_korean_document_pipeline: Optional[KoreanDocumentPipeline] = None


def get_korean_document_pipeline(
    chunk_config: Optional[ChunkConfig] = None,
    use_advanced_parser: bool = True,
    use_morpheme_analysis: bool = False
) -> KoreanDocumentPipeline:
    """Get global Korean document pipeline instance"""
    global _korean_document_pipeline
    if _korean_document_pipeline is None:
        _korean_document_pipeline = KoreanDocumentPipeline(
            chunk_config=chunk_config,
            use_advanced_parser=use_advanced_parser,
            use_morpheme_analysis=use_morpheme_analysis
        )
    return _korean_document_pipeline
