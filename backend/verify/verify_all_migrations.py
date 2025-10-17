#!/usr/bin/env python3
"""
모든 마이그레이션 검증 스크립트

이 스크립트는 모든 마이그레이션이 올바르게 적용되었는지 확인합니다.
"""

import sys
from sqlalchemy import create_engine, inspect, text
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_all_migrations():
    """모든 마이그레이션 검증"""

    logger.info("=" * 70)
    logger.info("마이그레이션 검증 시작")
    logger.info("=" * 70)

    # 데이터베이스 연결
    try:
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        logger.info(f"✓ 데이터베이스 연결 성공")
    except Exception as e:
        logger.error(f"✗ 데이터베이스 연결 실패: {e}")
        return False

    all_passed = True

    # 1. 문서 버전 관리 검증
    logger.info("\n" + "-" * 70)
    logger.info("1. 문서 버전 관리 (Document Versioning)")
    logger.info("-" * 70)

    try:
        tables = inspector.get_table_names()

        if "document_versions" in tables:
            logger.info("✓ document_versions 테이블 존재")

            columns = {
                col["name"] for col in inspector.get_columns("document_versions")
            }
            required = {
                "id",
                "document_id",
                "version",
                "content_hash",
                "changes_summary",
            }

            if required.issubset(columns):
                logger.info("✓ 필수 컬럼 모두 존재")
            else:
                logger.error(f"✗ 누락된 컬럼: {required - columns}")
                all_passed = False
        else:
            logger.error("✗ document_versions 테이블 없음")
            all_passed = False

    except Exception as e:
        logger.error(f"✗ 검증 실패: {e}")
        all_passed = False

    # 2. 메타데이터 추출 검증
    logger.info("\n" + "-" * 70)
    logger.info("2. 메타데이터 추출 (Metadata Extraction)")
    logger.info("-" * 70)

    try:
        if "documents" in tables:
            columns = {col["name"] for col in inspector.get_columns("documents")}
            metadata_fields = {
                "author",
                "title",
                "language",
                "page_count",
                "word_count",
                "creation_date",
                "keywords",
            }

            if metadata_fields.issubset(columns):
                logger.info("✓ 메타데이터 필드 모두 존재")
            else:
                logger.error(f"✗ 누락된 필드: {metadata_fields - columns}")
                all_passed = False
        else:
            logger.error("✗ documents 테이블 없음")
            all_passed = False

    except Exception as e:
        logger.error(f"✗ 검증 실패: {e}")
        all_passed = False

    # 3. 문서 ACL 검증
    logger.info("\n" + "-" * 70)
    logger.info("3. 문서 접근 제어 (Document ACL)")
    logger.info("-" * 70)

    try:
        acl_tables = {"document_permissions", "permission_groups", "group_members"}

        if acl_tables.issubset(set(tables)):
            logger.info("✓ ACL 테이블 모두 존재")

            # 인덱스 확인
            perm_indexes = inspector.get_indexes("document_permissions")
            index_names = {idx["name"] for idx in perm_indexes}

            if "idx_doc_perm_lookup" in index_names:
                logger.info("✓ ACL 인덱스 존재")
            else:
                logger.warning("⚠ ACL 인덱스 없음 (성능 저하 가능)")
        else:
            logger.error(f"✗ 누락된 테이블: {acl_tables - set(tables)}")
            all_passed = False

    except Exception as e:
        logger.error(f"✗ 검증 실패: {e}")
        all_passed = False

    # 4. 답변 품질 평가 검증
    logger.info("\n" + "-" * 70)
    logger.info("4. 답변 품질 평가 (Answer Quality)")
    logger.info("-" * 70)

    try:
        if "feedback" in tables:
            logger.info("✓ feedback 테이블 존재")

            columns = {col["name"] for col in inspector.get_columns("feedback")}
            required = {"id", "message_id", "user_id", "rating", "feedback_type"}

            if required.issubset(columns):
                logger.info("✓ 피드백 필드 모두 존재")
            else:
                logger.error(f"✗ 누락된 필드: {required - columns}")
                all_passed = False
        else:
            logger.error("✗ feedback 테이블 없음")
            all_passed = False

    except Exception as e:
        logger.error(f"✗ 검증 실패: {e}")
        all_passed = False

    # 5. 마이그레이션 히스토리 확인
    logger.info("\n" + "-" * 70)
    logger.info("5. 마이그레이션 히스토리")
    logger.info("-" * 70)

    try:
        if "migration_history" in tables:
            with engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                    SELECT filename, applied_at, success
                    FROM migration_history
                    ORDER BY applied_at
                """
                    )
                )

                migrations = result.fetchall()

                if migrations:
                    logger.info(f"✓ 적용된 마이그레이션: {len(migrations)}개")
                    for mig in migrations:
                        status = "✓" if mig[2] else "✗"
                        logger.info(f"  {status} {mig[0]} ({mig[1]})")
                else:
                    logger.warning("⚠ 적용된 마이그레이션 없음")
        else:
            logger.warning("⚠ migration_history 테이블 없음")

    except Exception as e:
        logger.error(f"✗ 검증 실패: {e}")
        all_passed = False

    # 최종 결과
    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("✓ 모든 마이그레이션 검증 통과!")
        logger.info("=" * 70)
        logger.info("\n다음 단계:")
        logger.info("  1. 환경 변수 설정: python verify_env_config.py")
        logger.info(
            "  2. 프로덕션 배포: docker-compose -f docker-compose.prod.yml up -d"
        )
        logger.info("  3. 배포 후 검증: python verify_production_deployment.py")
    else:
        logger.error("✗ 일부 검증 실패")
        logger.error("=" * 70)
        logger.error("\n문제를 해결한 후 다시 실행하세요.")

    logger.info("")
    return all_passed


if __name__ == "__main__":
    try:
        success = verify_all_migrations()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"✗ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
