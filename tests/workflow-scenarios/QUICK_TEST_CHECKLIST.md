# Quick Test Checklist

빠르게 주요 기능을 테스트하기 위한 체크리스트입니다.

## 🚀 5분 Quick Test

### 1. 기본 워크플로우 생성 (1분)
- [ ] http://localhost:3000/agent-builder/workflows/new 접속
- [ ] Workflow Name 입력: "Quick Test"
- [ ] Block Palette에서 "Start" 드래그
- [ ] Block Palette에서 "End" 드래그
- [ ] Start → End 연결
- [ ] 저장 버튼 클릭
- [ ] ✅ 성공 메시지 확인

### 2. Python Code 노드 테스트 (2분)
- [ ] 새 워크플로우 생성
- [ ] Start → Python Code → End 구성
- [ ] Python Code 노드 클릭
- [ ] Config 탭에서 코드 입력:
```python
return {"result": "Hello from Python!", "input": input}
```
- [ ] 저장
- [ ] 실행 버튼 클릭
- [ ] Input: `{"test": "data"}`
- [ ] ✅ 결과에 "Hello from Python!" 포함 확인

### 3. Condition 분기 테스트 (2분)
- [ ] Start → Condition → End 구성
- [ ] Condition 노드 설정:
  - Operator: greater_than
  - Condition: `input.get('value', 0) > 50`
- [ ] True/False 출력에 각각 Python Code 연결
- [ ] 테스트 1: `{"value": 75}` → True 경로
- [ ] 테스트 2: `{"value": 25}` → False 경로
- [ ] ✅ 올바른 분기 확인

## 🎯 15분 Comprehensive Test

### 4. HTTP Request 테스트 (3분)
- [ ] Start → HTTP Request → End
- [ ] Config:
  - Method: GET
  - URL: `https://api.github.com/users/github`
- [ ] 실행
- [ ] ✅ GitHub 사용자 데이터 반환 확인

### 5. AI Agent 테스트 (5분)
- [ ] Start → AI Agent → End
- [ ] Config:
  - Provider: Ollama (또는 OpenAI)
  - Model: llama3.3:70b (또는 gpt-4)
  - System Prompt: "You are a helpful assistant"
  - Prompt: "Explain {{input.topic}} in one sentence"
- [ ] 실행: `{"topic": "quantum computing"}`
- [ ] ✅ AI 응답 생성 확인

### 6. Parallel & Merge 테스트 (4분)
- [ ] Start → Parallel → (3개 Python Code) → Merge → End
- [ ] Parallel 설정: 3 branches
- [ ] 각 Python Code:
  - Task 1: `return {"task": 1, "result": input.get('value') * 2}`
  - Task 2: `return {"task": 2, "result": input.get('value') + 10}`
  - Task 3: `return {"task": 3, "result": input.get('value') ** 2}`
- [ ] Merge 설정: wait_all, 3 inputs
- [ ] 실행: `{"value": 5}`
- [ ] ✅ 3개 결과 모두 병합 확인

### 7. Vector Search 테스트 (3분)
- [ ] Start → Vector Search → End
- [ ] Config:
  - Query: `{{input.query}}`
  - Collection: documents
  - Top K: 3
  - Score Threshold: 0.7
- [ ] 실행: `{"query": "machine learning"}`
- [ ] ✅ 관련 문서 반환 확인

## 🔥 30분 Full Test

### 8. Complex Workflow: AI Research Pipeline (10분)
```
Start → Vector Search → Condition → [True] → AI Agent → Python (Format) → End
                                  → [False] → Python (No Results) → End
```
- [ ] Vector Search: 문서 검색
- [ ] Condition: 결과 존재 여부 확인
- [ ] AI Agent: 검색 결과 분석
- [ ] Python Format: 결과 포맷팅
- [ ] 실행 및 검증

### 9. Data Processing Pipeline (10분)
```
Start → HTTP GET → Python Filter → Parallel → Stats → Merge → Python Summary → End
                                            → Transform →
                                            → Validate →
```
- [ ] HTTP GET: 외부 API 데이터 가져오기
- [ ] Python Filter: 데이터 필터링
- [ ] Parallel: 3개 처리 작업 병렬 실행
- [ ] Merge: 결과 병합
- [ ] Summary: 최종 요약
- [ ] 실행 및 검증

### 10. Slack/Gmail Integration (10분)
- [ ] Slack 메시지 전송 테스트
- [ ] Gmail 이메일 전송 테스트
- [ ] Webhook 트리거 테스트
- [ ] Schedule 트리거 설정

## 📊 테스트 결과

| 테스트 | 상태 | 시간 | 비고 |
|--------|------|------|------|
| 1. 기본 워크플로우 | ⬜ | ___ | |
| 2. Python Code | ⬜ | ___ | |
| 3. Condition | ⬜ | ___ | |
| 4. HTTP Request | ⬜ | ___ | |
| 5. AI Agent | ⬜ | ___ | |
| 6. Parallel & Merge | ⬜ | ___ | |
| 7. Vector Search | ⬜ | ___ | |
| 8. AI Research | ⬜ | ___ | |
| 9. Data Pipeline | ⬜ | ___ | |
| 10. Integrations | ⬜ | ___ | |

**범례**: ⬜ 미실행 | ✅ 성공 | ❌ 실패 | ⚠️ 부분 성공

## 🐛 발견된 이슈

1. _______________________________________________
   - 재현 단계: _________________________________
   - 예상 결과: _________________________________
   - 실제 결과: _________________________________

2. _______________________________________________

3. _______________________________________________

## 💡 개선 제안

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

---

**테스트 일시**: _______________
**테스터**: _______________
**환경**: Development / Staging / Production
