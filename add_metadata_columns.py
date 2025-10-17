"""
문서 메타데이터 컬럼 추가 스크립트

document_title, document_author 등 메타데이터 컬럼 추가
"""

import asyncio
import logging
from sqlalchemy import text
from backend.db.database import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_metadata_columns():
    """메타데이터 컬럼 추가"""
    
    logger.info("메타데이터 컬럼 추가 시작...")
    
    db = SessionLocal()
    
    try:
        # 추가할 컬럼 정의
        columns_to_add = [
            ("document_title", "VARCHAR(500)", False),
            ("document_author", "VARCHAR(200)", True),  # 인덱스 필요
            ("document_subject", "VARCHAR(500)", False),
            ("document_keywords", "TEXT", False),
            ("document_language", "VARCHAR(10)", True),  # 인덱스 필요
            ("document_creation_date", "TIMESTAMP", True),  # 인덱스 필요
            ("document_modification_date", "TIMESTAMP", False),
        ]
        
        for col_name, col_type, needs_index in columns_to_add:
            logger.info(f"\n{col_name} 컬럼 확인 중...")
            
            # 컬럼 존재 확인
            check_col = text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='documents' AND column_name='{col_name}'
            """)
            
            result = db.execute(check_col).fetchone()
            
            if not result:
                logger.info(f"   {col_name} 컬럼이 없습니다. 추가 중...")
                
                # 컬럼 추가
                add_col = text(f"""
                    ALTER TABLE documents 
                    ADD COLUMN {col_name} {col_type}
                """)
                db.execute(add_col)
                
                logger.info(f"   ✅ {col_name} 컬럼 추가 완료")
                
                # 인덱스 추가 (필요한 경우)
                if needs_index:
                    try:
                        index_name = f"ix_documents_{col_name}"
                        add_index = text(f"""
                            CREATE INDEX {index_name} ON documents({col_name})
                        """)
                        db.execute(add_index)
                        logger.info(f"   ✅ {col_name} 인덱스 추가 완료")
                    except Exception as e:
                        logger.warning(f"   ⚠️ 인덱스 추가 실패 (무시 가능): {e}")
            else:
                logger.info(f"   ✅ {col_name} 컬럼이 이미 존재합니다")
        
        # 커밋
        db.commit()
        
        logger.info("\n✅ 메타데이터 컬럼 추가 완료!")
        
        # 최종 테이블 구조 확인
        logger.info("\n최종 테이블 구조:")
        
        check_columns = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name='documents'
            ORDER BY ordinal_position
        """)
        
        columns = db.execute(check_columns).fetchall()
        
        logger.info(f"\ndocuments 테이블 컬럼 ({len(columns)}개):")
        for col in columns:
            logger.info(f"  - {col[0]}: {col[1]} (nullable={col[2]})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 컬럼 추가 실패: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()


async def main():
    """메인 함수"""
    logger.info("="*80)
    logger.info("문서 메타데이터 컬럼 추가 스크립트")
    logger.info("="*80)
    
    success = await add_metadata_columns()
    
    if success:
        logger.info("\n" + "="*80)
        logger.info("✅ 메타데이터 컬럼 추가 완료!")
        logger.info("="*80)
        logger.info("\n이제 애플리케이션을 다시 시작하세요:")
        logger.info("  docker-compose restart backend")
    else:
        logger.error("\n" + "="*80)
        logger.error("❌ 컬럼 추가 실패")
        logger.error("="*80)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
