"""
Enhanced Table Extractor for Multimodal RAG

멀티모달 RAG를 위한 고급 표 추출기:
- 복잡한 표 구조 인식
- 병합 셀 처리
- 다중 표 감지
- 표 컨텍스트 보존
- 검색 최적화 포맷팅
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TableCell:
    """표 셀 정보"""
    text: str
    bbox: List[float]  # [x1, y1, x2, y2]
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    confidence: float = 1.0


@dataclass
class TableStructure:
    """표 구조 정보"""
    cells: List[TableCell]
    rows: int
    cols: int
    bbox: List[float]  # 표 전체 영역
    has_header: bool = False
    title: Optional[str] = None
    caption: Optional[str] = None


class EnhancedTableExtractor:
    """
    고급 표 추출기
    
    Features:
    - 정확한 행/열 감지
    - 병합 셀 인식
    - 표 경계 자동 감지
    - 헤더 자동 식별
    - 다중 표 처리
    """
    
    def __init__(
        self,
        row_threshold: int = 25,
        col_threshold: int = 30,
        min_cells: int = 4
    ):
        """
        초기화
        
        Args:
            row_threshold: 같은 행으로 판단할 Y 좌표 차이 (픽셀)
            col_threshold: 같은 열로 판단할 X 좌표 차이 (픽셀)
            min_cells: 표로 인식할 최소 셀 수
        """
        self.row_threshold = row_threshold
        self.col_threshold = col_threshold
        self.min_cells = min_cells
        
        logger.info(
            f"EnhancedTableExtractor initialized: "
            f"row_threshold={row_threshold}, col_threshold={col_threshold}"
        )
    
    def extract_tables(
        self,
        ocr_results: List[Dict]
    ) -> List[TableStructure]:
        """
        OCR 결과에서 표 추출
        
        Args:
            ocr_results: OCR 결과 리스트
                [{'text': str, 'bbox': [[x,y], ...], 'confidence': float}, ...]
        
        Returns:
            추출된 표 리스트
        """
        if not ocr_results:
            return []
        
        # 1. 표 영역 감지
        table_regions = self._detect_table_regions(ocr_results)
        
        if not table_regions:
            logger.info("No table regions detected")
            return []
        
        # 2. 각 표 영역에서 구조 추출
        tables = []
        for region_idx, region in enumerate(table_regions):
            try:
                table = self._extract_table_structure(region, region_idx)
                if table:
                    tables.append(table)
            except Exception as e:
                logger.warning(f"Failed to extract table {region_idx}: {e}")
                continue
        
        logger.info(f"Extracted {len(tables)} tables")
        return tables
    
    def _detect_table_regions(
        self,
        ocr_results: List[Dict]
    ) -> List[List[Dict]]:
        """
        표 영역 감지
        
        알고리즘:
        1. 텍스트 요소들을 그리드 패턴으로 그룹화
        2. 밀집된 영역을 표로 판단
        3. 각 표 영역의 요소들을 분리
        """
        # 바운딩 박스를 [x1, y1, x2, y2] 형식으로 변환
        elements = []
        for result in ocr_results:
            bbox = result['bbox']
            # bbox는 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] 형식
            x_coords = [p[0] for p in bbox]
            y_coords = [p[1] for p in bbox]
            
            elements.append({
                'text': result['text'],
                'bbox': [min(x_coords), min(y_coords), max(x_coords), max(y_coords)],
                'confidence': result.get('confidence', 1.0),
                'original_bbox': bbox
            })
        
        # Y 좌표로 정렬
        elements_sorted = sorted(elements, key=lambda e: e['bbox'][1])
        
        # 행 그룹화
        rows = self._group_into_rows(elements_sorted)
        
        # 표 영역 감지
        table_regions = []
        current_table = []
        
        for row in rows:
            # 행에 여러 열이 있고, 정렬되어 있으면 표의 일부
            if len(row) >= 2:
                # 열 간격 확인
                row_sorted = sorted(row, key=lambda e: e['bbox'][0])
                spacings = []
                for i in range(len(row_sorted) - 1):
                    spacing = row_sorted[i+1]['bbox'][0] - row_sorted[i]['bbox'][2]
                    spacings.append(spacing)
                
                # 일정한 간격이 있으면 표로 판단
                if spacings and max(spacings) > 10:
                    current_table.extend(row)
                else:
                    # 표 종료
                    if len(current_table) >= self.min_cells:
                        table_regions.append(current_table)
                    current_table = []
            else:
                # 단일 열 행 - 표 종료 또는 제목
                if current_table:
                    # 이전 표 저장
                    if len(current_table) >= self.min_cells:
                        table_regions.append(current_table)
                    current_table = []
        
        # 마지막 표
        if len(current_table) >= self.min_cells:
            table_regions.append(current_table)
        
        return table_regions
    
    def _group_into_rows(self, elements: List[Dict]) -> List[List[Dict]]:
        """요소들을 행으로 그룹화"""
        rows = []
        current_row = []
        current_y = None
        
        for element in elements:
            y = element['bbox'][1]  # Top Y
            
            if current_y is None:
                current_y = y
                current_row.append(element)
            elif abs(y - current_y) < self.row_threshold:
                # 같은 행
                current_row.append(element)
            else:
                # 새 행
                if current_row:
                    rows.append(current_row)
                current_row = [element]
                current_y = y
        
        # 마지막 행
        if current_row:
            rows.append(current_row)
        
        return rows
    
    def _extract_table_structure(
        self,
        region: List[Dict],
        table_idx: int
    ) -> Optional[TableStructure]:
        """
        표 영역에서 구조 추출
        
        Args:
            region: 표 영역의 요소들
            table_idx: 표 인덱스
        
        Returns:
            TableStructure 또는 None
        """
        if not region:
            return None
        
        # 1. 행 그룹화
        rows = self._group_into_rows(region)
        
        if len(rows) < 2:
            return None
        
        # 2. 열 위치 감지
        col_positions = self._detect_column_positions(rows)
        
        if len(col_positions) < 2:
            return None
        
        # 3. 셀 할당
        cells = []
        for row_idx, row in enumerate(rows):
            row_sorted = sorted(row, key=lambda e: e['bbox'][0])
            
            for element in row_sorted:
                # 요소가 속한 열 찾기
                col_idx = self._find_column_index(element, col_positions)
                
                cell = TableCell(
                    text=element['text'],
                    bbox=element['bbox'],
                    row=row_idx,
                    col=col_idx,
                    confidence=element['confidence']
                )
                cells.append(cell)
        
        # 4. 표 경계 계산
        all_x = [c.bbox[0] for c in cells] + [c.bbox[2] for c in cells]
        all_y = [c.bbox[1] for c in cells] + [c.bbox[3] for c in cells]
        table_bbox = [min(all_x), min(all_y), max(all_x), max(all_y)]
        
        # 5. 헤더 감지
        has_header = self._detect_header(cells, rows)
        
        # 6. TableStructure 생성
        table = TableStructure(
            cells=cells,
            rows=len(rows),
            cols=len(col_positions),
            bbox=table_bbox,
            has_header=has_header
        )
        
        logger.info(
            f"Table {table_idx}: {table.rows}x{table.cols}, "
            f"header={has_header}, cells={len(cells)}"
        )
        
        return table
    
    def _detect_column_positions(self, rows: List[List[Dict]]) -> List[float]:
        """
        열 위치 감지
        
        Returns:
            열의 X 좌표 리스트 (정렬됨)
        """
        # 모든 요소의 X 좌표 수집
        x_positions = []
        for row in rows:
            for element in row:
                x_positions.append(element['bbox'][0])  # Left X
        
        # X 좌표 클러스터링
        x_positions_sorted = sorted(set(x_positions))
        
        # 가까운 X 좌표들을 하나의 열로 그룹화
        col_positions = []
        current_col = x_positions_sorted[0]
        
        for x in x_positions_sorted[1:]:
            if x - current_col > self.col_threshold:
                col_positions.append(current_col)
                current_col = x
        
        col_positions.append(current_col)
        
        return col_positions
    
    def _find_column_index(
        self,
        element: Dict,
        col_positions: List[float]
    ) -> int:
        """요소가 속한 열 인덱스 찾기"""
        x = element['bbox'][0]
        
        # 가장 가까운 열 찾기
        min_dist = float('inf')
        col_idx = 0
        
        for idx, col_x in enumerate(col_positions):
            dist = abs(x - col_x)
            if dist < min_dist:
                min_dist = dist
                col_idx = idx
        
        return col_idx
    
    def _detect_header(
        self,
        cells: List[TableCell],
        rows: List[List[Dict]]
    ) -> bool:
        """
        헤더 행 감지
        
        휴리스틱:
        - 첫 행의 텍스트가 짧고 명확한 경우
        - 첫 행과 두 번째 행의 스타일이 다른 경우
        - 키워드 포함 ("항목", "사양", "이름" 등)
        """
        if not cells or not rows:
            return False
        
        # 첫 행의 셀들
        first_row_cells = [c for c in cells if c.row == 0]
        
        if not first_row_cells:
            return False
        
        # 헤더 키워드
        header_keywords = [
            '항목', '사양', '이름', '명칭', '구분', '분류',
            '제품', '모델', '규격', '단위', '수량', '가격',
            '날짜', '시간', '장소', '담당', '비고', '설명',
            'name', 'type', 'model', 'spec', 'price', 'date'
        ]
        
        # 키워드 확인
        first_row_text = ' '.join(c.text for c in first_row_cells).lower()
        has_keyword = any(kw in first_row_text for kw in header_keywords)
        
        # 첫 행 텍스트가 짧은 경우 (헤더는 보통 짧음)
        avg_length = sum(len(c.text) for c in first_row_cells) / len(first_row_cells)
        is_short = avg_length < 10
        
        return has_keyword or is_short
    
    def format_table_for_rag(
        self,
        table: TableStructure,
        table_idx: int = 0
    ) -> str:
        """
        RAG 검색에 최적화된 표 포맷팅
        
        전략:
        1. 마크다운 표 형식
        2. 각 행을 자연어 문장으로도 변환
        3. 키-값 쌍 명시
        4. 컨텍스트 정보 추가
        """
        lines = []
        
        # 표 시작 마커
        lines.append(f"\n{'='*70}")
        lines.append(f"[TABLE {table_idx + 1}]")
        if table.title:
            lines.append(f"제목: {table.title}")
        lines.append(f"크기: {table.rows}행 x {table.cols}열")
        lines.append('='*70)
        
        # 셀을 행/열로 정리
        grid = [[None for _ in range(table.cols)] for _ in range(table.rows)]
        
        for cell in table.cells:
            if 0 <= cell.row < table.rows and 0 <= cell.col < table.cols:
                grid[cell.row][cell.col] = cell.text
        
        # 1. 마크다운 표 형식
        lines.append("\n[마크다운 표]")
        
        # 헤더
        if table.has_header and grid:
            header_row = grid[0]
            lines.append("| " + " | ".join(str(c or "") for c in header_row) + " |")
            lines.append("|" + "|".join(["---" for _ in header_row]) + "|")
            data_rows = grid[1:]
        else:
            data_rows = grid
        
        # 데이터 행
        for row in data_rows:
            lines.append("| " + " | ".join(str(c or "") for c in row) + " |")
        
        # 2. 자연어 형식 (검색 최적화)
        lines.append("\n[자연어 형식]")
        
        if table.has_header and grid:
            headers = grid[0]
            for row_idx, row in enumerate(data_rows, 1):
                lines.append(f"\n행 {row_idx}:")
                for col_idx, (header, value) in enumerate(zip(headers, row)):
                    if header and value:
                        # 키-값 쌍
                        lines.append(f"  • {header}: {value}")
                        # 검색용 반복
                        lines.append(f"    → {value}")
        else:
            # 헤더 없는 경우
            for row_idx, row in enumerate(grid, 1):
                row_text = " | ".join(str(c or "") for c in row)
                lines.append(f"행 {row_idx}: {row_text}")
        
        # 3. 키워드 추출 (검색 최적화)
        lines.append("\n[주요 키워드]")
        keywords = self._extract_table_keywords(table)
        lines.append(", ".join(keywords))
        
        # 표 종료 마커
        lines.append('='*70)
        lines.append(f"[TABLE {table_idx + 1} END]")
        lines.append('='*70 + "\n")
        
        return "\n".join(lines)
    
    def _extract_table_keywords(self, table: TableStructure) -> List[str]:
        """표에서 주요 키워드 추출"""
        keywords = set()
        
        for cell in table.cells:
            text = cell.text.strip()
            if not text:
                continue
            
            # 짧은 텍스트는 키워드로 간주
            if len(text) <= 20:
                keywords.add(text)
            
            # 숫자 포함 텍스트 (사양, 가격 등)
            if any(c.isdigit() for c in text):
                keywords.add(text)
        
        return sorted(keywords)[:20]  # 상위 20개


# Global instance
_enhanced_table_extractor: Optional[EnhancedTableExtractor] = None


def get_enhanced_table_extractor(
    row_threshold: int = 25,
    col_threshold: int = 30,
    min_cells: int = 4
) -> EnhancedTableExtractor:
    """Get global enhanced table extractor instance"""
    global _enhanced_table_extractor
    if _enhanced_table_extractor is None:
        _enhanced_table_extractor = EnhancedTableExtractor(
            row_threshold=row_threshold,
            col_threshold=col_threshold,
            min_cells=min_cells
        )
    return _enhanced_table_extractor
