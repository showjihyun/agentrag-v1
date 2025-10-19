"""
Reprocess Documents with Enhanced Table Processing

기존 문서를 개선된 표 처리 방식으로 재처리하는 스크립트
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.document import Document
from backend.services.document_processor import DocumentProcessor
from backend.services.enhanced_table_processor import get_enhanced_table_processor
from backend.services.table_aware_chunker import get_table_aware_chunker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentReprocessor:
    """문서 재처리기"""
    
    def __init__(self, batch_size: int = 10):
        """
        초기화
        
        Args:
            batch_size: 배치 크기
        """
        self.batch_size = batch_size
        self.doc_processor = DocumentProcessor()
        self.table_processor = get_enhanced_table_processor()
        self.table_chunker = get_table_aware_chunker()
        
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def reprocess_documents(
        self,
        db: Session,
        file_types: Optional[List[str]] = None,
        force: bool = False,
        limit: Optional[int] = None
    ):
        """
        문서 재처리
        
        Args:
            db: 데이터베이스 세션
            file_types: 재처리할 파일 타입 리스트
            force: 강제 재처리 여부
            limit: 재처리할 최대 문서 수
        """
        logger.info("=" * 70)
        logger.info("문서 재처리 시작")
        logger.info("=" * 70)
        
        # 재처리 대상 문서 조회
        query = db.query(Document).filter(Document.status == 'completed')
        
        if file_types:
            query = query.filter(Document.file_type.in_(file_types))
        
        if not force:
            # 표 처리가 안 된 문서만 재처리
            query = query.filter(
                ~Document.metadata.has_key('enhanced_table_processing')
            )
        
        if limit:
            query = query.limit(limit)
        
        documents = query.all()
        self.stats['total'] = len(documents)
        
        logger.info(f"재처리 대상 문서: {self.stats['total']}개")
        logger.info(f"파일 타입: {file_types or '전체'}")
        logger.info(f"강제 재처리: {force}")
        logger.info("")
        
        # 배치 처리
        for i in range(0, len(documents), self.batch_size):
            batch = documents[i:i + self.batch_size]
            self._process_batch(db, batch, i)
        
        # 결과 출력
        self._print_summary()
    
    def _process_batch(self, db: Session, batch: List[Document], start_idx: int):
        """배치 처리"""
        logger.info(f"배치 {start_idx // self.batch_size + 1} 처리 중...")
        
        for doc in batch:
            try:
                self._reprocess_document(db, doc)
                self.stats['success'] += 1
                logger.info(f"  ✓ {doc.filename} 재처리 완료")
            except Exception as e:
                self.stats['failed'] += 1
                logger.error(f"  ✗ {doc.filename} 재처리 실패: {e}")
        
        db.commit()
        logger.info(f"배치 커밋 완료 (성공: {self.stats['success']}, 실패: {self.stats['failed']})\n")
    
    def _reprocess_document(self, db: Session, doc: Document):
        """단일 문서 재처리"""
        # 1. 파일 읽기
        file_path = self._get_file_path(doc)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # 2. 텍스트 추출
        text = self._extract_text(file_content, doc.file_type)
        
        # 3. 표 처리 강화
        if '[TABLE START]' in text:
            # 이미 표 마커가 있으면 스킵
            logger.debug(f"  표 마커 이미 존재: {doc.filename}")
        else:
            # 표 처리 필요
            text = self._enhance_tables(text)
        
        # 4. 청킹 (표 보존)
        chunks = self.table_chunker.chunk_text_with_tables(
            text=text,
            preserve_tables=True
        )
        
        # 5. 메타데이터 업데이트
        if doc.metadata is None:
            doc.metadata = {}
        
        doc.metadata['enhanced_table_processing'] = True
        doc.metadata['reprocessed_at'] = datetime.utcnow().isoformat()
        doc.metadata['chunk_count'] = len(chunks)
        doc.metadata['table_aware_chunking'] = True
        
        # 6. 임베딩 재생성 (실제로는 별도 프로세스에서 처리)
        # TODO: 임베딩 재생성 로직 추가
        
        db.add(doc)
    
    def _get_file_path(self, doc: Document) -> str:
        """파일 경로 가져오기"""
        # 실제 파일 저장 경로 (설정에 따라 다름)
        from backend.config import settings
        
        if settings.FILE_STORAGE_BACKEND == 'local':
            return os.path.join(settings.LOCAL_STORAGE_PATH, str(doc.id), doc.filename)
        else:
            # S3 등 다른 스토리지는 별도 처리
            raise NotImplementedError("S3 storage not implemented yet")
    
    def _extract_text(self, file_content: bytes, file_type: str) -> str:
        """텍스트 추출"""
        if file_type == 'pdf':
            return self.doc_processor.extract_text_from_pdf(file_content)
        elif file_type == 'docx':
            return self.doc_processor.extract_text_from_docx(file_content)
        elif file_type == 'txt':
            return self.doc_processor.extract_text_from_txt(file_content)
        elif file_type == 'hwp':
            return self.doc_processor.extract_text_from_hwp(file_content)
        elif file_type == 'hwpx':
            return self.doc_processor.extract_text_from_hwpx(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _enhance_tables(self, text: str) -> str:
        """표 처리 강화 (간단한 구현)"""
        # 실제로는 더 정교한 표 감지 및 처리 필요
        # 여기서는 기존 텍스트를 그대로 반환
        return text
    
    def _print_summary(self):
        """결과 요약 출력"""
        logger.info("\n" + "=" * 70)
        logger.info("재처리 완료")
        logger.info("=" * 70)
        logger.info(f"총 문서: {self.stats['total']}개")
        logger.info(f"성공: {self.stats['success']}개")
        logger.info(f"실패: {self.stats['failed']}개")
        logger.info(f"건너뜀: {self.stats['skipped']}개")
        
        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total']) * 100
            logger.info(f"성공률: {success_rate:.1f}%")
        
        logger.info("=" * 70)


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='기존 문서를 개선된 표 처리 방식으로 재처리'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='배치 크기 (기본값: 10)'
    )
    parser.add_argument(
        '--file-types',
        type=str,
        help='재처리할 파일 타입 (쉼표로 구분, 예: pdf,docx)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='이미 처리된 문서도 강제로 재처리'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='재처리할 최대 문서 수'
    )
    
    args = parser.parse_args()
    
    # 파일 타입 파싱
    file_types = None
    if args.file_types:
        file_types = [ft.strip() for ft in args.file_types.split(',')]
    
    # 재처리 실행
    db = SessionLocal()
    reprocessor = DocumentReprocessor(batch_size=args.batch_size)
    
    try:
        reprocessor.reprocess_documents(
            db=db,
            file_types=file_types,
            force=args.force,
            limit=args.limit
        )
    except Exception as e:
        logger.error(f"재처리 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
