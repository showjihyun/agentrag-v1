# HWP/HWPX Processor Wrapper
"""
HWP/HWPX 처리를 위한 통합 래퍼

기본 파서와 고급 파서를 자동으로 선택하여 사용합니다.
"""

import logging
from typing import Dict, List
from backend.services.document_processor import DocumentProcessor
from backend.services.advanced_hwp_parser import get_advanced_hwp_parser
from backend.services.korean_text_processor import get_korean_text_processor

logger = logging.getLogger(__name__)


class HWPProcessorWrapper:
    """
    HWP/HWPX 처리 통합 래퍼
    
    Features:
    - 자동 파서 선택 (고급 → 기본)
    - 한글 텍스트 처리
    - 구조 정보 보존
    - 메타데이터 추출
    """
    
    def __init__(
        self,
        document_processor: DocumentProcessor,
        use_advanced_parser: bool = True,
        use_korean_processor: bool = True
    ):
        self.document_processor = document_processor
        self.use_advanced_parser = use_advanced_parser
        self.use_korean_processor = use_korean_processor
        
        # 고급 파서 초기화
        if use_advanced_parser:
            self.advanced_parser = get_advanced_hwp_parser()
        else:
            self.advanced_parser = None
        
        # 한글 처리기 초기화
        if use_korean_processor:
            self.korean_processor = get_korean_text_processor()
        else:
            self.korean_processor = None
        
        logger.info(
            f"HWPProcessorWrapper initialized: "
            f"advanced_parser={use_advanced_parser}, "
            f"korean_processor={use_korean_processor}"
        )
    
    def process_hwp(self, file_content: bytes, filename: str) -> Dict:
        """
        HWP 파일 처리
        
        Args:
            file_content: HWP 파일 바이트
            filename: 파일명
        
        Returns:
            {
                'text': str,
                'chunks': List[Dict],
                'metadata': Dict,
                'processing_method': str
            }
        """
        processing_method = "basic"
        
        try:
            # 1. 고급 파서 시도
            if self.advanced_parser and self.advanced_parser.hwp5_available:
                if self.advanced_parser.can_parse(file_content):
                    logger.info(f"Using advanced HWP parser for {filename}")
                    result = self._process_with_advanced_parser(file_content)
                    processing_method = "advanced"
                    return {
                        **result,
                        'processing_method': processing_method
                    }
            
            # 2. 기본 파서 사용
            logger.info(f"Using basic HWP parser for {filename}")
            text = self.document_processor.extract_text_from_hwp(file_content)
            
            # 한글 처리
            if self.korean_processor:
                processed = self.korean_processor.process_korean_text(text)
                text = processed['normalized']
            
            return {
                'text': text,
                'chunks': self._create_basic_chunks(text),
                'metadata': {},
                'processing_method': processing_method
            }
            
        except Exception as e:
            logger.error(f"HWP processing failed: {e}")
            raise
    
    def process_hwpx(self, file_content: bytes, filename: str) -> Dict:
        """
        HWPX 파일 처리
        
        Args:
            file_content: HWPX 파일 바이트
            filename: 파일명
        
        Returns:
            {
                'text': str,
                'chunks': List[Dict],
                'metadata': Dict,
                'processing_method': str
            }
        """
        try:
            # HWPX는 기본 파서 사용 (XML 기반이라 이미 구조화됨)
            logger.info(f"Processing HWPX file: {filename}")
            text = self.document_processor.extract_text_from_hwpx(file_content)
            
            # 한글 처리
            if self.korean_processor:
                processed = self.korean_processor.process_korean_text(text)
                text = processed['normalized']
            
            return {
                'text': text,
                'chunks': self._create_basic_chunks(text),
                'metadata': {},
                'processing_method': 'basic'
            }
            
        except Exception as e:
            logger.error(f"HWPX processing failed: {e}")
            raise
    
    def _process_with_advanced_parser(self, file_content: bytes) -> Dict:
        """고급 파서로 처리"""
        # 구조 정보 포함 추출
        parsed = self.advanced_parser.extract_with_structure(file_content)
        
        # 한글 처리
        if self.korean_processor:
            processed = self.korean_processor.process_korean_text(parsed['text'])
            parsed['text'] = processed['normalized']
            
            # 각 문단도 처리
            for para in parsed['paragraphs']:
                para_processed = self.korean_processor.process_korean_text(para['text'])
                para['text'] = para_processed['normalized']
                para['keywords'] = para_processed.get('keywords', [])
        
        # 구조 인식 청킹
        chunks = self._create_structured_chunks(parsed)
        
        return {
            'text': parsed['text'],
            'chunks': chunks,
            'metadata': parsed['metadata'],
            'structure': parsed['structure']
        }
    
    def _create_structured_chunks(self, parsed: Dict) -> List[Dict]:
        """구조 인식 청킹"""
        chunks = []
        
        paragraphs = parsed['paragraphs']
        tables = parsed['tables']
        
        current_section = None
        current_chunk_text = []
        current_chunk_size = 0
        target_size = 500
        overlap_size = 50
        
        for para_idx, para in enumerate(paragraphs):
            # 제목 감지
            if para['is_heading']:
                # 이전 청크 저장
                if current_chunk_text:
                    chunk = {
                        'chunk_id': f"para_{para_idx}",
                        'text': "\n".join(current_chunk_text),
                        'type': 'paragraph',
                        'section_title': current_section,
                        'metadata': {
                            'paragraph_index': para_idx,
                            'has_structure': True
                        }
                    }
                    chunks.append(chunk)
                    current_chunk_text = []
                    current_chunk_size = 0
                
                # 새 섹션 시작
                current_section = para['text']
            
            # 문단 추가
            para_text = para['text']
            para_size = len(para_text)
            
            # 청크 크기 체크
            if current_chunk_size + para_size > target_size:
                # 현재 청크 저장
                if current_chunk_text:
                    chunk = {
                        'chunk_id': f"para_{para_idx}",
                        'text': "\n".join(current_chunk_text),
                        'type': 'paragraph',
                        'section_title': current_section,
                        'metadata': {
                            'paragraph_index': para_idx,
                            'has_structure': True
                        }
                    }
                    chunks.append(chunk)
                
                # 새 청크 시작 (오버랩)
                if overlap_size > 0 and current_chunk_text:
                    overlap_text = current_chunk_text[-1]
                    current_chunk_text = [overlap_text, para_text]
                    current_chunk_size = len(overlap_text) + para_size
                else:
                    current_chunk_text = [para_text]
                    current_chunk_size = para_size
            else:
                current_chunk_text.append(para_text)
                current_chunk_size += para_size
        
        # 마지막 청크
        if current_chunk_text:
            chunk = {
                'chunk_id': f"para_final",
                'text': "\n".join(current_chunk_text),
                'type': 'paragraph',
                'section_title': current_section,
                'metadata': {
                    'paragraph_index': len(paragraphs),
                    'has_structure': True
                }
            }
            chunks.append(chunk)
        
        # 테이블 청크 추가
        for table_idx, table in enumerate(tables):
            table_text = self._format_table_for_rag(table)
            
            chunk = {
                'chunk_id': f"table_{table_idx}",
                'text': table_text,
                'type': 'table',
                'section_title': current_section,
                'metadata': {
                    'table_index': table_idx,
                    'rows': table['rows'],
                    'cols': table['cols'],
                    'has_header': table['has_header'],
                    'caption': table.get('caption', '')
                }
            }
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} structured chunks")
        
        return chunks
    
    def _create_basic_chunks(self, text: str) -> List[Dict]:
        """기본 청킹 (구조 정보 없음)"""
        chunks = []
        
        # 간단한 문단 기반 청킹
        paragraphs = text.split('\n\n')
        
        current_chunk = []
        current_size = 0
        target_size = 500
        
        for para_idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            
            para_size = len(para)
            
            if current_size + para_size > target_size:
                if current_chunk:
                    chunk = {
                        'chunk_id': f"chunk_{para_idx}",
                        'text': "\n\n".join(current_chunk),
                        'type': 'paragraph',
                        'metadata': {
                            'paragraph_index': para_idx
                        }
                    }
                    chunks.append(chunk)
                
                current_chunk = [para]
                current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # 마지막 청크
        if current_chunk:
            chunk = {
                'chunk_id': f"chunk_final",
                'text': "\n\n".join(current_chunk),
                'type': 'paragraph',
                'metadata': {
                    'paragraph_index': len(paragraphs)
                }
            }
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} basic chunks")
        
        return chunks
    
    def _format_table_for_rag(self, table: Dict) -> str:
        """RAG 최적화 테이블 포맷팅"""
        lines = []
        
        # 캡션
        if table.get('caption'):
            lines.append(f"[테이블: {table['caption']}]")
        
        # 헤더
        if table['has_header'] and table['cells']:
            headers = table['cells'][0]
            lines.append("헤더: " + ", ".join(headers))
            
            # 데이터 행
            for row in table['cells'][1:]:
                row_text = " | ".join(
                    f"{headers[i]}: {cell}" 
                    for i, cell in enumerate(row) 
                    if i < len(headers)
                )
                lines.append(row_text)
        else:
            # 헤더 없는 테이블
            for row in table['cells']:
                lines.append(" | ".join(row))
        
        return "\n".join(lines)


# Global instance
_hwp_processor_wrapper = None


def get_hwp_processor_wrapper(
    document_processor: DocumentProcessor = None,
    use_advanced_parser: bool = True,
    use_korean_processor: bool = True
) -> HWPProcessorWrapper:
    """Get global HWP processor wrapper instance"""
    global _hwp_processor_wrapper
    if _hwp_processor_wrapper is None:
        if document_processor is None:
            document_processor = DocumentProcessor()
        _hwp_processor_wrapper = HWPProcessorWrapper(
            document_processor=document_processor,
            use_advanced_parser=use_advanced_parser,
            use_korean_processor=use_korean_processor
        )
    return _hwp_processor_wrapper
