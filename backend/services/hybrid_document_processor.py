"""
Hybrid Document Processor

하이브리드 접근 방식:
1. Native 텍스트 추출 (빠름, 효율적)
2. ColPali 이미지 임베딩 (정확도, 시각적 검색)
3. 결과 병합 및 최적화
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class HybridDocumentProcessor:
    """
    하이브리드 문서 처리기
    
    Features:
    - Docling 고급 문서 처리 (표/차트 추출)
    - Native 텍스트 추출 (Fallback)
    - ColPali 이미지 임베딩 (선택적, 정확도)
    - 스캔본 자동 감지
    - 비용 최적화
    """
    
    def __init__(
        self,
        use_docling: bool = True,  # NEW: Docling 사용
        enable_colpali: bool = True,
        colpali_threshold: float = 0.3,  # 텍스트 비율 임계값
        process_images_always: bool = False  # 항상 이미지 처리
    ):
        """
        초기화
        
        Args:
            use_docling: Docling 사용 여부 (권장)
            enable_colpali: ColPali 사용 여부
            colpali_threshold: 텍스트 비율 임계값 (이하면 스캔본으로 판단)
            process_images_always: 항상 이미지 처리 (하이브리드 모드)
        """
        self.use_docling = use_docling
        self.enable_colpali = enable_colpali
        self.colpali_threshold = colpali_threshold
        self.process_images_always = process_images_always
        
        # 프로세서 초기화
        self.docling_processor = None
        self.doc_processor = None
        self.colpali_processor = None
        self.colpali_milvus = None
        self.structured_data_service = None
        
        self._init_processors()
        
        logger.info(
            f"HybridDocumentProcessor initialized: "
            f"docling={use_docling}, "
            f"colpali={enable_colpali}, "
            f"threshold={colpali_threshold}, "
            f"always_process={process_images_always}"
        )
    
    def _init_processors(self):
        """프로세서 초기화"""
        try:
            # Docling 프로세서 (우선)
            if self.use_docling:
                try:
                    from backend.services.docling_processor import get_docling_processor
                    from backend.services.structured_data_service import get_structured_data_service
                    
                    self.docling_processor = get_docling_processor(
                        enable_ocr=True,
                        enable_table_structure=True,
                        enable_figure_extraction=True,
                        images_scale=2.0
                    )
                    self.structured_data_service = get_structured_data_service()
                    
                    logger.info("✅ Docling processor initialized")
                    
                except Exception as e:
                    logger.warning(f"⚠️  Docling not available: {e}")
                    logger.warning("Falling back to native processor")
                    self.use_docling = False
            
            # Native 텍스트 프로세서 (Fallback)
            if not self.use_docling:
                from backend.services.document_processor import DocumentProcessor
                self.doc_processor = DocumentProcessor()
                logger.info("✅ Native document processor initialized")
            
            # ColPali 프로세서 (선택적)
            if self.enable_colpali:
                try:
                    from backend.services.colpali_processor import get_colpali_processor
                    from backend.services.colpali_milvus_service import get_colpali_milvus_service
                    from backend.config import settings
                    
                    self.colpali_processor = get_colpali_processor(
                        model_name=settings.COLPALI_MODEL,
                        use_gpu=settings.COLPALI_USE_GPU,
                        enable_binarization=settings.COLPALI_ENABLE_BINARIZATION,
                        enable_pooling=settings.COLPALI_ENABLE_POOLING,
                        pooling_factor=settings.COLPALI_POOLING_FACTOR
                    )
                    self.colpali_milvus = get_colpali_milvus_service()
                    
                    if self.colpali_processor:
                        model_info = self.colpali_processor.get_model_info()
                        logger.info(f"✅ ColPali processor initialized on {model_info['device']}")
                    else:
                        logger.warning("⚠️  ColPali processor returned None")
                        self.enable_colpali = False
                except Exception as e:
                    logger.warning(f"⚠️  ColPali not available: {e}")
                    self.enable_colpali = False
            
        except Exception as e:
            logger.error(f"Failed to initialize processors: {e}")
            raise
    
    async def process_document(
        self,
        file_path: str,
        file_type: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        하이브리드 문서 처리
        
        Args:
            file_path: 파일 경로
            file_type: 파일 타입
            document_id: 문서 ID
            metadata: 메타데이터
        
        Returns:
            처리 결과
        """
        # Docling 사용 시
        if self.use_docling and self.docling_processor:
            return await self._process_with_docling(
                file_path, file_type, document_id, metadata
            )
        
        # Legacy 처리
        return await self._process_legacy(
            file_path, file_type, document_id, metadata
        )
    
    async def _process_with_docling(
        self,
        file_path: str,
        file_type: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Docling을 사용한 문서 처리"""
        try:
            logger.info(f"🚀 Processing with Docling: {document_id}")
            
            # 사용자 ID 추출
            user_id = (metadata or {}).get('user_id', 'unknown')
            
            # Docling 처리
            docling_result = await self.docling_processor.process_document(
                file_path=file_path,
                document_id=document_id,
                user_id=user_id,
                metadata=metadata
            )
            
            # 표 데이터를 Milvus에 저장
            if self.structured_data_service and docling_result.get('tables'):
                logger.info(f"💾 Saving {len(docling_result['tables'])} tables to Milvus...")
                for table in docling_result['tables']:
                    try:
                        self.structured_data_service.insert_table(
                            table_id=table['table_id'],
                            document_id=table['document_id'],
                            user_id=table['user_id'],
                            page_number=table['page_number'],
                            caption=table['caption'],
                            searchable_text=table['searchable_text'],
                            table_data=table['data'],
                            bbox=table.get('bbox'),
                            metadata=table.get('metadata')
                        )
                    except Exception as e:
                        logger.error(f"Failed to save table {table['table_id']}: {e}")
            
            # 결과 변환 (기존 형식과 호환)
            result = {
                'document_id': document_id,
                'file_type': file_type,
                'processing_method': 'docling',
                'native_text': self._combine_text_chunks(docling_result.get('text_chunks', [])),
                'native_chunks': docling_result.get('text_chunks', []),
                'tables': docling_result.get('tables', []),
                'figures': docling_result.get('figures', []),
                'colpali_processed': any(
                    fig.get('colpali_processed', False)
                    for fig in docling_result.get('figures', [])
                ),
                'colpali_patches': sum(
                    fig.get('colpali_patches', 0)
                    for fig in docling_result.get('figures', [])
                ),
                'layout': docling_result.get('layout', {}),
                'metadata': docling_result.get('metadata', {}),
                'stats': docling_result.get('stats', {})
            }
            
            logger.info(
                f"✅ Docling processing complete: "
                f"{result['stats'].get('num_text_chunks', 0)} chunks, "
                f"{result['stats'].get('num_tables', 0)} tables, "
                f"{result['stats'].get('num_figures', 0)} figures"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Docling processing failed: {e}")
            logger.warning("Falling back to legacy processing")
            return await self._process_legacy(file_path, file_type, document_id, metadata)
    
    def _combine_text_chunks(self, chunks: List[Dict]) -> str:
        """텍스트 청크를 하나의 문자열로 결합"""
        return '\n\n'.join(chunk.get('text', '') for chunk in chunks)
    
    async def _process_legacy(
        self,
        file_path: str,
        file_type: str,
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Legacy 문서 처리 (기존 방식)"""
        result = {
            'document_id': document_id,
            'file_type': file_type,
            'native_text': None,
            'native_chunks': [],
            'colpali_processed': False,
            'colpali_patches': 0,
            'is_scanned': False,
            'processing_method': None,
            'text_ratio': 0.0
        }
        
        try:
            # 1단계: Native 텍스트 추출 (항상 시도)
            logger.info(f"Step 1: Native text extraction for {document_id}")
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            native_text = self.doc_processor.extract_text(file_content, file_type)
            result['native_text'] = native_text
            
            # 텍스트 품질 분석
            text_ratio = self._analyze_text_quality(native_text, file_content)
            result['text_ratio'] = text_ratio
            
            logger.info(
                f"Native text extracted: {len(native_text)} chars, "
                f"text_ratio={text_ratio:.2f}"
            )
            
            # 2단계: 이미지 파일 형식 확인
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.tiff'}
            file_ext = Path(file_path).suffix.lower()
            is_image_file = file_ext in image_extensions
            
            logger.info(f"📄 File analysis: ext={file_ext}, is_image={is_image_file}")
            
            # 2.5단계: 스캔본 여부 판단
            is_scanned = text_ratio < self.colpali_threshold
            result['is_scanned'] = is_scanned
            
            if is_scanned:
                logger.info(f"📋 Document {document_id} detected as scanned (text_ratio={text_ratio:.2f})")
            
            if is_image_file:
                logger.info(f"🖼️  Document {document_id} is an image file ({file_ext})")
            
            # 3단계: ColPali 처리 결정
            should_use_colpali = False
            
            logger.info(f"🔍 ColPali check: enabled={self.enable_colpali}, processor_available={self.colpali_processor is not None}")
            
            if self.enable_colpali and self.colpali_processor:
                # 이미지 파일이면 무조건 ColPali 처리
                if is_image_file:
                    should_use_colpali = True
                    result['processing_method'] = 'colpali_only'
                    logger.info("✅ Using ColPali (image file)")
                    
                elif is_scanned:
                    # 스캔본이면 ColPali 필수
                    should_use_colpali = True
                    result['processing_method'] = 'colpali_only'
                    logger.info("✅ Using ColPali (scanned document)")
                    
                elif self.process_images_always:
                    # 하이브리드 모드: 둘 다 사용
                    should_use_colpali = True
                    result['processing_method'] = 'hybrid'
                    logger.info("✅ Using Hybrid (Native + ColPali)")
                    
                else:
                    # Native만 사용
                    result['processing_method'] = 'native_only'
                    logger.info("ℹ️  Using Native only (good text quality)")
            else:
                result['processing_method'] = 'native_only'
                logger.warning("⚠️  ColPali not available - using Native only")
            
            # 4단계: ColPali 처리 (필요시)
            if should_use_colpali:
                logger.info(f"🚀 Step 2: ColPali processing for {document_id}")
                
                try:
                    # PDF를 이미지로 변환 (필요시)
                    if file_type == 'pdf':
                        logger.info(f"📄 Converting PDF to images...")
                        image_paths = await self._pdf_to_images(file_path)
                    else:
                        # 이미지 파일은 그대로 사용
                        image_paths = [file_path]
                        logger.info(f"🖼️  Using image file directly: {file_path}")
                    
                    # ColPali로 이미지 처리
                    total_patches = 0
                    for i, img_path in enumerate(image_paths, 1):
                        logger.info(f"🔄 Processing image {i}/{len(image_paths)}: {Path(img_path).name}")
                        colpali_result = self.colpali_processor.process_image(img_path)
                        
                        # Milvus에 저장
                        if colpali_result.get('embeddings') is not None:
                            # Extract user_id from metadata
                            user_id = (metadata or {}).get('user_id', 'unknown')
                            
                            # Phase 2: Extract associated text
                            # For images, use native_text as context
                            # For PDFs, could extract text from same page
                            associated_text = native_text[:5000] if native_text else ""
                            
                            # Extract page number if available
                            page_number = (metadata or {}).get('page_number', i)
                            
                            await self.colpali_milvus.insert_image(
                                image_path=img_path,
                                embeddings=colpali_result['embeddings'],
                                document_id=document_id,
                                user_id=user_id,
                                metadata={
                                    'file_type': file_type,
                                    'is_scanned': is_scanned,
                                    'text_ratio': text_ratio,
                                    'image_index': i,
                                    **(metadata or {})
                                },
                                page_number=page_number,  # Phase 2
                                associated_text=associated_text  # Phase 2
                            )
                            patches = colpali_result.get('num_patches', 0)
                            total_patches += patches
                            logger.info(f"   ✓ Saved {patches} patches to Milvus")
                    
                    result['colpali_processed'] = True
                    result['colpali_patches'] = total_patches
                    
                    logger.info(
                        f"✅ ColPali processing completed: {total_patches} patches"
                    )
                    
                except Exception as e:
                    logger.error(f"ColPali processing failed: {e}")
                    # ColPali 실패해도 Native 텍스트는 사용 가능
            
            # 5단계: 텍스트 청킹 (Native 텍스트)
            if native_text and native_text.strip():
                chunks = self.doc_processor.chunk_text(native_text, document_id)
                result['native_chunks'] = chunks
                logger.info(f"Created {len(chunks)} chunks from native text")
            
            return result
            
        except Exception as e:
            logger.error(f"Hybrid document processing failed: {e}")
            raise
    
    def _analyze_text_quality(self, text: str, file_content: bytes) -> float:
        """
        텍스트 품질 분석 (스캔본 감지)
        
        Args:
            text: 추출된 텍스트
            file_content: 원본 파일 내용
        
        Returns:
            텍스트 비율 (0.0 ~ 1.0)
        """
        if not text or not text.strip():
            return 0.0
        
        # 텍스트 길이 대비 파일 크기 비율
        text_bytes = len(text.encode('utf-8'))
        file_bytes = len(file_content)
        
        if file_bytes == 0:
            return 0.0
        
        # 비율 계산 (정규화)
        ratio = min(text_bytes / file_bytes, 1.0)
        
        # 추가 휴리스틱
        # - 텍스트가 너무 짧으면 스캔본일 가능성
        if len(text.strip()) < 100:
            ratio *= 0.5
        
        # - 특수문자/공백이 너무 많으면 OCR 오류일 가능성
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        if len(text) > 0 and special_chars / len(text) > 0.3:
            ratio *= 0.7
        
        return ratio
    
    async def _pdf_to_images(self, pdf_path: str) -> List[str]:
        """
        PDF를 이미지로 변환
        
        Args:
            pdf_path: PDF 파일 경로
        
        Returns:
            이미지 파일 경로 리스트
        """
        try:
            from pdf2image import convert_from_path
            import tempfile
            import os
            
            # PDF를 이미지로 변환
            images = convert_from_path(pdf_path, dpi=200)
            
            # 임시 파일로 저장
            image_paths = []
            temp_dir = tempfile.mkdtemp()
            
            for i, image in enumerate(images):
                img_path = os.path.join(temp_dir, f"page_{i+1}.png")
                image.save(img_path, 'PNG')
                image_paths.append(img_path)
            
            logger.info(f"Converted PDF to {len(image_paths)} images")
            return image_paths
            
        except ImportError:
            logger.warning("pdf2image not available, using PDF as-is")
            return [pdf_path]
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            return [pdf_path]
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        return {
            'use_docling': self.use_docling,
            'docling_available': self.docling_processor is not None,
            'enable_colpali': self.enable_colpali,
            'colpali_threshold': self.colpali_threshold,
            'process_images_always': self.process_images_always,
            'colpali_available': self.colpali_processor is not None,
            'structured_data_available': self.structured_data_service is not None
        }


# Global instance
_hybrid_processor: Optional[HybridDocumentProcessor] = None


def get_hybrid_document_processor(
    use_docling: bool = True,
    enable_colpali: bool = True,
    colpali_threshold: float = 0.3,
    process_images_always: bool = False
) -> HybridDocumentProcessor:
    """Get global hybrid document processor instance"""
    global _hybrid_processor
    
    if _hybrid_processor is None:
        _hybrid_processor = HybridDocumentProcessor(
            use_docling=use_docling,
            enable_colpali=enable_colpali,
            colpali_threshold=colpali_threshold,
            process_images_always=process_images_always
        )
    
    return _hybrid_processor
