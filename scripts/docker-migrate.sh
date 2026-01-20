#!/bin/bash
# Docker 컨테이너에서 Alembic 마이그레이션 실행
# Usage: ./docker-migrate.sh [command] [target]
# Commands: upgrade, current, history, downgrade

set -e

echo "========================================"
echo "Docker 컨테이너 마이그레이션 실행"
echo "========================================"
echo ""

# 컨테이너 실행 확인
if ! docker ps | grep -q agenticrag-backend; then
    echo "[ERROR] agenticrag-backend 컨테이너가 실행 중이 아닙니다."
    echo ""
    echo "컨테이너를 먼저 시작하세요:"
    echo "  docker-compose up -d"
    echo ""
    exit 1
fi

# 명령어 파라미터 (기본값: upgrade head)
COMMAND=${1:-upgrade}
TARGET=${2:-}

if [ -z "$TARGET" ]; then
    if [ "$COMMAND" = "upgrade" ]; then
        TARGET="head"
    elif [ "$COMMAND" = "downgrade" ]; then
        TARGET="-1"
    fi
fi

echo "실행 명령: alembic $COMMAND $TARGET"
echo ""

# Docker 컨테이너에서 마이그레이션 실행
if docker exec -it agenticrag-backend alembic $COMMAND $TARGET; then
    echo ""
    echo "========================================"
    echo "마이그레이션 성공!"
    echo "========================================"
    echo ""
    
    # 현재 마이그레이션 버전 확인
    echo "현재 마이그레이션 버전:"
    docker exec -it agenticrag-backend alembic current
else
    echo ""
    echo "========================================"
    echo "마이그레이션 실패!"
    echo "========================================"
    echo ""
    echo "로그를 확인하세요:"
    echo "  docker logs agenticrag-backend"
    echo ""
    exit 1
fi

echo ""
