#!/usr/bin/env python3
"""
프로덕션 배포 검증 스크립트

배포 후 모든 서비스가 정상 작동하는지 확인합니다.
"""

import sys
import requests
import logging
from sqlalchemy import create_engine, text
from config import settings
import redis
from pymilvus import connections

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_production_deployment():
    """프로덕션 배포 검증"""

    logger.info("=" * 70)
    logger.info("프로덕션 배포 검증")
    logger.info("=" * 70)

    all_passed = True

    # 1. 데이터베이스 연결 확인
    logger.info("\n" + "-" * 70)
    logger.info("1. PostgreSQL 연결")
    logger.info("-" * 70)

    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"✓ PostgreSQL 연결 성공")
            logger.info(f"  버전: {version.split(',')[0]}")
    except Exception as e:
        logger.error(f"✗ PostgreSQL 연결 실패: {e}")
        all_passed = False

    # 2. Redis 연결 확인
    logger.info("\n" + "-" * 70)
    logger.info("2. Redis 연결")
    logger.info("-" * 70)

    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=getattr(settings, "REDIS_PASSWORD", None),
            decode_responses=True,
        )
        r.ping()
        info = r.info()
        logger.info(f"✓ Redis 연결 성공")
        logger.info(f"  버전: {info['redis_version']}")
    except Exception as e:
        logger.error(f"✗ Redis 연결 실패: {e}")
        all_passed = False

    # 3. Milvus 연결 확인
    logger.info("\n" + "-" * 70)
    logger.info("3. Milvus 연결")
    logger.info("-" * 70)

    try:
        connections.connect(
            alias="default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT
        )
        logger.info(f"✓ Milvus 연결 성공")
        connections.disconnect("default")
    except Exception as e:
        logger.error(f"✗ Milvus 연결 실패: {e}")
        all_passed = False

    # 4. Backend API Health Check
    logger.info("\n" + "-" * 70)
    logger.info("4. Backend API")
    logger.info("-" * 70)

    backend_url = f"http://localhost:{settings.BACKEND_PORT}"

    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ Backend API 정상")
            logger.info(f"  상태: {data.get('status')}")
        else:
            logger.error(f"✗ Backend API 응답 오류: {response.status_code}")
            all_passed = False
    except Exception as e:
        logger.error(f"✗ Backend API 연결 실패: {e}")
        all_passed = False

    # 5. API 엔드포인트 테스트
    logger.info("\n" + "-" * 70)
    logger.info("5. API 엔드포인트")
    logger.info("-" * 70)

    endpoints = [
        ("/api/auth/register", "POST", "회원가입"),
        ("/api/query", "POST", "쿼리 실행"),
        ("/api/documents", "GET", "문서 목록"),
    ]

    for path, method, description in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{backend_url}{path}", timeout=5)
            else:
                response = requests.post(f"{backend_url}{path}", json={}, timeout=5)

            # 401, 422는 정상 (인증 필요, 유효성 검사 실패)
            if response.status_code in [200, 401, 422]:
                logger.info(f"✓ {description}: 엔드포인트 존재")
            else:
                logger.warning(
                    f"⚠ {description}: 예상치 못한 응답 {response.status_code}"
                )
        except Exception as e:
            logger.error(f"✗ {description}: {e}")
            all_passed = False

    # 최종 결과
    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("✓ 프로덕션 배포 검증 통과!")
        logger.info("=" * 70)
        logger.info("\n시스템이 정상적으로 실행 중입니다.")
        logger.info("\n다음 단계:")
        logger.info("  1. 모니터링 대시보드 확인")
        logger.info("  2. 사용자 테스트 진행")
        logger.info("  3. 성능 모니터링 시작")
    else:
        logger.error("✗ 프로덕션 배포 검증 실패")
        logger.error("=" * 70)
        logger.error("\n문제를 해결한 후 다시 실행하세요.")

    logger.info("")
    return all_passed


if __name__ == "__main__":
    try:
        success = verify_production_deployment()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"✗ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
