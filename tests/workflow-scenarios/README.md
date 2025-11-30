# Workflow Tools Test Scenarios

워크플로우의 모든 도구, 조건, 트리거에 대한 종합 테스트 시나리오입니다.

## 🚀 Quick Start

### 처음 시작하시나요?
```bash
# 단계별 가이드 확인
cat tests/workflow-scenarios/GET_STARTED.md
```

### 1. 시스템 확인 (1분)
```bash
python tests/workflow-scenarios/verify-setup.py
```

### 2. 빠른 테스트 (5-30분)
```bash
# Quick Test Checklist 확인
cat tests/workflow-scenarios/QUICK_TEST_CHECKLIST.md

# 브라우저에서 워크플로우 빌더 열기
http://localhost:3000/agent-builder/workflows/new
```

**추천 테스트 순서**:
1. ⚡ 5분: 기본 기능 (Start→End, Python Code, Condition)
2. 🎯 15분: 주요 도구 (HTTP, AI, Parallel/Merge, Vector Search)
3. 🔥 30분: 복잡한 워크플로우 (AI Research, Data Pipeline, Integrations)

### 3. 결과 추적
```bash
# 테스트 결과 기록
python tests/workflow-scenarios/track-results.py add

# 요약 보기
python tests/workflow-scenarios/track-results.py summary
```

### 4. 상세 테스트 (1-2시간)
```bash
# 전체 테스트 가이드
cat tests/workflow-scenarios/MANUAL_TESTING_GUIDE.md
```

### 5. 자동 테스트 (개발 중)
```bash
# 주의: 백엔드 API 통합 이슈로 현재 작동하지 않을 수 있음
python tests/workflow-scenarios/test-runner.py --scenario 00-basic/simple-workflow.json
```

## 📁 테스트 구조

```
tests/workflow-scenarios/
├── README.md                          # 이 파일
├── QUICK_TEST_CHECKLIST.md            # 빠른 테스트 체크리스트 (⚡ 시작하기)
├── MANUAL_TESTING_GUIDE.md            # 상세 수동 테스트 가이드
├── TESTING_GUIDE.md                   # 자동 테스트 가이드
├── verify-setup.py                    # 시스템 검증 스크립트
├── test-runner.py                     # 자동 테스트 실행 스크립트
│
├── 00-basic/                          # 기본 테스트
│   └── simple-workflow.json
├── 01-ai-tools/                       # AI 도구 테스트
│   └── openai-chat-basic.json
├── 02-communication-tools/            # 통신 도구 테스트
│   ├── slack-message.json
│   └── gmail-send.json
├── 03-api-integration/                # API 통합 테스트
│   └── http-request-get.json
├── 04-data-tools/                     # 데이터 도구 테스트
│   └── vector-search.json
├── 05-code-execution/                 # 코드 실행 테스트
│   └── python-code.json
├── 06-control-flow/                   # 제어 흐름 테스트
│   ├── condition-branching.json
│   └── parallel-merge.json
├── 07-triggers/                       # 트리거 테스트
│   ├── schedule-trigger.json
│   └── webhook-trigger.json
├── 08-complex-workflows/              # 복잡한 워크플로우 테스트
│   ├── ai-research-assistant.json
│   └── data-pipeline.json
└── 09-real-world/                     # 실제 사용 사례
    └── customer-support-automation.json
```

## ✅ 테스트 커버리지

### AI Tools (AI 도구)
- ✅ OpenAI Chat (GPT-4, GPT-3.5)
- ✅ Claude (Anthropic)
- ✅ Gemini (Google)

### Communication Tools (통신 도구)
- ✅ Slack 메시지 전송
- ✅ Gmail 이메일 전송
- ✅ Discord 웹훅
- ✅ Telegram 봇

### API Integration (API 통합)
- ✅ HTTP Request (GET, POST, PUT, DELETE)
- ✅ Webhook 수신
- ✅ GraphQL 쿼리

### Data Tools (데이터 도구)
- ✅ Vector Search (Milvus)
- ✅ PostgreSQL 쿼리
- ✅ CSV 파싱
- ✅ JSON 변환

### Code Execution (코드 실행)
- ✅ Python 코드 실행
- ✅ JavaScript 실행

### Control Flow (제어 흐름)
- ✅ Condition (if/else 분기)
- ✅ Switch (다중 분기)
- ✅ Loop (반복)
- ✅ Parallel (병렬 실행)
- ✅ Merge (결과 병합)

### Triggers (트리거)
- ✅ Schedule (Cron 스케줄)
- ✅ Webhook (HTTP 트리거)
- ✅ Manual (수동 트리거)
- ✅ Email (이메일 트리거)

### Complex Workflows (복잡한 워크플로우)
- ✅ AI Research Assistant (Vector Search + AI + Slack)
- ✅ Data Processing Pipeline (HTTP + Transform + Parallel + Merge)

## 📊 테스트 방법

### 수동 테스트 (권장)

1. **시스템 확인**
   ```bash
   python tests/workflow-scenarios/verify-setup.py
   ```

2. **워크플로우 빌더 열기**
   ```
   http://localhost:3000/agent-builder/workflows/new
   ```

3. **가이드 따라하기**
   - `MANUAL_TESTING_GUIDE.md` 참조
   - 각 도구별 체크리스트 완료
   - 결과 기록

### 자동 테스트 (개발 중)

```bash
# 전체 테스트
python tests/workflow-scenarios/test-runner.py --all

# 카테고리별
python tests/workflow-scenarios/test-runner.py --category 01-ai-tools

# 특정 시나리오
python tests/workflow-scenarios/test-runner.py --scenario 05-code-execution/python-code.json
```

**참고**: 자동 테스트는 현재 백엔드 API 통합 이슈로 완전히 작동하지 않을 수 있습니다.

## 🐛 문제 해결

### 시스템 검증 실패
```bash
# 백엔드 실행 확인
cd backend && uvicorn main:app --reload

# 프론트엔드 실행 확인
cd frontend && npm run dev

# 데이터베이스 실행 확인
docker-compose up -d postgres milvus redis
```

### 워크플로우 생성 실패
- Workflow Name 입력 확인
- Start 노드 존재 확인
- 모든 노드 연결 확인

### 도구 설정 문제
- 필수 필드 입력 확인
- API 키/토큰 설정 확인
- 네트워크 연결 확인

## 📝 테스트 결과 기록

### 수동 기록
테스트 완료 후 `MANUAL_TESTING_GUIDE.md` 또는 `QUICK_TEST_CHECKLIST.md`의 체크리스트를 작성하여 팀과 공유하세요.

### 자동 추적
```bash
# 테스트 결과 추가
python tests/workflow-scenarios/track-results.py add

# 요약 보기
python tests/workflow-scenarios/track-results.py summary

# 최근 테스트 보기
python tests/workflow-scenarios/track-results.py recent
```

## 🤝 기여하기

새로운 테스트 시나리오 추가:
1. 적절한 카테고리 폴더에 JSON 파일 생성
2. `MANUAL_TESTING_GUIDE.md`에 테스트 케이스 추가
3. 테스트 실행 및 검증
4. Pull Request 생성

---

**Last Updated**: 2024-11-23
**Status**: ✅ Manual Testing Ready | ⚠️ Automated Testing In Progress
