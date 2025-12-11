"""
Docling Document Processor

IBM Research의 Docling을 사용한 고급 문서 처리
- 표/차트 자동 추출
- 레이아웃 분석
- 구조화된 데이터 추출
- ColPali 통합
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import asyncio

logger = logging.getLogger(__name__)


class DoclingProcessor:
    """
    Docling 기반 문서 처리기
    
    Features:
    - PDF/DOCX/PPTX 지원
    - 표 구조 추출
    - 차트/그림 감지
    - 레이아웃 분석
    - OCR 통합
    - ColPali 연동
    """
    
    def __init__(
        self,
        enable_ocr: bool = True,
        enable_table_structure: bool = True,
        enable_figure_extraction: bool = True,
        images_scale: float = 2.0
    ):
        """
        초기화
        
        Args:
            enable_ocr: OCR 활성화
            enable_table_structure: 표 구조 분석
            enable_figure_extraction: 그림/차트 추출
            images_scale: 이미지 해상도 배율
        """
        self.enable_ocr = enable_ocr
        self.enable_table_structure = enable_table_structure
        self.enable_figure_extraction = enable_figure_extraction
        self.images_scale = images_scale
        
        self.converter = None
        
        self._init_docling()
        self._init_colpali()
        
        logger.info(
            f"DoclingProcessor initialized: "
            f"ocr={enable_ocr}, tables={enable_table_structure}, "
            f"figures={enable_figure_extraction}, scale={images_scale}"
        )
    
    def _init_docling(self):
        """Docling 초기화"""
        try:
            from docling.document_converter import DocumentConverter
            
            # Docling 2.x에서는 간단한 초기화만 필요
            # Pipeline 옵션은 convert() 호출 시 전달
            self.converter = DocumentConverter()
            
            logger.info("✅ Docling converter initialized")
            logger.info(f"   - OCR: {self.enable_ocr}")
            logger.info(f"   - Table structure: {self.enable_table_structure}")
            logger.info(f"   - Figure extraction: {self.enable_figure_extraction}")
            
        except ImportError as e:
            logger.error(f"❌ Docling not installed: {e}")
            logger.error("Install with: pip install docling")
            raise
        except Exception as e:
            logger.error(f"❌ Docling initialization failed: {e}")
            raise
    
    def _init_colpali(self):
        """ColPali removed - not used"""
        try:
            # ColPali initialization removed
            pass
            
            if False:
                logger.info("✅ ColPali integration enabled")
            else:
                logger.warning("⚠️  ColPali not available")
                
        except Exception as e:
            logger.warning(f"⚠️  ColPali initialization failed: {e}")
    
    async def process_document(
        self,
        file_path: str,
        document_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        문서 처리 (Docling)
        
        Args:
            file_path: 파일 경로
            document_id: 문서 ID
            user_id: 사용자 ID
            metadata: 추가 메타데이터
        
        Returns:
            {
                'document_id': str,
                'user_id': str,
                'text_chunks': List[Dict],  # 텍스트 청크
                'tables': List[Dict],       # 추출된 표
                'figures': List[Dict],      # 추출된 그림/차트
                'layout': Dict,             # 레이아웃 정보
                'metadata': Dict,           # 문서 메타데이터
                'stats': Dict               # 처리 통계
            }
        """
        try:
            logger.info(f"🚀 Processing document with Docling: {document_id}")
            
            # Docling 변환
            result = self.converter.convert(file_path)
            
            # 결과 구조 초기화
            processed = {
                'document_id': document_id,
                'user_id': user_id,
                'text_chunks': [],
                'tables': [],
                'figures': [],
                'layout': {},
                'metadata': metadata or {},
                'stats': {}
            }
            
            # 1. 텍스트 청크 추출
            logger.info("📝 Extracting text chunks...")
            processed['text_chunks'] = self._extract_text_chunks(
                result, document_id, user_id
            )
            
            # 2. 표 추출
            logger.info("📊 Extracting tables...")
            processed['tables'] = self._extract_tables(
                result, document_id, user_id
            )
            
            # 3. 그림/차트 추출
            if self.enable_figure_extraction:
                logger.info("🖼️  Extracting figures...")
                processed['figures'] = await self._extract_figures(
                    result, document_id, user_id, file_path
                )
            
            # 4. 레이아웃 정보
            processed['layout'] = self._extract_layout(result)
            
            # 5. 문서 메타데이터
            doc_metadata = self._extract_metadata(result)
            processed['metadata'].update(doc_metadata)
            
            # 6. 통계
            processed['stats'] = {
                'num_text_chunks': len(processed['text_chunks']),
                'num_tables': len(processed['tables']),
                'num_figures': len(processed['figures']),
                'num_pages': processed['layout'].get('num_pages', 0)
            }
            
            logger.info(
                f"✅ Docling processing complete: "
                f"{processed['stats']['num_text_chunks']} chunks, "
                f"{processed['stats']['num_tables']} tables, "
                f"{processed['stats']['num_figures']} figures"
            )
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Docling processing failed: {e}")
            raise
    
    def _extract_text_chunks(
        self,
        result,
        document_id: str,
        user_id: str
    ) -> List[Dict]:
        """텍스트 청크 추출 (의미 단위)"""
        chunks = []
        
        try:
            # Docling 2.x: result.document.export_to_markdown() 또는 직접 텍스트 추출
            if hasattr(result, 'document'):
                doc = result.document
                
                # 전체 텍스트 추출
                if hasattr(doc, 'export_to_markdown'):
                    full_text = doc.export_to_markdown()
                elif hasattr(doc, 'export_to_text'):
                    full_text = doc.export_to_text()
                else:
                    full_text = str(doc)
                
                # 간단한 청킹 (단락 단위)
                paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
                
                for i, text in enumerate(paragraphs):
                    if len(text) < 10:  # 너무 짧은 텍스트 제외
                        continue
                    
                    chunks.append({
                        'chunk_id': f"{document_id}_chunk_{len(chunks)}",
                        'document_id': document_id,
                        'user_id': user_id,
                        'text': text,
                        'type': 'paragraph',
                        'page_number': 1,  # TODO: 페이지 번호 추출
                        'bbox': None,
                        'metadata': {
                            'level': None,
                            'is_heading': text.startswith('#'),
                            'char_count': len(text)
                        }
                    })
            
            logger.info(f"   ✓ Extracted {len(chunks)} text chunks")
            
        except Exception as e:
            logger.error(f"Text chunk extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return chunks
    
    def _extract_tables(
        self,
        result,
        document_id: str,
        user_id: str
    ) -> List[Dict]:
        """표 추출 (구조화된 데이터)"""
        tables = []
        
        try:
            # Docling 2.x: result.document.tables 또는 export_to_dict()
            if hasattr(result, 'document'):
                doc = result.document
                
                # 표 추출 시도
                if hasattr(doc, 'tables'):
                    for i, table in enumerate(doc.tables):
                        table_data = self._parse_table_v2(table)
                        
                        if not table_data or not table_data.get('rows'):
                            continue
                        
                        searchable_text = self._table_to_text(table_data, "")
                        
                        tables.append({
                            'table_id': f"{document_id}_table_{len(tables)}",
                            'document_id': document_id,
                            'user_id': user_id,
                            'page_number': 1,  # TODO: 페이지 번호
                            'bbox': None,
                            'caption': "",
                            'data': table_data,
                            'searchable_text': searchable_text,
                            'metadata': {
                                'num_rows': len(table_data.get('rows', [])),
                                'num_cols': len(table_data.get('headers', [])),
                                'has_caption': False
                            }
                        })
            
            logger.info(f"   ✓ Extracted {len(tables)} tables")
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return tables
    
    async def _extract_figures(
        self,
        result,
        document_id: str,
        user_id: str,
        original_file_path: str
    ) -> List[Dict]:
        """그림/차트 추출 (ColPali 통합)"""
        figures = []
        
        try:
            # Docling 2.x: result.document.pictures 또는 images
            if hasattr(result, 'document'):
                doc = result.document
                
                # 이미지 추출 시도
                if hasattr(doc, 'pictures'):
                    for i, picture in enumerate(doc.pictures):
                        figures.append({
                            'figure_id': f"{document_id}_figure_{len(figures)}",
                            'document_id': document_id,
                            'user_id': user_id,
                            'page_number': 1,  # TODO: 페이지 번호
                            'bbox': None,
                            'caption': "",
                            'image_path': None,
                            'colpali_processed': False,
                            'colpali_patches': 0,
                            'metadata': {
                                'type': 'picture',
                                'has_caption': False
                            }
                        })
            
            logger.info(f"   ✓ Extracted {len(figures)} figures")
            
        except Exception as e:
            logger.error(f"Figure extraction failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        return figures
    
    def _parse_table_v2(self, table) -> Dict:
        """Docling 2.x 표 데이터 파싱"""
        try:
            table_data = {'headers': [], 'rows': []}
            
            # 표를 문자열로 변환하여 파싱
            if hasattr(table, 'export_to_markdown'):
                md_text = table.export_to_markdown()
                lines = [l.strip() for l in md_text.split('\n') if l.strip() and not l.strip().startswith('|--')]
                
                if lines:
                    # 첫 줄은 헤더
                    table_data['headers'] = [h.strip() for h in lines[0].split('|') if h.strip()]
                    # 나머지는 행
                    table_data['rows'] = [
                        [cell.strip() for cell in line.split('|') if cell.strip()]
                        for line in lines[1:]
                    ]
            
            return table_data
            
        except Exception as e:
            logger.warning(f"Table v2 parsing failed: {e}")
            return {'headers': [], 'rows': []}
    
    def _parse_table(self, table_element) -> Dict:
        """표 데이터 파싱"""
        try:
            # Docling의 표 구조 접근
            table_data = {'headers': [], 'rows': []}
            
            # 표 데이터가 있는지 확인
            if hasattr(table_element, 'data'):
                data = table_element.data
                
                # 헤더 추출
                if hasattr(data, 'headers'):
                    table_data['headers'] = data.headers
                elif hasattr(data, 'header'):
                    table_data['headers'] = data.header
                
                # 행 추출
                if hasattr(data, 'rows'):
                    table_data['rows'] = data.rows
                elif hasattr(data, 'body'):
                    table_data['rows'] = data.body
            
            # 텍스트에서 파싱 (fallback)
            elif hasattr(table_element, 'text'):
                lines = table_element.text.strip().split('\n')
                if lines:
                    table_data['headers'] = [h.strip() for h in lines[0].split('|')]
                    table_data['rows'] = [
                        [cell.strip() for cell in line.split('|')]
                        for line in lines[1:]
                    ]
            
            return table_data
            
        except Exception as e:
            logger.warning(f"Table parsing failed: {e}")
            return {'headers': [], 'rows': []}
    
    def _table_to_text(self, table_data: Dict, caption: str = "") -> str:
        """표를 검색 가능한 텍스트로 변환"""
        lines = []
        
        # 캡션
        if caption:
            lines.append(f"Caption: {caption}")
        
        # 헤더
        if table_data.get('headers'):
            lines.append(' | '.join(str(h) for h in table_data['headers']))
            lines.append('-' * 50)
        
        # 행
        for row in table_data.get('rows', []):
            lines.append(' | '.join(str(cell) for cell in row))
        
        return '\n'.join(lines)
    
    def _find_caption(self, page, element, element_type: str) -> str:
        """표/그림의 캡션 찾기"""
        try:
            element_bbox = self._get_bbox(element)
            if not element_bbox:
                return ""
            
            caption_candidates = []
            
            for other_element in page.elements:
                # 캡션 또는 텍스트 요소
                if other_element.type in ['caption', 'paragraph', 'text']:
                    text = getattr(other_element, 'text', '').strip()
                    
                    if not text:
                        continue
                    
                    # "표 1:", "Figure 2:" 등의 패턴 확인
                    is_caption = any(
                        keyword in text.lower()
                        for keyword in ['table', '표', 'figure', '그림', 'chart', '차트']
                    )
                    
                    if is_caption or other_element.type == 'caption':
                        other_bbox = self._get_bbox(other_element)
                        if other_bbox:
                            distance = self._calculate_distance(element_bbox, other_bbox)
                            caption_candidates.append((distance, text))
            
            # 가장 가까운 캡션 반환
            if caption_candidates:
                caption_candidates.sort(key=lambda x: x[0])
                return caption_candidates[0][1]
            
        except Exception as e:
            logger.warning(f"Caption finding failed: {e}")
        
        return ""
    
    def _get_bbox(self, element) -> Optional[List[float]]:
        """요소의 bbox 가져오기"""
        try:
            if hasattr(element, 'bbox'):
                bbox = element.bbox
                if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                    return list(bbox)
            
            if hasattr(element, 'bounding_box'):
                bbox = element.bounding_box
                if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                    return list(bbox)
        except:
            pass
        
        return None
    
    def _calculate_distance(self, bbox1: List[float], bbox2: List[float]) -> float:
        """두 bbox 간 거리 계산"""
        try:
            # 중심점 간 거리
            center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
            center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)
            
            return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
        except:
            return float('inf')
    
    def _get_image_path(self, element, original_file_path: str, page_num: int) -> Optional[str]:
        """이미지 경로 가져오기"""
        try:
            # Docling이 추출한 이미지 경로
            if hasattr(element, 'image_path'):
                return element.image_path
            
            if hasattr(element, 'image'):
                return element.image
            
            # Fallback: 원본 파일에서 추출 필요
            # TODO: pdf2image로 페이지 추출
            
        except Exception as e:
            logger.warning(f"Image path extraction failed: {e}")
        
        return None
    
    async def _process_with_colpali(
        self,
        image_path: str,
        document_id: str,
        user_id: str,
        page_number: int,
        caption: str
    ) -> Optional[Dict]:
        """ColPali로 이미지 처리"""
        try:
            # 임베딩 생성
            result = self.colpali_processor.process_image(image_path)
            
            if result.get('embeddings') is None:
                return None
            
            # Milvus 저장
            await self.colpali_milvus.insert_image(
                image_path=image_path,
                embeddings=result['embeddings'],
                document_id=document_id,
                user_id=user_id,
                page_number=page_number,
                associated_text=caption[:5000] if caption else ""
            )
            
            logger.info(f"      ✓ ColPali processed: {result.get('num_patches', 0)} patches")
            
            return result
            
        except Exception as e:
            logger.warning(f"ColPali processing failed: {e}")
            return None
    
    def _extract_layout(self, result) -> Dict:
        """레이아웃 정보 추출"""
        try:
            return {
                'num_pages': len(result.pages),
                'page_sizes': [
                    {
                        'width': getattr(page, 'width', 0),
                        'height': getattr(page, 'height', 0)
                    }
                    for page in result.pages
                ]
            }
        except:
            return {'num_pages': 0, 'page_sizes': []}
    
    def _extract_metadata(self, result) -> Dict:
        """문서 메타데이터 추출"""
        try:
            return {
                'title': getattr(result, 'title', ''),
                'author': getattr(result, 'author', ''),
                'creation_date': str(getattr(result, 'creation_date', '')),
                'num_pages': len(result.pages)
            }
        except:
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """프로세서 통계"""
        return {
            'docling_available': self.converter is not None,
            'colpali_available': self.colpali_processor is not None,
            'enable_ocr': self.enable_ocr,
            'enable_table_structure': self.enable_table_structure,
            'enable_figure_extraction': self.enable_figure_extraction,
            'images_scale': self.images_scale
        }


# Global instance
_docling_processor: Optional[DoclingProcessor] = None


def get_docling_processor(
    enable_ocr: bool = True,
    enable_table_structure: bool = True,
    enable_figure_extraction: bool = True,
    images_scale: float = 2.0
) -> DoclingProcessor:
    """Get global Docling processor instance"""
    global _docling_processor
    
    if _docling_processor is None:
        _docling_processor = DoclingProcessor(
            enable_ocr=enable_ocr,
            enable_table_structure=enable_table_structure,
            enable_figure_extraction=enable_figure_extraction,
            images_scale=images_scale
        )
    
    return _docling_processor
