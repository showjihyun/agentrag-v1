# AgenticBuilder 설치 가이드

## 시스템 요구사항

### 최소 요구사항

**하드웨어:**
- CPU: 4 코어 이상
- RAM: 8GB 이상
- 디스크: 50GB 이상 여유 공간

**소프트웨어:**
- Docker 20.10 이상
- Docker Compose 2.0 이상
- (선택) Python 3.10 이상 (로컬 개발)
- (선택) Node.js 18 이상 (프론트엔드 개발)

### 권장 요구사항

**하드웨어:**
- CPU: 8 코어 이상
- RAM: 16GB 이상
- 디스크: 100GB 이상 SSD

**소프트웨어:**
- Docker 24.0 이상
- Docker Compose 2.20 이상

## Docker를 이용한 설치 (권장)

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/agenticbuilder.git
cd agenticbuilder
```

### 2. 환경 변수 설정

```bash
# 환경 변수 파일 복사
cp .env.example .env

# 환경 변수 편집
nano .env  # 또는 원하는 에디터 사용
```

**필수 환경 변수:**

```bash
# 데이터베이스
POSTGRES_DB=agenticrag
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password_here

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=  # 비워두면 비밀번호 없음

# Milvus
MILVUS_HOST=milvus
MILVUS_PORT=19530

# 보안
SECRET_KEY=your-secret-key-change-in-production
ENCRYPTION_KEY=your-encryption-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-change-in-production

# LLM 제공자 (최소 하나 필요)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk_...

# 애플리케이션
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production
```

**보안 키 생성:**

```bash
# Python을 사용한 랜덤 키 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Docker Compose로 실행

```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 특정 서비스 로그만 확인
docker-compose logs -f backend
```

### 4. 서비스 상태 확인

```bash
# 모든 컨테이너 상태 확인
docker-compose ps

# 헬스 체크
curl http://localhost:8000/api/health
```

**예상 출력:**
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "redis": {"status": "healthy"},
    "milvus": {"status": "healthy"}
  }
}
```

### 5. 초기 데이터베이스 설정

```bash
# 데이터베이스 마이그레이션 실행
docker-compose exec backend python -m alembic upgrade head

# 초기 데이터 시드 (선택)
docker-compose exec backend python scripts/seed_data.py
```

### 6. 접속 확인

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Milvus UI**: http://localhost:9092

## 로컬 개발 환경 설정

### Backend 설정

```bash
cd backend

# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집

# 데이터베이스 마이그레이션
alembic upgrade head

# 개발 서버 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend 설정

```bash
cd frontend

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env.local
# .env.local 파일 편집

# 개발 서버 실행
npm run dev
```

## 프로덕션 배포

### Docker Compose (프로덕션)

```bash
# 프로덕션 설정 사용
docker-compose -f docker-compose.prod.yml up -d

# 또는 최적화된 설정 사용
docker-compose -f docker-compose.optimized.yml up -d
```

### Kubernetes 배포

```bash
# Kubernetes 매니페스트 적용
kubectl apply -f k8s/

# 배포 상태 확인
kubectl get pods -n agenticbuilder

# 서비스 확인
kubectl get services -n agenticbuilder
```

**주요 Kubernetes 리소스:**
- Deployment: backend, frontend
- StatefulSet: postgres, redis, milvus
- Service: LoadBalancer, ClusterIP
- Ingress: HTTPS 라우팅
- ConfigMap: 설정 관리
- Secret: 민감 정보 관리

### 환경별 설정

**개발 환경:**
```bash
DEBUG=true
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

**스테이징 환경:**
```bash
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=staging
```

**프로덕션 환경:**
```bash
DEBUG=false
LOG_LEVEL=WARNING
ENVIRONMENT=production
```

## 데이터베이스 마이그레이션

### Alembic 사용

```bash
# 현재 마이그레이션 상태 확인
alembic current

# 최신 버전으로 업그레이드
alembic upgrade head

# 특정 버전으로 업그레이드
alembic upgrade <revision>

# 이전 버전으로 다운그레이드
alembic downgrade -1

# 새 마이그레이션 생성
alembic revision -m "Add new table"

# 자동 마이그레이션 생성 (모델 변경 감지)
alembic revision --autogenerate -m "Auto migration"
```

## 백업 및 복구

### 데이터베이스 백업

```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U postgres agenticrag > backup.sql

# 또는 Docker 볼륨 백업
docker run --rm -v agenticbuilder_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data
```

### 데이터베이스 복구

```bash
# PostgreSQL 복구
docker-compose exec -T postgres psql -U postgres agenticrag < backup.sql

# 또는 Docker 볼륨 복구
docker run --rm -v agenticbuilder_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

### Milvus 백업

```bash
# Milvus 데이터 백업
docker run --rm -v agenticbuilder_milvus_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/milvus_backup.tar.gz /data
```

## 모니터링 설정

### Prometheus & Grafana

```bash
# 모니터링 스택 시작
docker-compose --profile monitoring up -d

# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

### Jaeger (분산 추적)

```bash
# Jaeger 시작
docker-compose --profile monitoring up -d jaeger

# Jaeger UI: http://localhost:16686
```

## 문제 해결

### 일반적인 문제

**1. 포트 충돌**
```bash
# 사용 중인 포트 확인
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# docker-compose.yml에서 포트 변경
ports:
  - "8001:8000"  # 호스트:컨테이너
```

**2. 데이터베이스 연결 실패**
```bash
# 데이터베이스 컨테이너 로그 확인
docker-compose logs postgres

# 데이터베이스 연결 테스트
docker-compose exec backend python -c "from backend.db.database import engine; print(engine.connect())"
```

**3. Milvus 연결 실패**
```bash
# Milvus 상태 확인
docker-compose logs milvus

# Milvus 재시작
docker-compose restart milvus etcd minio
```

**4. 메모리 부족**
```bash
# Docker 메모리 제한 증가
# Docker Desktop > Settings > Resources > Memory
# 최소 8GB 권장

# 또는 docker-compose.yml에서 제한 조정
deploy:
  resources:
    limits:
      memory: 4G
```

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs -f

# 특정 서비스 로그
docker-compose logs -f backend

# 최근 100줄만 보기
docker-compose logs --tail=100 backend

# 타임스탬프 포함
docker-compose logs -f -t backend
```

### 컨테이너 재시작

```bash
# 모든 서비스 재시작
docker-compose restart

# 특정 서비스만 재시작
docker-compose restart backend

# 서비스 중지 후 재시작
docker-compose down
docker-compose up -d
```

### 데이터 초기화

```bash
# 모든 데이터 삭제 (주의!)
docker-compose down -v

# 특정 볼륨만 삭제
docker volume rm agenticbuilder_postgres_data
```

## 업그레이드

### 새 버전으로 업그레이드

```bash
# 최신 코드 가져오기
git pull origin main

# 이미지 재빌드
docker-compose build

# 서비스 재시작
docker-compose down
docker-compose up -d

# 데이터베이스 마이그레이션
docker-compose exec backend alembic upgrade head
```

## 보안 체크리스트

- [ ] 모든 기본 비밀번호 변경
- [ ] SECRET_KEY, ENCRYPTION_KEY, JWT_SECRET_KEY 변경
- [ ] HTTPS 설정 (프로덕션)
- [ ] 방화벽 규칙 설정
- [ ] 정기적인 백업 설정
- [ ] 로그 모니터링 설정
- [ ] Rate Limiting 활성화
- [ ] CORS 설정 검토

## 다음 단계

설치가 완료되면:

1. [API 레퍼런스](03-api-reference.md) 확인
2. [워크플로우 시스템](04-workflow-system.md) 학습
3. 첫 번째 워크플로우 생성
4. [모범 사례](06-best-practices.md) 검토

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026-01-20
