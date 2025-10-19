"""
Enhanced Table Processor for Improved RAG Accuracy

표 데이터 처리 정확도를 높이기 위한 고급 처리기:
1. 표 구조 분석 및 메타데이터 추출
2. 표 내용 의미론적 인덱싱
3. 표 검색 최적화
4. 표 컨텍스트 보강
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class EnhancedTableProcessor:
    """
    표 데이터 처리 정확도 향상을 위한 고급 프로세서
    
    Features:
    - 표 구조 분석 (헤더, 데이터 행 구분)
    - 표 메타데이터 추출 (제목, 단위, 주석)
    - 표 내용 의미론적 인덱싱
    - 표 검색 최적화 (키-값 매핑)
    - 표 컨텍스트 보강 (주변 텍스트 포함)
    """
    
    def __init__(self):
        """초기화"""
        self.table_patterns = {
            'title': r'표\s*\d+[\.:]?\s*(.+)',  # 표 1. 제목
            'unit': r'\(([^)]+)\)',  # (단위)
            'note': r'주[:]?\s*(.+)',  # 주: 설명
            'source': r'출처[:]?\s*(.+)',  # 출처: 
        }
    
    def process_table(
        self,
        table_data: List[List[str]],
        context_before: str = "",
        context_after: str = "",
        table_index: int = 1
    ) -> Dict[str, Any]:
        """
        표 데이터를 처리하여 검색 최적화된 형태로 변환
        
        Args:
            table_data: 표 데이터 (2D 리스트)
            context_before: 표 이전 텍스트 (제목, 설명 등)
            context_after: 표 이후 텍스트 (주석, 출처 등)
            table_index: 표 번호
            
        Returns:
            처리된 표 데이터 및 메타데이터
        """
        if not table_data or len(table_data) == 0:
            return None
        
        # 1. 표 메타데이터 추출
        metadata = self._extract_table_metadata(
            context_before, 
            context_after, 
            table_index
        )
        
        # 2. 표 구조 분석
        structure = self._analyze_table_structure(table_data)
        
        # 3. 표 내용 인덱싱
        indexed_content = self._index_table_content(
            table_data, 
            structure
        )
        
        # 4. 검색 최적화된 텍스트 생성
        searchable_text = self._generate_searchable_text(
            table_data,
            structure,
            metadata,
            indexed_content
        )
        
        return {
            'table_index': table_index,
            'metadata': metadata,
            'structure': structure,
            'indexed_content': indexed_content,
            'searchable_text': searchable_text,
            'raw_data': table_data
        }
    
    def _extract_table_metadata(
        self,
        context_before: str,
        context_after: str,
        table_index: int
    ) -> Dict[str, Any]:
        """표 메타데이터 추출"""
        metadata = {
            'table_number': table_index,
            'title': None,
            'unit': None,
            'notes': [],
            'source': None
        }
        
        # 제목 추출 (표 이전 텍스트에서)
        if context_before:
            title_match = re.search(self.table_patterns['title'], context_before)
            if title_match:
                metadata['title'] = title_match.group(1).strip()
        
        # 단위 추출
        combined_text = context_before + context_after
        unit_matches = re.findall(self.table_patterns['unit'], combined_text)
        if unit_matches:
            metadata['unit'] = unit_matches[0]
        
        # 주석 추출 (표 이후 텍스트에서)
        if context_after:
            note_matches = re.findall(self.table_patterns['note'], context_after)
            metadata['notes'] = [note.strip() for note in note_matches]
            
            source_match = re.search(self.table_patterns['source'], context_after)
            if source_match:
                metadata['source'] = source_match.group(1).strip()
        
        return metadata
    
    def _analyze_table_structure(
        self,
        table_data: List[List[str]]
    ) -> Dict[str, Any]:
        """표 구조 분석"""
        if not table_data:
            return {}
        
        num_rows = len(table_data)
        num_cols = len(table_data[0]) if table_data else 0
        
        # 헤더 행 감지 (첫 행이 다른 행과 다른 패턴을 가지는지)
        has_header = self._detect_header_row(table_data)
        
        # 데이터 타입 분석 (숫자, 텍스트, 날짜 등)
        column_types = self._analyze_column_types(table_data, has_header)
        
        return {
            'num_rows': num_rows,
            'num_cols': num_cols,
            'has_header': has_header,
            'header_row': table_data[0] if has_header else None,
            'data_rows': table_data[1:] if has_header else table_data,
            'column_types': column_types
        }
    
    def _detect_header_row(self, table_data: List[List[str]]) -> bool:
        """헤더 행 감지"""
        if len(table_data) < 2:
            return False
        
        first_row = table_data[0]
        second_row = table_data[1]
        
        # 첫 행이 모두 텍스트이고 두 번째 행에 숫자가 많으면 헤더로 판단
        first_row_numeric = sum(1 for cell in first_row if self._is_numeric(cell))
        second_row_numeric = sum(1 for cell in second_row if self._is_numeric(cell))
        
        return first_row_numeric < second_row_numeric
    
    def _is_numeric(self, text: str) -> bool:
        """숫자 여부 판단"""
        if not text or not text.strip():
            return False
        
        # 쉼표, 퍼센트, 단위 제거 후 숫자 판단
        cleaned = re.sub(r'[,,%원달러€$]', '', text.strip())
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _analyze_column_types(
        self,
        table_data: List[List[str]],
        has_header: bool
    ) -> List[str]:
        """컬럼 데이터 타입 분석"""
        if not table_data:
            return []
        
        num_cols = len(table_data[0])
        data_rows = table_data[1:] if has_header else table_data
        
        column_types = []
        
        for col_idx in range(num_cols):
            col_values = [row[col_idx] for row in data_rows if col_idx < len(row)]
            
            # 숫자 비율 계산
            numeric_count = sum(1 for val in col_values if self._is_numeric(val))
            numeric_ratio = numeric_count / len(col_values) if col_values else 0
            
            if numeric_ratio > 0.7:
                column_types.append('numeric')
            elif any('년' in val or '월' in val or '일' in val for val in col_values):
                column_types.append('date')
            else:
                column_types.append('text')
        
        return column_types
    
    def _index_table_content(
        self,
        table_data: List[List[str]],
        structure: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """표 내용을 키-값 형태로 인덱싱"""
        indexed = {}
        
        if not structure.get('has_header'):
            return indexed
        
        headers = structure['header_row']
        data_rows = structure['data_rows']
        
        for row in data_rows:
            for col_idx, header in enumerate(headers):
                if col_idx < len(row):
                    key = header.strip()
                    value = row[col_idx].strip()
                    
                    if key and value:
                        if key not in indexed:
                            indexed[key] = []
                        indexed[key].append(value)
        
        return indexed
    
    def _generate_searchable_text(
        self,
        table_data: List[List[str]],
        structure: Dict[str, Any],
        metadata: Dict[str, Any],
        indexed_content: Dict[str, List[str]]
    ) -> str:
        """검색 최적화된 텍스트 생성"""
        lines = []
        
        # 구분선
        lines.append("=" * 80)
        lines.append("[TABLE START]")
        lines.append("=" * 80)
        
        # 메타데이터
        if metadata.get('title'):
            lines.append(f"\n📊 표 제목: {metadata['title']}")
        
        lines.append(f"표 번호: {metadata['table_number']}")
        lines.append(f"크기: {structure['num_rows']}행 × {structure['num_cols']}열")
        
        if metadata.get('unit'):
            lines.append(f"단위: {metadata['unit']}")
        
        lines.append("")
        
        # 표 내용 (키-값 형태로 반복)
        if structure.get('has_header'):
            headers = structure['header_row']
            data_rows = structure['data_rows']
            
            lines.append("📋 표 내용:")
            lines.append("-" * 80)
            
            for row_idx, row in enumerate(data_rows, 1):
                lines.append(f"\n[행 {row_idx}]")
                
                for col_idx, header in enumerate(headers):
                    if col_idx < len(row):
                        value = row[col_idx].strip()
                        if header and value:
                            # 키-값 형태로 저장 (검색 최적화)
                            lines.append(f"  • {header}: {value}")
                            
                            # 검색을 위한 추가 표현
                            lines.append(f"    → {header}은(는) {value}")
                            lines.append(f"    → {value} ({header})")
        else:
            # 헤더가 없는 경우
            lines.append("📋 표 내용:")
            lines.append("-" * 80)
            
            for row_idx, row in enumerate(table_data, 1):
                row_text = " | ".join(cell.strip() for cell in row if cell.strip())
                if row_text:
                    lines.append(f"행 {row_idx}: {row_text}")
        
        # 주석 및 출처
        if metadata.get('notes'):
            lines.append("\n📝 주석:")
            for note in metadata['notes']:
                lines.append(f"  • {note}")
        
        if metadata.get('source'):
            lines.append(f"\n📚 출처: {metadata['source']}")
        
        # 인덱싱된 내용 (검색 최적화)
        if indexed_content:
            lines.append("\n🔍 검색 키워드:")
            for key, values in indexed_content.items():
                unique_values = list(set(values))
                lines.append(f"  • {key}: {', '.join(unique_values[:5])}")
        
        lines.append("\n" + "=" * 80)
        lines.append("[TABLE END]")
        lines.append("=" * 80)
        
        return "\n".join(lines)


# 싱글톤 인스턴스
_table_processor = None


def get_enhanced_table_processor() -> EnhancedTableProcessor:
    """Enhanced Table Processor 싱글톤 인스턴스 반환"""
    global _table_processor
    if _table_processor is None:
        _table_processor = EnhancedTableProcessor()
    return _table_processor
