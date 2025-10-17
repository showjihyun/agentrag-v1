"""
Korean-Optimized Chunking Strategy

한글 문서에 최적화된 청킹 전략:
- 문장 경계 인식 (한글 특화)
- 문단 구조 보존
- 의미 단위 유지
- 테이블/리스트 처리
"""

import logging
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChunkConfig:
    """청킹 설정"""
    target_size: int = 500
    min_size: int = 100
    max_size: int = 1000
    overlap: int = 50
    preserve_structure: bool = True


class KoreanChunkingStrategy:
    """
    한글 최적화 청킹 전략
    
    특징:
    - 한글 문장 경계 정확한 인식
    - 문단/섹션 구조 보존
    - 테이블/리스트 완전성 유지
    - 의미 단위 분리 방지
    """
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        
        # 한글 문장 종결 패턴
        self.sentence_endings = re.compile(
            r'([.!?])\s+|'  # 영문 문장 종결
            r'([.!?。！？])\s*(?=[가-힣A-Z])|'  # 한글 문장 종결
            r'([다요]\s*[.!?])\s*'  # 한글 종결어미 + 문장부호
        )
        
        # 문단 구분 패턴
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        
        # 제목 패턴
        self.heading_pattern = re.compile(
            r'^(#{1,6}\s+|'  # Markdown 제목
            r'\d+\.\s+|'  # 번호 제목
            r'[가-힣]{1,20}:\s*$|'  # 한글 제목 + 콜론
            r'\[.*?\])'  # 대괄호 제목
        , re.MULTILINE)
        
        # 테이블 패턴
        self.table_pattern = re.compile(
            r'\[Table \d+\].*?\[TABLE END\]',
            re.DOTALL
        )
        
        # 리스트 패턴
        self.list_pattern = re.compile(
            r'^[\s]*[-*•]\s+',
            re.MULTILINE
        )
        
        logger.info(f"KoreanChunkingStrategy initialized: {self.config}")
    
    def chunk_text(
        self, 
        text: str, 
        metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 원본 텍스트
            metadata: 메타데이터
        
        Returns:
            List[Dict]: 청크 리스트
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # 1. 테이블 분리 (완전성 유지)
        tables, text_without_tables = self._extract_tables(text)
        
        # 2. 문단 기반 청킹
        if self.config.preserve_structure:
            text_chunks = self._chunk_by_structure(text_without_tables)
        else:
            text_chunks = self._chunk_by_size(text_without_tables)
        
        # 3. 청크 생성
        for idx, chunk_text in enumerate(text_chunks):
            chunk = {
                'chunk_id': f"chunk_{idx}",
                'text': chunk_text,
                'type': 'text',
                'size': len(chunk_text),
                'metadata': metadata or {}
            }
            chunks.append(chunk)
        
        # 4. 테이블 청크 추가
        for idx, table_text in enumerate(tables):
            chunk = {
                'chunk_id': f"table_{idx}",
                'text': table_text,
                'type': 'table',
                'size': len(table_text),
                'metadata': {**(metadata or {}), 'is_table': True}
            }
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks ({len(text_chunks)} text, {len(tables)} tables)")
        
        return chunks
    
    def _extract_tables(self, text: str) -> Tuple[List[str], str]:
        """테이블 추출 및 분리"""
        tables = []
        
        # 테이블 찾기
        for match in self.table_pattern.finditer(text):
            tables.append(match.group())
        
        # 테이블 제거
        text_without_tables = self.table_pattern.sub('', text)
        
        return tables, text_without_tables
    
    def _chunk_by_structure(self, text: str) -> List[str]:
        """구조 기반 청킹"""
        chunks = []
        
        # 문단으로 분리
        paragraphs = self.paragraph_pattern.split(text)
        
        current_chunk = []
        current_size = 0
        current_section = None
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 제목 감지
            is_heading = bool(self.heading_pattern.match(para))
            
            if is_heading:
                # 이전 청크 저장
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # 새 섹션 시작
                current_section = para
                current_chunk.append(para)
                current_size = len(para)
                continue
            
            # 리스트 항목 감지
            is_list = bool(self.list_pattern.search(para))
            
            para_size = len(para)
            
            # 크기 체크
            if current_size + para_size > self.config.max_size:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                
                # 새 청크 시작 (오버랩)
                if self.config.overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-1]
                    if len(overlap_text) <= self.config.overlap:
                        current_chunk = [overlap_text, para]
                        current_size = len(overlap_text) + para_size
                    else:
                        current_chunk = [para]
                        current_size = para_size
                else:
                    current_chunk = [para]
                    current_size = para_size
            else:
                current_chunk.append(para)
                current_size += para_size
        
        # 마지막 청크
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
    
    def _chunk_by_size(self, text: str) -> List[str]:
        """크기 기반 청킹 (문장 경계 고려)"""
        chunks = []
        
        # 문장으로 분리
        sentences = self._split_sentences(text)
        
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_size = len(sentence)
            
            # 크기 체크
            if current_size + sentence_size > self.config.target_size:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                # 새 청크 시작 (오버랩)
                if self.config.overlap > 0 and current_chunk:
                    # 마지막 몇 문장을 오버랩
                    overlap_sentences = []
                    overlap_size = 0
                    
                    for sent in reversed(current_chunk):
                        if overlap_size + len(sent) <= self.config.overlap:
                            overlap_sentences.insert(0, sent)
                            overlap_size += len(sent)
                        else:
                            break
                    
                    current_chunk = overlap_sentences + [sentence]
                    current_size = overlap_size + sentence_size
                else:
                    current_chunk = [sentence]
                    current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # 마지막 청크
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """한글 문장 분리"""
        sentences = []
        
        # 문장 종결 패턴으로 분리
        parts = self.sentence_endings.split(text)
        
        current_sentence = ""
        
        for part in parts:
            if part is None:
                continue
            
            part = part.strip()
            if not part:
                continue
            
            # 문장 종결 부호인 경우
            if part in ['.', '!', '?', '。', '！', '？']:
                current_sentence += part
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                current_sentence += part + " "
        
        # 남은 문장
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def optimize_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        청크 최적화
        
        - 너무 작은 청크 병합
        - 너무 큰 청크 분할
        - 중복 제거
        """
        optimized = []
        
        i = 0
        while i < len(chunks):
            chunk = chunks[i]
            
            # 너무 작은 청크
            if chunk['size'] < self.config.min_size:
                # 다음 청크와 병합
                if i + 1 < len(chunks):
                    next_chunk = chunks[i + 1]
                    merged_text = chunk['text'] + '\n\n' + next_chunk['text']
                    
                    merged_chunk = {
                        'chunk_id': f"merged_{i}",
                        'text': merged_text,
                        'type': chunk['type'],
                        'size': len(merged_text),
                        'metadata': chunk['metadata']
                    }
                    optimized.append(merged_chunk)
                    i += 2
                    continue
                else:
                    # 마지막 청크는 그대로 유지
                    optimized.append(chunk)
                    i += 1
                    continue
            
            # 너무 큰 청크
            if chunk['size'] > self.config.max_size:
                # 분할
                sub_chunks = self._split_large_chunk(chunk)
                optimized.extend(sub_chunks)
                i += 1
                continue
            
            # 정상 크기
            optimized.append(chunk)
            i += 1
        
        logger.info(f"Optimized chunks: {len(chunks)} → {len(optimized)}")
        
        return optimized
    
    def _split_large_chunk(self, chunk: Dict) -> List[Dict]:
        """큰 청크 분할"""
        text = chunk['text']
        
        # 문장으로 분리
        sentences = self._split_sentences(text)
        
        sub_chunks = []
        current_text = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.config.target_size:
                if current_text:
                    sub_chunk = {
                        'chunk_id': f"{chunk['chunk_id']}_sub_{len(sub_chunks)}",
                        'text': ' '.join(current_text),
                        'type': chunk['type'],
                        'size': current_size,
                        'metadata': chunk['metadata']
                    }
                    sub_chunks.append(sub_chunk)
                
                current_text = [sentence]
                current_size = sentence_size
            else:
                current_text.append(sentence)
                current_size += sentence_size
        
        # 마지막 서브 청크
        if current_text:
            sub_chunk = {
                'chunk_id': f"{chunk['chunk_id']}_sub_{len(sub_chunks)}",
                'text': ' '.join(current_text),
                'type': chunk['type'],
                'size': current_size,
                'metadata': chunk['metadata']
            }
            sub_chunks.append(sub_chunk)
        
        return sub_chunks


# Global instance
_korean_chunking_strategy: Optional[KoreanChunkingStrategy] = None


def get_korean_chunking_strategy(
    config: Optional[ChunkConfig] = None
) -> KoreanChunkingStrategy:
    """Get global Korean chunking strategy instance"""
    global _korean_chunking_strategy
    if _korean_chunking_strategy is None:
        _korean_chunking_strategy = KoreanChunkingStrategy(config)
    return _korean_chunking_strategy
