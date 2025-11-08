#!/bin/bash

# ============================================
# Agent Builder - Linux/Mac 시작 스크립트
# ============================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 헤더 출력
echo -e "${GREEN}"
echo "========================================"
echo "   Agent Builder 시작 중..."
echo "========================================"
echo -e "${NC}"

# 환경 변수 확인
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[경고] .env 파일이 없습니다.${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}.env.example 파일을 .env로 복사하시겠습니까? (y/n)${NC}"
        read -r COPY_ENV
        if [ "$COPY_ENV" = "y" ] || [ "$COPY_ENV" = "Y" ]; then
            cp .env.example .env
            echo -e "${GREEN}.env 파일이 생성되었습니다. 설정을 확인하세요.${NC}"
            exit 1
        fi
    fi
    echo -e "${RED}[오류] .env 파일을 생성하고 다시 시도하세요.${NC}"
    exit 1
fi

# Python 버전 확인
echo -e "${BLUE}[1/6] Python 버전 확인 중...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[오류] Python3가 설치되어 있지 않습니다.${NC}"
    echo "Python 3.10 이상을 설치하세요: https://www.python.org/downloads/"
    exit 1
fi
python3 --version
echo ""

# Node.js 버전 확인
echo -e "${BLUE}[2/6] Node.js 버전 확인 중...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}[오류] Node.js가 설치되어 있지 않습니다.${NC}"
    echo "Node.js 18 이상을 설치하세요: https://nodejs.org/"
    exit 1
fi
node --version
echo ""

# 백엔드 의존성 설치 확인
echo -e "${BLUE}[3/6] 백엔드 의존성 확인 중...${NC}"
if [ ! -d "backend/venv" ]; then
    echo "가상환경이 없습니다. 생성 중..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "가상환경이 이미 존재합니다."
fi
echo ""

# 프론트엔드 의존성 설치 확인
echo -e "${BLUE}[4/6] 프론트엔드 의존성 확인 중...${NC}"
if [ ! -d "frontend/node_modules" ]; then
    echo "node_modules가 없습니다. 설치 중..."
    cd frontend
    npm install
    cd ..
else
    echo "node_modules가 이미 존재합니다."
fi
echo ""

# 데이터베이스 마이그레이션
echo -e "${BLUE}[5/6] 데이터베이스 마이그레이션 확인 중...${NC}"
cd backend
source venv/bin/activate
alembic upgrade head
cd ..
echo ""

# 서버 시작
echo -e "${BLUE}[6/6] 서버 시작 중...${NC}"
echo ""
echo -e "${GREEN}========================================"
echo "   백엔드: http://localhost:8000"
echo "   프론트엔드: http://localhost:3000"
echo "   API 문서: http://localhost:8000/docs"
echo "========================================${NC}"
echo ""
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

# 로그 디렉토리 생성
mkdir -p logs

# 백엔드 서버 시작 (백그라운드)
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo -e "${GREEN}✓ 백엔드 서버 시작됨 (PID: $BACKEND_PID)${NC}"

# 잠시 대기 (백엔드가 먼저 시작되도록)
sleep 3

# 프론트엔드 서버 시작 (백그라운드)
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "${GREEN}✓ 프론트엔드 서버 시작됨 (PID: $FRONTEND_PID)${NC}"
echo ""
echo -e "${GREEN}서버가 시작되었습니다!${NC}"
echo "브라우저에서 http://localhost:3000 을 열어주세요."
echo ""
echo "로그 확인:"
echo "  - 백엔드: tail -f logs/backend.log"
echo "  - 프론트엔드: tail -f logs/frontend.log"
echo ""

# PID 파일 저장
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# 종료 핸들러
cleanup() {
    echo ""
    echo -e "${YELLOW}서버를 종료하는 중...${NC}"
    
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        kill $BACKEND_PID 2>/dev/null
        rm .backend.pid
        echo -e "${GREEN}✓ 백엔드 서버 종료됨${NC}"
    fi
    
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        kill $FRONTEND_PID 2>/dev/null
        rm .frontend.pid
        echo -e "${GREEN}✓ 프론트엔드 서버 종료됨${NC}"
    fi
    
    echo -e "${GREEN}모든 서버가 종료되었습니다.${NC}"
    exit 0
}

# Ctrl+C 시그널 처리
trap cleanup SIGINT SIGTERM

# 서버 실행 유지
echo "서버가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요."
wait
