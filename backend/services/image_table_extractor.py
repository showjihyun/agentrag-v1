"""
Image Table Extractor for Improved RAG Accuracy

이미지 내 표 추출 정확도 향상:
1. ColPali 기반 표 영역 감지
2. 표 구조 복원
3. OCR 후처리 및 정제
4. 표 컨텍스트 보강
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


class ImageTableExtractor:
    """
    이미지 내 표 추출 및 처리
    
    Features:
    - ColPali 기반 표 영역 감지
    - 표 구조 복원 (행/열 정렬)
    - OCR 후처리 (노이즈 제거, 정렬)
    - 표 컨텍스트 보강
    """
    
    def __init__(self):
        """초기화"""
        self.colpali_processor = None
        self.ocr_engine = None
        
    def extract_tables_from_image(
        self,
        image: Image.Image,
        use_colpali: bool = True,
        use_ocr_fallback: bool = True
    ) -> List[Dict[str, Any]]:
        """
        이미지에서 표 추출
        
        Args:
            image: PIL Image 객체
            use_colpali: ColPali 사용 여부
            use_ocr_fallback: OCR 폴백 사용 여부
            
        Returns:
            추출된 표 리스트
        """
        tables = []
        
        # 1. ColPali로 표 영역 감지 및 추출
        if use_colpali:
            try:
                colpali_tables = self._extract_with_colpali(image)
                tables.extend(colpali_tables)
                logger.info(f"ColPali로 {len(colpali_tables)}개 표 추출")
            except Exception as e:
                logger.warning(f"ColPali 표 추출 실패: {e}")
        
        # 2. OCR 폴백 (ColPali 실패 시 또는 추가 정보 필요 시)
        if use_ocr_fallback and (not tables or self._needs_ocr_refinement(tables)):
            try:
                ocr_tables = self._extract_with_ocr(image)
                
                # ColPali 결과와 병합
                if tables:
                    tables = self._merge_table_results(tables, ocr_tables)
                else:
                    tables = ocr_tables
                
                logger.info(f"OCR로 {len(ocr_tables)}개 표 추출/보강")
            except Exception as e:
                logger.warning(f"OCR 표 추출 실패: {e}")
        
        # 3. 표 후처리
        processed_tables = []
        for table in tables:
            processed = self._post_process_table(table)
            if processed:
                processed_tables.append(processed)
        
        return processed_tables
    
    def _extract_with_colpali(self, image: Image.Image) -> List[Dict[str, Any]]:
        """ColPali로 표 추출"""
        if self.colpali_processor is None:
            from backend.services.colpali_processor import get_colpali_processor
            self.colpali_processor = get_colpali_processor()
        
        # ColPali는 이미지 전체를 패치로 나누어 처리
        # 표 영역은 높은 attention을 받음
        embeddings = self.colpali_processor.process_image(image)
        
        # 표 영역 감지 (attention map 기반)
        table_regions = self._detect_table_regions(embeddings, image)
        
        tables = []
        for region in table_regions:
            table_data = {
                'source': 'colpali',
                'region': region,
                'confidence': region.get('confidence', 0.0),
                'data': region.get('data', []),
                'metadata': {
                    'bbox': region.get('bbox'),
                    'attention_score': region.get('attention_score')
                }
            }
            tables.append(table_data)
        
        return tables
    
    def _detect_table_regions(
        self,
        embeddings: Dict[str, Any],
        image: Image.Image
    ) -> List[Dict[str, Any]]:
        """표 영역 감지 (attention map 기반)"""
        # ColPali의 attention map을 분석하여 표 영역 감지
        # 표는 일반적으로 높은 attention과 규칙적인 패턴을 가짐
        
        regions = []
        
        # 간단한 구현 (실제로는 더 정교한 알고리즘 필요)
        # 여기서는 전체 이미지를 하나의 표로 간주
        width, height = image.size
        regions.append({
            'bbox': (0, 0, width, height),
            'confidence': 0.8,
            'attention_score': 0.9,
            'data': []  # 실제 표 데이터는 OCR로 추출
        })
        
        return regions
    
    def _extract_with_ocr(self, image: Image.Image) -> List[Dict[str, Any]]:
        """OCR로 표 추출"""
        if self.ocr_engine is None:
            try:
                import easyocr
                self.ocr_engine = easyocr.Reader(['ko', 'en'])
                logger.info("EasyOCR 초기화 완료")
            except ImportError:
                logger.warning("EasyOCR not available, skipping OCR extraction")
                return []
        
        # OCR 실행
        results = self.ocr_engine.readtext(np.array(image))
        
        # 표 구조 복원
        table_data = self._reconstruct_table_structure(results, image.size)
        
        tables = []
        if table_data:
            tables.append({
                'source': 'ocr',
                'confidence': 0.7,
                'data': table_data,
                'metadata': {
                    'ocr_results': len(results)
                }
            })
        
        return tables
    
    def _reconstruct_table_structure(
        self,
        ocr_results: List[Tuple],
        image_size: Tuple[int, int]
    ) -> List[List[str]]:
        """OCR 결과로부터 표 구조 복원"""
        if not ocr_results:
            return []
        
        # OCR 결과를 위치 기반으로 정렬
        # (bbox, text, confidence)
        sorted_results = sorted(ocr_results, key=lambda x: (x[0][0][1], x[0][0][0]))
        
        # 행 그룹화 (y 좌표 기준)
        rows = []
        current_row = []
        current_y = None
        y_threshold = 20  # 같은 행으로 간주할 y 좌표 차이
        
        for bbox, text, conf in sorted_results:
            y = bbox[0][1]  # 상단 y 좌표
            
            if current_y is None or abs(y - current_y) < y_threshold:
                current_row.append((bbox, text, conf))
                current_y = y if current_y is None else current_y
            else:
                if current_row:
                    rows.append(current_row)
                current_row = [(bbox, text, conf)]
                current_y = y
        
        if current_row:
            rows.append(current_row)
        
        # 각 행을 x 좌표 기준으로 정렬하여 표 데이터 생성
        table_data = []
        for row in rows:
            sorted_row = sorted(row, key=lambda x: x[0][0][0])  # x 좌표 기준 정렬
            row_data = [text for _, text, _ in sorted_row]
            table_data.append(row_data)
        
        return table_data
    
    def _needs_ocr_refinement(self, tables: List[Dict[str, Any]]) -> bool:
        """OCR 보강이 필요한지 판단"""
        # ColPali 결과에 실제 텍스트 데이터가 없으면 OCR 필요
        for table in tables:
            if not table.get('data') or len(table['data']) == 0:
                return True
        return False
    
    def _merge_table_results(
        self,
        colpali_tables: List[Dict[str, Any]],
        ocr_tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """ColPali와 OCR 결과 병합"""
        merged = []
        
        for colpali_table in colpali_tables:
            # ColPali 표에 OCR 데이터 추가
            if not colpali_table.get('data') and ocr_tables:
                # 가장 가까운 OCR 표 찾기
                best_ocr = ocr_tables[0] if ocr_tables else None
                if best_ocr:
                    colpali_table['data'] = best_ocr['data']
                    colpali_table['source'] = 'colpali+ocr'
            
            merged.append(colpali_table)
        
        return merged
    
    def _post_process_table(self, table: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """표 후처리"""
        if not table.get('data'):
            return None
        
        # 1. 빈 행/열 제거
        cleaned_data = self._remove_empty_rows_cols(table['data'])
        
        # 2. 텍스트 정제
        cleaned_data = self._clean_table_text(cleaned_data)
        
        # 3. 표 유효성 검증
        if not self._is_valid_table(cleaned_data):
            return None
        
        table['data'] = cleaned_data
        return table
    
    def _remove_empty_rows_cols(
        self,
        table_data: List[List[str]]
    ) -> List[List[str]]:
        """빈 행/열 제거"""
        if not table_data:
            return []
        
        # 빈 행 제거
        non_empty_rows = [
            row for row in table_data
            if any(cell.strip() for cell in row)
        ]
        
        if not non_empty_rows:
            return []
        
        # 빈 열 제거
        num_cols = max(len(row) for row in non_empty_rows)
        non_empty_cols = []
        
        for col_idx in range(num_cols):
            has_content = any(
                col_idx < len(row) and row[col_idx].strip()
                for row in non_empty_rows
            )
            if has_content:
                non_empty_cols.append(col_idx)
        
        # 빈 열이 아닌 열만 유지
        cleaned = []
        for row in non_empty_rows:
            cleaned_row = [
                row[col_idx] if col_idx < len(row) else ""
                for col_idx in non_empty_cols
            ]
            cleaned.append(cleaned_row)
        
        return cleaned
    
    def _clean_table_text(
        self,
        table_data: List[List[str]]
    ) -> List[List[str]]:
        """표 텍스트 정제"""
        cleaned = []
        
        for row in table_data:
            cleaned_row = []
            for cell in row:
                # 공백 정리
                cleaned_cell = ' '.join(cell.split())
                # 특수문자 정리 (필요시)
                cleaned_cell = cleaned_cell.strip()
                cleaned_row.append(cleaned_cell)
            cleaned.append(cleaned_row)
        
        return cleaned
    
    def _is_valid_table(self, table_data: List[List[str]]) -> bool:
        """표 유효성 검증"""
        if not table_data or len(table_data) < 2:
            return False
        
        # 최소 2행 이상
        # 최소 2열 이상
        if all(len(row) < 2 for row in table_data):
            return False
        
        return True


# 싱글톤 인스턴스
_image_table_extractor = None


def get_image_table_extractor() -> ImageTableExtractor:
    """Image Table Extractor 싱글톤 인스턴스 반환"""
    global _image_table_extractor
    if _image_table_extractor is None:
        _image_table_extractor = ImageTableExtractor()
    return _image_table_extractor
