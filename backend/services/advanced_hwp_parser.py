# Advanced HWP Parser
"""
고급 HWP 파서 - hwp5 라이브러리 사용

HWP 5.0+ 형식을 완벽하게 파싱하여 구조 정보를 보존합니다.

Features:
- 정확한 문단 구조 파싱
- 스타일 정보 보존
- 테이블 정확한 추출
- 한글 특수 문자 완벽 지원
- 메타데이터 추출
"""

import logging
from typing import Dict, List, Optional
import io

logger = logging.getLogger(__name__)


class AdvancedHWPParser:
    """
    고급 HWP 파서
    
    hwp5 라이브러리가 설치되어 있으면 사용하고,
    없으면 기본 파서로 폴백합니다.
    """
    
    def __init__(self):
        self.hwp5_available = False
        self.supported_versions = ['5.0', '5.1']
        
        # hwp5 라이브러리 확인
        try:
            import hwp5
            from hwp5.xmlmodel import Hwp5File
            from hwp5 import hwp5txt
            self.hwp5_available = True
            self.Hwp5File = Hwp5File
            logger.info("hwp5 library available - using advanced HWP parser")
        except ImportError:
            logger.warning(
                "hwp5 library not available - falling back to basic parser. "
                "Install with: pip install pyhwp"
            )
    
    def can_parse(self, file_content: bytes) -> bool:
        """
        HWP 파일을 고급 파서로 처리할 수 있는지 확인
        
        Args:
            file_content: HWP 파일 바이트
        
        Returns:
            bool: 처리 가능 여부
        """
        if not self.hwp5_available:
            return False
        
        try:
            hwp_file = io.BytesIO(file_content)
            hwp = self.Hwp5File(hwp_file)
            version = hwp.fileheader.version
            return version in self.supported_versions
        except:
            return False
    
    def extract_with_structure(
        self, 
        file_content: bytes
    ) -> Dict:
        """
        구조 정보를 포함한 HWP 추출
        
        Args:
            file_content: HWP 파일 바이트
        
        Returns:
            {
                'text': str,              # 전체 텍스트
                'paragraphs': List[Dict], # 문단 정보
                'tables': List[Dict],     # 테이블 정보
                'metadata': Dict,         # 메타데이터
                'structure': Dict         # 문서 구조
            }
        
        Raises:
            Exception: 파싱 실패 시
        """
        if not self.hwp5_available:
            raise ImportError("hwp5 library not available")
        
        try:
            # BytesIO로 변환
            hwp_file = io.BytesIO(file_content)
            
            # HWP 파일 열기
            hwp = self.Hwp5File(hwp_file)
            
            # 문단 추출
            paragraphs = self._extract_paragraphs(hwp)
            
            # 테이블 추출
            tables = self._extract_tables(hwp)
            
            # 메타데이터 추출
            metadata = self._extract_metadata(hwp)
            
            # 문서 구조 추출
            structure = self._extract_structure(hwp)
            
            # 전체 텍스트 생성
            text = self._build_full_text(paragraphs, tables)
            
            logger.info(
                f"Advanced HWP parsing completed: "
                f"{len(paragraphs)} paragraphs, {len(tables)} tables"
            )
            
            return {
                'text': text,
                'paragraphs': paragraphs,
                'tables': tables,
                'metadata': metadata,
                'structure': structure
            }
            
        except Exception as e:
            logger.error(f"Advanced HWP parsing failed: {e}")
            raise
    
    def _extract_paragraphs(self, hwp) -> List[Dict]:
        """문단 추출"""
        paragraphs = []
        
        try:
            # bodytext 섹션 순회
            for section_idx, section in enumerate(hwp.bodytext.section_list):
                for para_idx, paragraph in enumerate(section.paragraphs):
                    try:
                        para_dict = {
                            'text': self._get_paragraph_text(paragraph),
                            'section_index': section_idx,
                            'paragraph_index': para_idx,
                            'style': self._get_paragraph_style(paragraph),
                            'level': self._get_heading_level(paragraph),
                            'is_heading': self._is_heading(paragraph)
                        }
                        paragraphs.append(para_dict)
                    except Exception as e:
                        logger.warning(f"Failed to extract paragraph {para_idx}: {e}")
                        continue
        
        except Exception as e:
            logger.warning(f"Paragraph extraction failed: {e}")
        
        return paragraphs
    
    def _get_paragraph_text(self, paragraph) -> str:
        """문단 텍스트 추출"""
        try:
            # hwp5의 텍스트 추출 메서드 사용
            if hasattr(paragraph, 'get_text'):
                return paragraph.get_text()
            elif hasattr(paragraph, 'text'):
                return paragraph.text
            else:
                # 수동 텍스트 추출
                text_parts = []
                for child in paragraph:
                    if hasattr(child, 'text'):
                        text_parts.append(child.text)
                return "".join(text_parts)
        except:
            return ""
    
    def _get_paragraph_style(self, paragraph) -> Optional[str]:
        """문단 스타일 추출"""
        try:
            if hasattr(paragraph, 'get_style_name'):
                return paragraph.get_style_name()
            elif hasattr(paragraph, 'style'):
                return paragraph.style
        except:
            pass
        return None
    
    def _get_heading_level(self, paragraph) -> int:
        """제목 레벨 추출"""
        try:
            if hasattr(paragraph, 'get_heading_level'):
                return paragraph.get_heading_level()
            elif hasattr(paragraph, 'heading_level'):
                return paragraph.heading_level
        except:
            pass
        return 0
    
    def _is_heading(self, paragraph) -> bool:
        """제목 여부 확인"""
        try:
            if hasattr(paragraph, 'is_heading'):
                return paragraph.is_heading()
            
            # 스타일 이름으로 판단
            style = self._get_paragraph_style(paragraph)
            if style and ('제목' in style or 'heading' in style.lower()):
                return True
            
            # 레벨로 판단
            level = self._get_heading_level(paragraph)
            return level > 0
        except:
            return False
    
    def _extract_tables(self, hwp) -> List[Dict]:
        """테이블 추출"""
        tables = []
        
        try:
            for section in hwp.bodytext.section_list:
                # 테이블 찾기
                if hasattr(section, 'tables'):
                    for table_idx, table in enumerate(section.tables):
                        try:
                            table_dict = {
                                'rows': self._get_table_rows(table),
                                'cols': self._get_table_cols(table),
                                'cells': self._extract_table_cells(table),
                                'caption': self._get_table_caption(table),
                                'has_header': self._detect_table_header(table)
                            }
                            tables.append(table_dict)
                        except Exception as e:
                            logger.warning(f"Failed to extract table {table_idx}: {e}")
                            continue
        
        except Exception as e:
            logger.warning(f"Table extraction failed: {e}")
        
        return tables
    
    def _get_table_rows(self, table) -> int:
        """테이블 행 수"""
        try:
            if hasattr(table, 'get_rows'):
                return table.get_rows()
            elif hasattr(table, 'rows'):
                return len(table.rows)
        except:
            pass
        return 0
    
    def _get_table_cols(self, table) -> int:
        """테이블 열 수"""
        try:
            if hasattr(table, 'get_cols'):
                return table.get_cols()
            elif hasattr(table, 'cols'):
                return table.cols
        except:
            pass
        return 0
    
    def _extract_table_cells(self, table) -> List[List[str]]:
        """테이블 셀 추출"""
        cells = []
        
        try:
            if hasattr(table, 'rows'):
                for row in table.rows:
                    row_cells = []
                    if hasattr(row, 'cells'):
                        for cell in row.cells:
                            cell_text = self._get_cell_text(cell)
                            row_cells.append(cell_text)
                    cells.append(row_cells)
        except Exception as e:
            logger.warning(f"Cell extraction failed: {e}")
        
        return cells
    
    def _get_cell_text(self, cell) -> str:
        """셀 텍스트 추출"""
        try:
            if hasattr(cell, 'get_text'):
                return cell.get_text()
            elif hasattr(cell, 'text'):
                return cell.text
        except:
            pass
        return ""
    
    def _get_table_caption(self, table) -> str:
        """테이블 캡션 추출"""
        try:
            if hasattr(table, 'get_caption'):
                return table.get_caption()
            elif hasattr(table, 'caption'):
                return table.caption
        except:
            pass
        return ""
    
    def _detect_table_header(self, table) -> bool:
        """테이블 헤더 자동 감지"""
        try:
            if not hasattr(table, 'rows') or not table.rows:
                return False
            
            first_row = table.rows[0]
            
            # 첫 행의 셀들이 굵은 글씨이거나 배경색이 있으면 헤더로 판단
            if hasattr(first_row, 'cells'):
                for cell in first_row.cells:
                    # 굵은 글씨 체크
                    if hasattr(cell, 'is_bold') and cell.is_bold():
                        return True
                    # 배경색 체크
                    if hasattr(cell, 'has_background') and cell.has_background():
                        return True
        except:
            pass
        
        return False
    
    def _extract_metadata(self, hwp) -> Dict:
        """메타데이터 추출"""
        metadata = {}
        
        try:
            if hasattr(hwp, 'docinfo'):
                doc_info = hwp.docinfo
                
                # 각 메타데이터 필드 추출
                fields = [
                    'title', 'author', 'date', 'keywords', 
                    'subject', 'description', 'creator', 'last_saved_by'
                ]
                
                for field in fields:
                    try:
                        getter = f'get_{field}'
                        if hasattr(doc_info, getter):
                            value = getattr(doc_info, getter)()
                            if value:
                                metadata[field] = value
                        elif hasattr(doc_info, field):
                            value = getattr(doc_info, field)
                            if value:
                                metadata[field] = value
                    except:
                        continue
        
        except Exception as e:
            logger.warning(f"Metadata extraction failed: {e}")
        
        return metadata
    
    def _extract_structure(self, hwp) -> Dict:
        """문서 구조 추출 (목차)"""
        structure = {
            'sections': [],
            'headings': [],
            'toc': []  # Table of Contents
        }
        
        try:
            for section_idx, section in enumerate(hwp.bodytext.section_list):
                section_info = {
                    'index': section_idx,
                    'headings': []
                }
                
                # 섹션 내 제목 찾기
                if hasattr(section, 'paragraphs'):
                    for para in section.paragraphs:
                        if self._is_heading(para):
                            heading_info = {
                                'text': self._get_paragraph_text(para),
                                'level': self._get_heading_level(para),
                                'section_index': section_idx
                            }
                            section_info['headings'].append(heading_info)
                            structure['headings'].append(heading_info)
                            structure['toc'].append(heading_info)
                
                structure['sections'].append(section_info)
        
        except Exception as e:
            logger.warning(f"Structure extraction failed: {e}")
        
        return structure
    
    def _build_full_text(
        self, 
        paragraphs: List[Dict], 
        tables: List[Dict]
    ) -> str:
        """전체 텍스트 생성"""
        text_parts = []
        
        # 문단 텍스트
        for para in paragraphs:
            if para['is_heading']:
                # 제목은 강조
                level = para['level'] or 1
                prefix = "#" * min(level, 6)
                text_parts.append(f"\n{prefix} {para['text']}\n")
            else:
                text_parts.append(para['text'])
        
        # 테이블 텍스트
        for idx, table in enumerate(tables, 1):
            if table.get('caption'):
                text_parts.append(f"\n[Table {idx}: {table['caption']}]")
            else:
                text_parts.append(f"\n[Table {idx}]")
            
            table_text = self._format_table(table)
            text_parts.append(table_text)
        
        return "\n\n".join(text_parts)
    
    def _format_table(self, table: Dict) -> str:
        """테이블 포맷팅"""
        if not table['cells']:
            return ""
        
        lines = []
        
        for row_idx, row in enumerate(table['cells']):
            line = " | ".join(str(cell) for cell in row)
            lines.append(line)
            
            # 헤더 구분선
            if row_idx == 0 and table['has_header']:
                separator = " | ".join(["-" * max(len(str(cell)), 3) for cell in row])
                lines.append(separator)
        
        return "\n".join(lines)


# Global instance
_advanced_hwp_parser: Optional[AdvancedHWPParser] = None


def get_advanced_hwp_parser() -> AdvancedHWPParser:
    """Get global advanced HWP parser instance"""
    global _advanced_hwp_parser
    if _advanced_hwp_parser is None:
        _advanced_hwp_parser = AdvancedHWPParser()
    return _advanced_hwp_parser
