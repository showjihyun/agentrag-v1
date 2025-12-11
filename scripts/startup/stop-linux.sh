#!/bin/bash

# ============================================
# Agent Builder - Linux/Mac 종료 스크립트
# ============================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Agent Builder 서버를 종료하는 중...${NC}"
echo ""

# PID 파일에서 프로세스 종료
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        echo -e "${GREEN}✓ 백엔드 서버 종료됨 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${YELLOW}백엔드 서버가 이미 종료되었습니다.${NC}"
    fi
    rm .backend.pid
fi

if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ 프론트엔드 서버 종료됨 (PID: $FRONTEND_PID)${NC}"
    else
        echo -e "${YELLOW}프론트엔드 서버가 이미 종료되었습니다.${NC}"
    fi
    rm .frontend.pid
fi

# 포트로 실행 중인 프로세스 찾아서 종료
echo ""
echo "포트 8000, 3000에서 실행 중인 프로세스 확인 중..."

# 백엔드 포트 (8000)
BACKEND_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PIDS" ]; then
    echo -e "${YELLOW}포트 8000에서 실행 중인 프로세스 발견: $BACKEND_PIDS${NC}"
    kill -9 $BACKEND_PIDS 2>/dev/null
    echo -e "${GREEN}✓ 포트 8000 정리 완료${NC}"
fi

# 프론트엔드 포트 (3000)
FRONTEND_PIDS=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo -e "${YELLOW}포트 3000에서 실행 중인 프로세스 발견: $FRONTEND_PIDS${NC}"
    kill -9 $FRONTEND_PIDS 2>/dev/null
    echo -e "${GREEN}✓ 포트 3000 정리 완료${NC}"
fi

echo ""
echo -e "${GREEN}모든 서버가 종료되었습니다.${NC}"
