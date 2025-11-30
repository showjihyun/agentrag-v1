# Manual Workflow Testing Guide

백엔드 API 통합 이슈로 인해, UI를 통한 수동 테스트 가이드를 제공합니다.

## 🎯 테스트 목표

모든 워크플로우 도구, 조건, 트리거가 정상적으로 작동하는지 확인합니다.

## 📋 테스트 체크리스트

### 1. AI Tools (AI 도구)

#### OpenAI Chat
- [ ] 워크플로우 생성: Start → OpenAI Chat → End
- [ ] Config 설정:
  - Model: GPT-4 Turbo
  - System Message: "You are a helpful assistant"
  - Prompt: "Explain {{input}} in one sentence"
  - Temperature: 0.7
- [ ] 실행 테스트:
  - Input: `{"input": "artificial intelligence"}`
  - 예상: AI가 한 문장으로 설명
- [ ] 검증: ✅ 응답 생성됨, ✅ 에러 없음

#### Claude / Gemini
- [ ] 동일한 방식으로 테스트
- [ ] 각 모델의 특성 확인

### 2. Communication Tools (통신 도구)

#### Slack
- [ ] 워크플로우: Start → Slack → End
- [ ] Config:
  - Action: Send Message
  - Channel: #general
  - Message: "Test from workflow: {{input.message}}"
  - Bot Token: (환경 변수 또는 직접 입력)
- [ ] 실행: `{"message": "Hello World"}`
- [ ] 검증: ✅ Slack에 메시지 도착

#### Gmail
- [ ] 워크플로우: Start → Gmail → End
- [ ] Config:
  - Action: Send Email
  - To: test@example.com
  - Subject: "Test Email"
  - Body: HTML 또는 Plain Text
- [ ] 실행 및 검증

### 3. API Integration (API 통합)

#### HTTP Request - GET
- [ ] 워크플로우: Start → HTTP Request → End
- [ ] Config:
  - Method: GET
  - URL: `https://jsonplaceholder.typicode.com/users/1`
  - Headers: Accept: application/json
- [ ] 실행: `{}`
- [ ] 검증: ✅ 사용자 데이터 반환

#### HTTP Request - POST
- [ ] Method: POST
- [ ] URL: `https://jsonplaceholder.typicode.com/posts`
- [ ] Body: `{"title": "Test", "body": "Content", "userId": 1}`
- [ ] 검증: ✅ 201 Created 응답

### 4. Data Tools (데이터 도구)

#### Vector Search
- [ ] 워크플로우: Start → Vector Search → End
- [ ] Config:
  - Query: "{{input.query}}"
  - Collection: documents
  - Top K: 5
  - Score Threshold: 0.7
- [ ] 실행: `{"query": "AI and machine learning"}`
- [ ] 검증: ✅ 관련 문서 반환

### 5. Code Execution (코드 실행)

#### Python Code
- [ ] 워크플로우: Start → Python Code → End
- [ ] Config:
```python
numbers = input.get('numbers', [])
return {
    'sum': sum(numbers),
    'average': sum(numbers) / len(numbers) if numbers else 0
}
```
- [ ] 실행: `{"numbers": [1, 2, 3, 4, 5]}`
- [ ] 검증: ✅ sum=15, average=3

### 6. Control Flow (제어 흐름)

#### Condition (조건 분기)
```
Start → Condition → [True] → Python (Pass) → End
                  → [False] → Python (Fail) → End
```
- [ ] Condition Config:
  - Operator: greater_than
  - Condition: `input.get('score', 0) >= 70`
- [ ] 테스트 1: `{"score": 85}` → True 경로
- [ ] 테스트 2: `{"score": 45}` → False 경로
- [ ] 검증: ✅ 올바른 분기 선택

#### Parallel & Merge (병렬 & 병합)
```
Start → Parallel → Task 1 → Merge → End
                → Task 2 →
                → Task 3 →
```
- [ ] Parallel Config: 3 branches
- [ ] Merge Config: Mode = wait_all, Input Count = 3
- [ ] 실행: `{"value": 10}`
- [ ] 검증: ✅ 모든 태스크 실행, ✅ 병합 성공

### 7. Triggers (트리거)

#### Schedule Trigger
- [ ] Trigger Config:
  - Preset: Every 5 Minutes
  - Cron: `*/5 * * * *`
  - Timezone: UTC
- [ ] 검증: ✅ 트리거 등록됨, ✅ Cron 표현식 유효

#### Webhook Trigger
- [ ] Trigger Config:
  - Webhook ID: test_webhook_001
- [ ] Webhook URL 복사
- [ ] 테스트: `curl -X POST [URL] -d '{"test": "data"}'`
- [ ] 검증: ✅ 워크플로우 실행됨

### 8. Complex Workflows (복잡한 워크플로우)

#### AI Research Assistant
```
Start → Vector Search → Condition → [True] → OpenAI → Slack → End
                                  → [False] → Python (No Results) → Slack → End
```
- [ ] 실행: `{"question": "What is RAG?"}`
- [ ] 검증: 
  - ✅ Vector search 실행
  - ✅ 조건 평가
  - ✅ AI 분석 (결과 있을 경우)
  - ✅ Slack 알림

#### Data Pipeline
```
Start → HTTP GET → Python Filter → Parallel → Stats → Merge → End
                                            → Summary →
                                            → Validate →
```
- [ ] 실행: `{}`
- [ ] 검증:
  - ✅ HTTP 데이터 가져오기
  - ✅ 필터링
  - ✅ 병렬 처리
  - ✅ 결과 병합

## 📊 테스트 결과 기록

### 테스트 실행 정보
- 날짜: _______________
- 테스터: _______________
- 환경: Development / Staging / Production

### 결과 요약
| 카테고리 | 총 테스트 | 통과 | 실패 | 비고 |
|---------|----------|------|------|------|
| AI Tools | 3 | ___ | ___ | |
| Communication | 2 | ___ | ___ | |
| API Integration | 2 | ___ | ___ | |
| Data Tools | 1 | ___ | ___ | |
| Code Execution | 1 | ___ | ___ | |
| Control Flow | 2 | ___ | ___ | |
| Triggers | 2 | ___ | ___ | |
| Complex Workflows | 2 | ___ | ___ | |
| **총계** | **15** | ___ | ___ | |

### 발견된 이슈
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### 개선 사항
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

## 🐛 일반적인 문제 해결

### 1. 워크플로우 생성 실패
- **증상**: 저장 버튼 클릭 시 에러
- **해결**: 
  - Workflow Name 입력 확인
  - Start 노드 존재 확인
  - 모든 노드가 연결되어 있는지 확인

### 2. 노드 설정이 저장되지 않음
- **증상**: Config 변경 후 저장되지 않음
- **해결**:
  - 노드 클릭 → Config 탭 → 설정 변경 → 다른 곳 클릭 (자동 저장)
  - 워크플로우 저장 버튼 클릭

### 3. 실행 시 에러
- **증상**: 워크플로우 실행 시 에러 발생
- **해결**:
  - 각 노드의 필수 필드 입력 확인
  - API 키/토큰 설정 확인
  - 네트워크 연결 확인

### 4. Slack/Gmail 연동 실패
- **증상**: 메시지/이메일 전송 실패
- **해결**:
  - Bot Token / API 키 확인
  - 권한 설정 확인
  - 채널/수신자 주소 확인

### 5. Vector Search 결과 없음
- **증상**: 검색 결과가 비어있음
- **해결**:
  - Milvus 실행 확인
  - Collection에 데이터 존재 확인
  - Score Threshold 낮추기 (0.5 이하)

## 📝 테스트 팁

1. **단계별 테스트**: 복잡한 워크플로우는 단계별로 나눠서 테스트
2. **로그 확인**: 실행 이력에서 각 노드의 입출력 확인
3. **에러 메시지**: 에러 발생 시 메시지를 자세히 읽고 기록
4. **재현 가능성**: 이슈 발견 시 재현 단계 기록
5. **스크린샷**: 중요한 설정이나 에러는 스크린샷 저장

## 🎓 추가 리소스

- [Workflow Documentation](../../docs/workflows.md)
- [Tool Configuration Guide](../../docs/tool-configuration.md)
- [Troubleshooting Guide](../../docs/troubleshooting.md)

---

**테스트 완료 후 이 문서를 업데이트하여 팀과 공유하세요!**
