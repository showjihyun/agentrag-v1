# Workflow Testing Guide

## 📋 Overview

이 가이드는 워크플로우 도구들의 종합 테스트를 실행하는 방법을 설명합니다.

## 🚀 Quick Start

### 1. 환경 설정

```bash
# Python 의존성 설치
pip install requests

# 환경 변수 설정
export API_BASE_URL="http://localhost:8000"
export API_TOKEN="your_token_here"  # Optional

# Slack 테스트를 위한 토큰 (선택사항)
export SLACK_BOT_TOKEN="xoxb-your-token"
```

### 2. 전체 테스트 실행

```bash
cd tests/workflow-scenarios
python test-runner.py --all
```

### 3. 카테고리별 테스트

```bash
# AI 도구 테스트
python test-runner.py --category 01-ai-tools

# 통신 도구 테스트
python test-runner.py --category 02-communication-tools

# API 통합 테스트
python test-runner.py --category 03-api-integration

# 데이터 도구 테스트
python test-runner.py --category 04-data-tools

# 코드 실행 테스트
python test-runner.py --category 05-code-execution

# 제어 흐름 테스트
python test-runner.py --category 06-control-flow

# 트리거 테스트
python test-runner.py --category 07-triggers

# 복잡한 워크플로우 테스트
python test-runner.py --category 08-complex-workflows
```

### 4. 특정 시나리오 테스트

```bash
python test-runner.py --scenario 01-ai-tools/openai-chat-basic.json
```

## 📊 테스트 카테고리

### 1. AI Tools (01-ai-tools/)
- ✅ OpenAI Chat (GPT-4, GPT-3.5)
- ✅ Claude (Anthropic)
- ✅ Gemini (Google)

**테스트 항목:**
- 기본 채팅 기능
- 시스템 메시지 설정
- Temperature 조정
- Max tokens 제한
- 스트리밍 응답

### 2. Communication Tools (02-communication-tools/)
- ✅ Slack 메시지 전송
- ✅ Gmail 이메일 전송
- ✅ Discord 웹훅
- ✅ Telegram 봇

**테스트 항목:**
- 메시지 전송
- 채널/수신자 지정
- 첨부 파일
- 포맷팅 (Markdown, HTML)

### 3. API Integration (03-api-integration/)
- ✅ HTTP GET 요청
- ✅ HTTP POST 요청
- ✅ Headers 설정
- ✅ Query parameters
- ✅ Request body

**테스트 항목:**
- 다양한 HTTP 메서드
- 인증 (Bearer, API Key)
- 타임아웃 처리
- 에러 핸들링

### 4. Data Tools (04-data-tools/)
- ✅ Vector Search (Milvus)
- ✅ PostgreSQL 쿼리
- ✅ CSV 파싱
- ✅ JSON 변환

**테스트 항목:**
- 시맨틱 검색
- SQL 쿼리 실행
- 데이터 변환
- 필터링 및 정렬

### 5. Code Execution (05-code-execution/)
- ✅ Python 코드 실행
- ✅ JavaScript 실행
- ✅ 라이브러리 import
- ✅ 타임아웃 처리

**테스트 항목:**
- 기본 연산
- 데이터 처리
- 외부 라이브러리 사용
- 에러 핸들링

### 6. Control Flow (06-control-flow/)
- ✅ Condition (if/else)
- ✅ Switch (다중 분기)
- ✅ Loop (반복)
- ✅ Parallel (병렬 실행)
- ✅ Merge (결과 병합)

**테스트 항목:**
- 조건부 분기
- 다중 경로 선택
- 반복 처리
- 병렬 실행 및 병합

### 7. Triggers (07-triggers/)
- ✅ Schedule (Cron)
- ✅ Webhook (HTTP)
- ✅ Manual (수동)
- ✅ Email (이메일 수신)

**테스트 항목:**
- 스케줄 설정
- Webhook URL 생성
- 수동 트리거
- 이메일 트리거

### 8. Complex Workflows (08-complex-workflows/)
- ✅ AI Research Assistant
- ✅ Data Processing Pipeline
- ✅ Multi-step Automation
- ✅ Error Recovery

**테스트 항목:**
- 다단계 워크플로우
- 조건부 분기 + 병렬 처리
- 에러 핸들링 및 복구
- 실제 사용 사례

## 📈 테스트 결과

테스트 결과는 `test-results/` 폴더에 저장됩니다:

```
test-results/
├── summary.json              # 전체 요약
├── 01-ai-tools/
│   └── openai-chat-basic/
│       ├── result.json
│       └── logs.txt
├── 02-communication-tools/
│   └── slack-message/
│       ├── result.json
│       └── logs.txt
└── ...
```

### 결과 파일 구조

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "summary": {
    "total_scenarios": 20,
    "passed_scenarios": 18,
    "failed_scenarios": 2,
    "total_tests": 45,
    "passed_tests": 42,
    "failed_tests": 3,
    "errors": 0
  },
  "results": [...]
}
```

## 🔍 Assertions (검증 항목)

각 테스트는 다음 항목들을 검증합니다:

### 성능
- `response_time`: 응답 시간 (초)
- `execution_time`: 실행 시간

### 출력
- `output_not_empty`: 출력이 비어있지 않음
- `output_has_keys`: 특정 키 존재
- `json_response`: JSON 형식 응답

### HTTP
- `http_status_code`: HTTP 상태 코드
- `status_code_2xx`: 2xx 성공 응답

### 에러
- `no_errors`: 에러 없음
- `error_handled`: 에러 처리됨

### 워크플로우
- `all_nodes_executed`: 모든 노드 실행됨
- `correct_branch_taken`: 올바른 분기 선택
- `all_parallel_branches_executed`: 모든 병렬 브랜치 실행
- `merge_successful`: 병합 성공

### 트리거
- `trigger_registered`: 트리거 등록됨
- `webhook_url_generated`: Webhook URL 생성됨
- `cron_expression_valid`: Cron 표현식 유효

## 🐛 Troubleshooting

### 일반적인 문제

**1. API 연결 실패**
```bash
# API 서버가 실행 중인지 확인
curl http://localhost:8000/health

# 포트 확인
export API_BASE_URL="http://localhost:8000"
```

**2. 인증 오류**
```bash
# 토큰 확인
export API_TOKEN="your_valid_token"
```

**3. Slack/Gmail 테스트 실패**
```bash
# 환경 변수 설정 확인
echo $SLACK_BOT_TOKEN
echo $GMAIL_CREDENTIALS
```

**4. Vector Search 실패**
```bash
# Milvus 실행 확인
docker ps | grep milvus

# Collection 존재 확인
python -c "from pymilvus import connections, utility; connections.connect(); print(utility.list_collections())"
```

## 📝 새로운 테스트 시나리오 추가

### 1. JSON 파일 생성

```json
{
  "name": "My Test Scenario",
  "description": "Test description",
  "category": "my-category",
  "workflow": {
    "nodes": [...],
    "edges": [...]
  },
  "test_cases": [
    {
      "name": "Test case 1",
      "input": {...},
      "expected_output": {...}
    }
  ],
  "assertions": [
    {
      "type": "response_time",
      "max_seconds": 5
    }
  ]
}
```

### 2. 적절한 폴더에 저장

```bash
tests/workflow-scenarios/[category]/[scenario-name].json
```

### 3. 테스트 실행

```bash
python test-runner.py --scenario [category]/[scenario-name].json
```

## 🎯 Best Practices

1. **독립적인 테스트**: 각 테스트는 다른 테스트에 의존하지 않아야 함
2. **명확한 이름**: 테스트 이름은 무엇을 테스트하는지 명확히 표현
3. **적절한 타임아웃**: 각 도구의 특성에 맞는 타임아웃 설정
4. **에러 처리**: 예상되는 에러 케이스도 테스트
5. **문서화**: 전제 조건과 예상 결과를 명확히 문서화

## 📚 참고 자료

- [Workflow Documentation](../../docs/workflows.md)
- [API Reference](../../docs/api-reference.md)
- [Tool Configuration](../../docs/tool-configuration.md)

## 🤝 Contributing

새로운 테스트 시나리오를 추가하거나 개선 사항이 있다면:

1. 새로운 시나리오 JSON 파일 작성
2. 테스트 실행 및 검증
3. Pull Request 생성
4. 문서 업데이트

---

**Last Updated**: 2024-01-01
**Version**: 1.0.0
