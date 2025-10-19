"""
Table-Aware Chunker for Improved RAG Accuracy

표를 고려한 지능형 청킹:
1. 표를 분할하지 않고 완전한 형태로 유지
2. 표 주변 컨텍스트 포함
3. 표 크기에 따른 적응형 청킹
4. 표 메타데이터 보존
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class TableAwareChunker:
    """
    표를 고려한 지능형 청킹
    
    Features:
    - 표 경계 감지 및 보존
    - 표 주변 컨텍스트 포함
    - 적응형 청크 크기
    - 표 메타데이터 보존
    """
    
    def __init__(
        self,
        base_chunk_size: int = 500,
        chunk_overlap: int = 50,
        max_table_size: int = 2000,  # 표 최대 크기
        context_window: int = 200  # 표 주변 컨텍스트 크기
    ):
        """
        초기화
        
        Args:
            base_chunk_size: 기본 청크 크기
            chunk_overlap: 청크 오버랩
            max_table_size: 표 최대 크기 (이보다 크면 분할)
            context_window: 표 주변 컨텍스트 크기
        """
        self.base_chunk_size = base_chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_table_size = max_table_size
        self.context_window = context_window
        
        # 표 마커 패턴
        self.table_start_pattern = r'\[TABLE START\]'
        self.table_end_pattern = r'\[TABLE END\]'
    
    def chunk_text_with_tables(
        self,
        text: str,
        preserve_tables: bool = True
    ) -> List[Dict[str, Any]]:
        """
        표를 고려하여 텍스트 청킹
        
        Args:
            text: 청킹할 텍스트
            preserve_tables: 표 보존 여부
            
        Returns:
            청크 리스트 (메타데이터 포함)
        """
        if not preserve_tables:
            # 표 보존 없이 일반 청킹
            return self._simple_chunk(text)
        
        # 1. 표 영역 감지
        table_regions = self._detect_table_regions(text)
        
        if not table_regions:
            # 표가 없으면 일반 청킹
            return self._simple_chunk(text)
        
        # 2. 표를 고려한 청킹
        chunks = self._chunk_with_table_awareness(text, table_regions)
        
        return chunks
    
    def _detect_table_regions(self, text: str) -> List[Dict[str, Any]]:
        """표 영역 감지"""
        regions = []
        
        # [TABLE START]와 [TABLE END] 마커로 표 영역 찾기
        pattern = f'{self.table_start_pattern}(.*?){self.table_end_pattern}'
        matches = re.finditer(pattern, text, re.DOTALL)
        
        for match in matches:
            start = match.start()
            end = match.end()
            table_content = match.group(1)
            
            regions.append({
                'start': start,
                'end': end,
                'content': table_content,
                'size': len(table_content)
            })
        
        return regions
    
    def _chunk_with_table_awareness(
        self,
        text: str,
        table_regions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """표를 고려한 청킹"""
        chunks = []
        current_pos = 0
        
        for region in table_regions:
            # 1. 표 이전 텍스트 청킹
            before_text = text[current_pos:region['start']]
            if before_text.strip():
                before_chunks = self._simple_chunk(before_text)
                chunks.extend(before_chunks)
            
            # 2. 표 청킹 (컨텍스트 포함)
            table_chunk = self._create_table_chunk(
                text,
                region,
                current_pos
            )
            chunks.append(table_chunk)
            
            current_pos = region['end']
        
        # 3. 마지막 표 이후 텍스트 청킹
        after_text = text[current_pos:]
        if after_text.strip():
            after_chunks = self._simple_chunk(after_text)
            chunks.extend(after_chunks)
        
        return chunks
    
    def _create_table_chunk(
        self,
        full_text: str,
        table_region: Dict[str, Any],
        prev_pos: int
    ) -> Dict[str, Any]:
        """표 청크 생성 (컨텍스트 포함)"""
        # 표 이전 컨텍스트
        context_start = max(prev_pos, table_region['start'] - self.context_window)
        before_context = full_text[context_start:table_region['start']].strip()
        
        # 표 내용
        table_content = full_text[table_region['start']:table_region['end']]
        
        # 표 이후 컨텍스트
        context_end = min(len(full_text), table_region['end'] + self.context_window)
        after_context = full_text[table_region['end']:context_end].strip()
        
        # 청크 조합
        chunk_parts = []
        
        if before_context:
            chunk_parts.append(f"[컨텍스트 - 이전]\n{before_context}\n")
        
        chunk_parts.append(table_content)
        
        if after_context:
            chunk_parts.append(f"\n[컨텍스트 - 이후]\n{after_context}")
        
        chunk_text = "\n".join(chunk_parts)
        
        return {
            'text': chunk_text,
            'metadata': {
                'type': 'table',
                'has_table': True,
                'table_size': table_region['size'],
                'has_context_before': bool(before_context),
                'has_context_after': bool(after_context)
            }
        }
    
    def _simple_chunk(self, text: str) -> List[Dict[str, Any]]:
        """일반 텍스트 청킹"""
        if not text or not text.strip():
            return []
        
        chunks = []
        text = text.strip()
        
        # 문장 단위로 분할
        sentences = self._split_into_sentences(text)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.base_chunk_size and current_chunk:
                # 현재 청크 저장
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'metadata': {
                        'type': 'text',
                        'has_table': False
                    }
                })
                
                # 오버랩을 위해 마지막 문장 일부 유지
                if self.chunk_overlap > 0:
                    overlap_text = chunk_text[-self.chunk_overlap:]
                    current_chunk = [overlap_text, sentence]
                    current_size = len(overlap_text) + sentence_size
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # 마지막 청크
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'metadata': {
                    'type': 'text',
                    'has_table': False
                }
            })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """문장 단위로 분할"""
        # 한국어와 영어 문장 구분자
        sentence_endings = r'[.!?。！？]\s+'
        sentences = re.split(sentence_endings, text)
        
        # 빈 문장 제거
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences


# 싱글톤 인스턴스
_table_aware_chunker = None


def get_table_aware_chunker(
    base_chunk_size: int = 500,
    chunk_overlap: int = 50
) -> TableAwareChunker:
    """Table-Aware Chunker 싱글톤 인스턴스 반환"""
    global _table_aware_chunker
    if _table_aware_chunker is None:
        _table_aware_chunker = TableAwareChunker(
            base_chunk_size=base_chunk_size,
            chunk_overlap=chunk_overlap
        )
    return _table_aware_chunker
