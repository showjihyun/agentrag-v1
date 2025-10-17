#!/usr/bin/env python3
"""
환경 변수 설정 검증 스크립트

프로덕션 배포 전 필수 환경 변수가 올바르게 설정되었는지 확인합니다.
"""

import os
import sys
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_env_config():
    """환경 변수 설정 검증"""

    logger.info("=" * 70)
    logger.info("환경 변수 설정 검증")
    logger.info("=" * 70)

    all_passed = True
    warnings = []

    # 1. 필수 환경 변수 확인
    logger.info("\n" + "-" * 70)
    logger.info("1. 필수 환경 변수")
    logger.info("-" * 70)

    required_vars = {
        "DATABASE_URL": "데이터베이스 연결 문자열",
        "SECRET_KEY": "애플리케이션 비밀 키",
        "JWT_SECRET_KEY": "JWT 비밀 키",
        "REDIS_HOST": "Redis 호스트",
        "MILVUS_HOST": "Milvus 호스트",
    }

    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # 민감한 정보는 마스킹
            if "SECRET" in var or "PASSWORD" in var:
                display_value = (
                    value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
                )
            else:
                display_value = value
            logger.info(f"✓ {var}: {display_value}")
        else:
            logger.error(f"✗ {var}: 설정되지 않음 ({description})")
            all_passed = False

    # 2. 보안 설정 검증
    logger.info("\n" + "-" * 70)
    logger.info("2. 보안 설정")
    logger.info("-" * 70)

    # SECRET_KEY 강도 확인
    secret_key = os.getenv("SECRET_KEY", "")
    if len(secret_key) < 32:
        logger.error(
            f"✗ SECRET_KEY가 너무 짧습니다 (최소 32자 권장, 현재: {len(secret_key)}자)"
        )
        all_passed = False
    elif secret_key == "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION":
        logger.error("✗ SECRET_KEY가 기본값입니다. 반드시 변경하세요!")
        all_passed = False
    else:
        logger.info(f"✓ SECRET_KEY 길이: {len(secret_key)}자")

    # JWT_SECRET_KEY 확인
    jwt_secret = os.getenv("JWT_SECRET_KEY", "")
    if len(jwt_secret) < 32:
        logger.error(f"✗ JWT_SECRET_KEY가 너무 짧습니다 (최소 32자 권장)")
        all_passed = False
    elif jwt_secret == "CHANGE_THIS_JWT_SECRET_IN_PRODUCTION":
        logger.error("✗ JWT_SECRET_KEY가 기본값입니다. 반드시 변경하세요!")
        all_passed = False
    else:
        logger.info(f"✓ JWT_SECRET_KEY 길이: {len(jwt_secret)}자")

    # 비밀번호 강도 확인
    postgres_password = os.getenv("POSTGRES_PASSWORD", "")
    if postgres_password == "CHANGE_THIS_PASSWORD_IN_PRODUCTION":
        logger.error("✗ POSTGRES_PASSWORD가 기본값입니다. 반드시 변경하세요!")
        all_passed = False
    elif len(postgres_password) < 12:
        warnings.append("POSTGRES_PASSWORD가 짧습니다 (12자 이상 권장)")
    else:
        logger.info("✓ POSTGRES_PASSWORD 설정됨")

    # 3. LLM 설정 검증
    logger.info("\n" + "-" * 70)
    logger.info("3. LLM 설정")
    logger.info("-" * 70)

    llm_provider = os.getenv("LLM_PROVIDER", "ollama")
    llm_model = os.getenv("LLM_MODEL", "")

    logger.info(f"✓ LLM Provider: {llm_provider}")
    logger.info(f"✓ LLM Model: {llm_model}")

    if llm_provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key or not openai_key.startswith("sk-"):
            logger.error("✗ OPENAI_API_KEY가 올바르지 않습니다")
            all_passed = False
        else:
            logger.info("✓ OPENAI_API_KEY 설정됨")

    elif llm_provider == "claude":
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not claude_key or not claude_key.startswith("sk-ant-"):
            logger.error("✗ ANTHROPIC_API_KEY가 올바르지 않습니다")
            all_passed = False
        else:
            logger.info("✓ ANTHROPIC_API_KEY 설정됨")

    elif llm_provider == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        logger.info(f"✓ Ollama URL: {ollama_url}")

    # 4. 데이터베이스 설정 검증
    logger.info("\n" + "-" * 70)
    logger.info("4. 데이터베이스 설정")
    logger.info("-" * 70)

    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        # URL 파싱
        if "postgresql://" in database_url:
            logger.info("✓ PostgreSQL 연결 문자열 형식 확인")

            # 호스트 추출
            match = re.search(r"@([^:]+):", database_url)
            if match:
                host = match.group(1)
                logger.info(f"✓ 데이터베이스 호스트: {host}")
        else:
            logger.error("✗ DATABASE_URL 형식이 올바르지 않습니다")
            all_passed = False

    # 5. CORS 설정 검증
    logger.info("\n" + "-" * 70)
    logger.info("5. CORS 설정")
    logger.info("-" * 70)

    cors_origins = os.getenv("CORS_ORIGINS", "")
    if cors_origins:
        origins = [o.strip() for o in cors_origins.split(",")]
        logger.info(f"✓ 허용된 Origin: {len(origins)}개")
        for origin in origins:
            if origin.startswith("https://"):
                logger.info(f"  ✓ {origin}")
            elif origin.startswith("http://localhost"):
                warnings.append(f"개발 환경 Origin이 포함됨: {origin}")
            else:
                logger.warning(f"  ⚠ HTTPS가 아닌 Origin: {origin}")
    else:
        warnings.append("CORS_ORIGINS가 설정되지 않음 (모든 Origin 허용)")

    # 6. 환경 설정 확인
    logger.info("\n" + "-" * 70)
    logger.info("6. 환경 설정")
    logger.info("-" * 70)

    environment = os.getenv("ENVIRONMENT", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    logger.info(f"✓ 환경: {environment}")
    logger.info(f"✓ 로그 레벨: {log_level}")

    if environment != "production":
        warnings.append(f"ENVIRONMENT가 'production'이 아닙니다: {environment}")

    # 7. 선택적 설정 확인
    logger.info("\n" + "-" * 70)
    logger.info("7. 선택적 설정")
    logger.info("-" * 70)

    optional_vars = {
        "SENTRY_DSN": "에러 모니터링",
        "SMTP_HOST": "이메일 발송",
        "S3_ENDPOINT": "파일 스토리지",
    }

    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"✓ {var}: 설정됨 ({description})")
        else:
            logger.info(f"⊘ {var}: 미설정 ({description})")

    # 경고 출력
    if warnings:
        logger.info("\n" + "-" * 70)
        logger.info("⚠ 경고")
        logger.info("-" * 70)
        for warning in warnings:
            logger.warning(f"⚠ {warning}")

    # 최종 결과
    logger.info("\n" + "=" * 70)
    if all_passed:
        logger.info("✓ 환경 변수 검증 통과!")
        logger.info("=" * 70)
        if warnings:
            logger.info(f"\n⚠ {len(warnings)}개의 경고가 있습니다. 확인하세요.")
        logger.info("\n다음 단계:")
        logger.info("  1. 마이그레이션 실행: python run_migrations.py")
        logger.info("  2. 마이그레이션 검증: python verify_all_migrations.py")
        logger.info(
            "  3. 프로덕션 배포: docker-compose -f docker-compose.prod.yml up -d"
        )
    else:
        logger.error("✗ 환경 변수 검증 실패")
        logger.error("=" * 70)
        logger.error("\n필수 환경 변수를 설정한 후 다시 실행하세요.")
        logger.error("참고: .env.production.example 파일을 확인하세요.")

    logger.info("")
    return all_passed


if __name__ == "__main__":
    try:
        success = verify_env_config()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"✗ 예상치 못한 오류: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
