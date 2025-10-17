#!/usr/bin/env python3
"""
데이터베이스 마이그레이션 실행 스크립트

이 스크립트는 모든 SQL 마이그레이션 파일을 순서대로 실행합니다.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migrations():
    """모든 마이그레이션 파일 실행"""

    logger.info("=" * 70)
    logger.info("데이터베이스 마이그레이션 시작")
    logger.info("=" * 70)

    # 데이터베이스 연결
    try:
        engine = create_engine(settings.DATABASE_URL)
        logger.info(f"✓ 데이터베이스 연결 성공: {settings.DATABASE_URL.split('@')[1]}")
    except Exception as e:
        logger.error(f"✗ 데이터베이스 연결 실패: {e}")
        return False

    # 마이그레이션 파일 디렉토리
    migrations_dir = Path(__file__).parent / "db" / "migrations"

    if not migrations_dir.exists():
        logger.error(f"✗ 마이그레이션 디렉토리를 찾을 수 없습니다: {migrations_dir}")
        return False

    # 마이그레이션 파일 목록 (순서대로)
    migration_files = [
        "add_document_versioning.sql",
        "add_document_metadata_fields.sql",
        "add_document_acl.sql",
        "add_answer_feedback.sql",
    ]

    # 마이그레이션 추적 테이블 생성
    with engine.connect() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS migration_history (
                id SERIAL PRIMARY KEY,
                filename VARCHAR(255) UNIQUE NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE
            )
        """
            )
        )
        conn.commit()
        logger.info("✓ 마이그레이션 추적 테이블 준비 완료")

    # 각 마이그레이션 파일 실행
    success_count = 0
    skip_count = 0
    error_count = 0

    for filename in migration_files:
        filepath = migrations_dir / filename

        if not filepath.exists():
            logger.warning(f"⚠ 파일을 찾을 수 없습니다: {filename}")
            continue

        # 이미 실행된 마이그레이션인지 확인
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM migration_history WHERE filename = :filename"
                ),
                {"filename": filename},
            )
            already_applied = result.scalar() > 0

        if already_applied:
            logger.info(f"⊘ 이미 적용됨: {filename}")
            skip_count += 1
            continue

        # 마이그레이션 실행
        logger.info(f"→ 실행 중: {filename}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()

            with engine.connect() as conn:
                # SQL 파일 실행
                conn.execute(text(sql_content))

                # 마이그레이션 기록
                conn.execute(
                    text(
                        """
                        INSERT INTO migration_history (filename, success)
                        VALUES (:filename, TRUE)
                    """
                    ),
                    {"filename": filename},
                )
                conn.commit()

            logger.info(f"✓ 성공: {filename}")
            success_count += 1

        except Exception as e:
            logger.error(f"✗ 실패: {filename}")
            logger.error(f"  에러: {str(e)}")
            error_count += 1

            # 실패 기록
            try:
                with engine.connect() as conn:
                    conn.execute(
                        text(
                            """
                            INSERT INTO migration_history (filename, success)
                            VALUES (:filename, FALSE)
                        """
                        ),
                        {"filename": filename},
                    )
                    conn.commit()
            except:
                pass

    # 결과 요약
    logger.info("")
    logger.info("=" * 70)
    logger.info("마이그레이션 완료")
    logger.info("=" * 70)
    logger.info(f"✓ 성공: {success_count}개")
    logger.info(f"⊘ 건너뜀: {skip_count}개")
    logger.info(f"✗ 실패: {error_count}개")
    logger.info("")

    if error_count > 0:
        logger.error("⚠ 일부 마이그레이션이 실패했습니다. 로그를 확인하세요.")
        return False

    logger.info("✓ 모든 마이그레이션이 성공적으로 완료되었습니다!")
    return True


if __name__ == "__main__":
    try:
        success = run_migrations()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"✗ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
