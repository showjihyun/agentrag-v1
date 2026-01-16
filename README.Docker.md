# Docker 배포 가이드 🐳

Agentic RAG 시스템의 Docker 기반 배포를 위한 빠른 시작 가이드입니다.

---

## 🚀 빠른 시작

### 1. 사전 요구사항

- Docker 20.10+ 설치
- Docker Compose 2.0+ 설치
- 최소 8GB RAM
- 20GB 디스크 공간

### 2. 환경 설정

```bash
# .env 파일 생성
cp backend/.env.example backend/.env

# 환경 변수 편집 (필수!)
# - SECRET_KEY, ENCRYPTION_KEY, JWT_SECRET_KEY 변경
# - 데이터베이스 비밀번호 변경
# - API 키 설정
```

### 3. 빌드 & 실행

**Windows:**
```batch
scripts\docker-build.bat
scripts\docker-start.bat
```

**Linux/Mac:**
```bash
./scripts/docker-build.sh
./scripts/docker-start.sh
```

### 4. 접속 확인

- **API:** http://localhost:8000
- **API 문서:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/health

---

## 📋 포함된 서비스

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Backend API | 8000 | FastAPI 애플리케이션 |
| PostgreSQL | 5433 | 메인 데이터베이스 |
| Redis | 6380 | 캐시 & 세션 스토어 |
| Milvus | 19530 | 벡터 데이터베이스 |
| MinIO | 9002 | 객체 스토리지 (Milvus) |
| Jaeger | 16686 | 분산 추적 (선택적) |
| Prometheus | 9090 | 메트릭 수집 (선택적) |
| Grafana | 3001 | 메트릭 시각화 (선택적) |

---

## 🛠️ 주요 명령어

### 서비스 관리

```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 재시작
docker-compose restart

# 로그 확인
docker-compose logs -f backend

# 서비스 상태
docker-compose ps
```

### 데이터베이스 마이그레이션

```bash
# Windows
scripts\docker-migrate.bat

# Linux/Mac
./scripts/docker-migrate.sh

# 또는 직접 실행
docker-compose exec backend alembic upgrade head
```

### 컨테이너 접속

```bash
# Backend 쉘
docker-compose exec backend bash

# PostgreSQL
docker-compose exec postgres psql -U postgres -d agenticrag

# Redis CLI
docker-compose exec redis redis-cli
```

---

## 📊 모니터링

### 모니터링 서비스 시작

```bash
# 모니터링 프로파일 포함하여 시작
docker-compose --profile monitoring up -d
```

### 접속 주소

- **Jaeger UI:** http://localhost:16686
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001 (admin/admin)

---

## 🔐 보안 설정

### 필수 변경 사항

1. **보안 키 생성:**
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **환경 변수 설정:**
```bash
SECRET_KEY=<생성된-키>
ENCRYPTION_KEY=<생성된-키>
JWT_SECRET_KEY=<생성된-키>
POSTGRES_PASSWORD=<강력한-비밀번호>
REDIS_PASSWORD=<강력한-비밀번호>
```

3. **프로덕션 체크리스트:**
- [ ] 모든 기본 비밀번호 변경
- [ ] DEBUG=false 설정
- [ ] CORS 설정 확인
- [ ] SSL/TLS 인증서 설정
- [ ] 방화벽 규칙 설정

---

## 🚀 프로덕션 배포

### 1. 프로덕션 환경 설정

```bash
# 프로덕션 환경 변수 복사
cp backend/.env.production.example backend/.env.production

# 모든 값 설정
nano backend/.env.production
```

### 2. 프로덕션 이미지 빌드

```bash
docker build -f backend/Dockerfile.optimized -t agenticrag-backend:prod ./backend
```

### 3. 프로덕션 시작

```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🐛 트러블슈팅

### 서비스가 시작되지 않음

```bash
# 로그 확인
docker-compose logs backend

# 컨테이너 상태
docker-compose ps

# 헬스체크 확인
docker inspect agenticrag-backend | grep -A 10 Health
```

### 포트 충돌

```bash
# 포트 사용 확인
netstat -tulpn | grep 8000  # Linux
netstat -ano | findstr :8000  # Windows

# docker-compose.yml에서 포트 변경
ports:
  - "8001:8000"
```

### 메모리 부족

```bash
# 리소스 사용량 확인
docker stats

# Docker Desktop에서 메모리 할당 증가
# Settings > Resources > Memory > 8GB+
```

### 전체 재시작

```bash
# Windows
scripts\docker-clean.bat
scripts\docker-build.bat
scripts\docker-start.bat

# Linux/Mac
./scripts/docker-clean.sh
./scripts/docker-build.sh
./scripts/docker-start.sh
```

---

## 📦 백업 & 복구

### PostgreSQL 백업

```bash
# 백업
docker-compose exec postgres pg_dump -U postgres agenticrag > backup.sql

# 복구
cat backup.sql | docker-compose exec -T postgres psql -U postgres agenticrag
```

### Redis 백업

```bash
# 백업
docker-compose exec redis redis-cli SAVE
docker cp agenticrag-redis:/data/dump.rdb ./backup/

# 복구
docker cp ./backup/dump.rdb agenticrag-redis:/data/
docker-compose restart redis
```

---

## 📚 추가 문서

- **완전한 가이드:** [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md)
- **빠른 참조:** [docs/DOCKER_QUICK_REFERENCE.md](docs/DOCKER_QUICK_REFERENCE.md)
- **완료 요약:** [docs/DOCKER_COMPLETION_SUMMARY.md](docs/DOCKER_COMPLETION_SUMMARY.md)

---

## 🔧 개발 팁

### 핫 리로드 활성화

```yaml
# docker-compose.yml에 추가
services:
  backend:
    volumes:
      - ./backend:/app
    command: uvicorn main:app --reload --host 0.0.0.0
```

### 특정 서비스만 시작

```bash
docker-compose up -d postgres redis
```

### 로그 필터링

```bash
# 에러만 보기
docker-compose logs backend | grep ERROR

# 특정 시간 이후
docker-compose logs --since 2024-01-16T10:00:00 backend
```

---

## 💡 유용한 스크립트

### Windows
- `scripts\docker-build.bat` - 이미지 빌드
- `scripts\docker-start.bat` - 서비스 시작
- `scripts\docker-stop.bat` - 서비스 중지
- `scripts\docker-restart.bat` - 서비스 재시작
- `scripts\docker-logs.bat` - 로그 확인
- `scripts\docker-shell.bat` - 컨테이너 접속
- `scripts\docker-migrate.bat` - 마이그레이션
- `scripts\docker-clean.bat` - 전체 정리

### Linux/Mac
- `./scripts/docker-build.sh` - 이미지 빌드
- `./scripts/docker-start.sh` - 서비스 시작
- `./scripts/docker-stop.sh` - 서비스 중지
- `./scripts/docker-restart.sh` - 서비스 재시작
- `./scripts/docker-logs.sh` - 로그 확인
- `./scripts/docker-shell.sh` - 컨테이너 접속
- `./scripts/docker-migrate.sh` - 마이그레이션
- `./scripts/docker-clean.sh` - 전체 정리

---

## 📞 지원

문제가 발생하면:
1. [트러블슈팅 가이드](docs/DOCKER_GUIDE.md#트러블슈팅) 확인
2. 로그 확인: `docker-compose logs backend`
3. 헬스 체크: `curl http://localhost:8000/api/health`

---

**버전:** 2.0  
**최종 업데이트:** 2026-01-16  
**작성자:** Kiro AI Assistant

