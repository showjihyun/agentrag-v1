# 🚀 Get Started with Workflow Testing

워크플로우 테스트를 시작하기 위한 단계별 가이드입니다.

## Step 1: 시스템 준비 (2분)

### 1.1 서비스 실행 확인
```bash
# 백엔드 실행
cd backend
uvicorn main:app --reload

# 프론트엔드 실행 (새 터미널)
cd frontend
npm run dev

# 데이터베이스 실행 (새 터미널)
docker-compose up -d postgres milvus redis
```

### 1.2 시스템 검증
```bash
python tests/workflow-scenarios/verify-setup.py
```

**예상 결과**:
```
✓ Backend Health Check: OK
✓ Tools API: OK
✓ Blocks API: OK
✓ Workflows API: OK

✓ All checks passed (4/4)
System is ready for testing!
```

## Step 2: 첫 번째 워크플로우 만들기 (3분)

### 2.1 워크플로우 빌더 열기
브라우저에서 접속: http://localhost:3000/agent-builder/workflows/new

### 2.2 간단한 워크플로우 생성
1. **Workflow Name** 입력: "My First Workflow"
2. **Block Palette**에서 노드 추가:
   - Start 노드 드래그
   - Python Code 노드 드래그
   - End 노드 드래그
3. **노드 연결**: Start → Python Code → End
4. **Python Code 설정**:
   - 노드 클릭 → Config 탭
   - 코드 입력:
   ```python
   return {
       "message": "Hello from workflow!",
       "input_received": input
   }
   ```
5. **저장**: 상단 Save 버튼 클릭

### 2.3 워크플로우 실행
1. **Execute** 버튼 클릭
2. Input 입력:
   ```json
   {
     "name": "Test User",
     "value": 42
   }
   ```
3. **Run** 클릭
4. **결과 확인**: "Hello from workflow!" 메시지 확인

✅ **성공!** 첫 번째 워크플로우를 만들고 실행했습니다!

## Step 3: 주요 기능 테스트 (15분)

### 3.1 Quick Test Checklist 따라하기
```bash
cat tests/workflow-scenarios/QUICK_TEST_CHECKLIST.md
```

**테스트 순서**:
1. ✅ 기본 워크플로우 (완료!)
2. ⬜ Condition 분기
3. ⬜ HTTP Request
4. ⬜ Parallel & Merge
5. ⬜ AI Agent (선택사항)

### 3.2 결과 기록
```bash
# 테스트 결과 추가
python tests/workflow-scenarios/track-results.py add

# 입력 예시:
# Category: 1 (Basic)
# Test name: First Workflow
# Status: pass
# Notes: Successfully created and executed
```

## Step 4: 고급 기능 탐색 (30분+)

### 4.1 복잡한 워크플로우
- AI Research Assistant
- Data Processing Pipeline
- Customer Support Automation

### 4.2 상세 가이드 참조
```bash
cat tests/workflow-scenarios/MANUAL_TESTING_GUIDE.md
```

## 📊 진행 상황 확인

### 테스트 요약 보기
```bash
python tests/workflow-scenarios/track-results.py summary
```

### 최근 테스트 보기
```bash
python tests/workflow-scenarios/track-results.py recent
```

## 🎯 테스트 목표

### 최소 목표 (30분)
- [ ] 기본 워크플로우 생성 및 실행
- [ ] Python Code 노드 사용
- [ ] Condition 분기 테스트
- [ ] HTTP Request 테스트

### 권장 목표 (1시간)
- [ ] 최소 목표 완료
- [ ] Parallel & Merge 테스트
- [ ] Vector Search 테스트
- [ ] AI Agent 테스트 (선택)

### 완전 목표 (2시간)
- [ ] 권장 목표 완료
- [ ] 복잡한 워크플로우 1개 이상
- [ ] Slack/Gmail 통합 (선택)
- [ ] 모든 Control Flow 테스트

## 🐛 문제 발생 시

### 일반적인 문제

**1. 워크플로우가 저장되지 않음**
- Workflow Name이 입력되었는지 확인
- Start 노드가 있는지 확인
- 브라우저 콘솔에서 에러 확인 (F12)

**2. 노드 설정이 보이지 않음**
- 노드를 클릭했는지 확인
- 오른쪽 Properties Panel 확인
- 페이지 새로고침 시도

**3. 실행 시 에러**
- 각 노드의 필수 필드 확인
- 노드 간 연결 확인
- Execution History에서 에러 메시지 확인

**4. API 연결 실패**
```bash
# 백엔드 상태 확인
curl http://localhost:8000/health

# 시스템 재검증
python tests/workflow-scenarios/verify-setup.py
```

### 도움 받기
- [Troubleshooting Guide](../../docs/troubleshooting.md)
- [Workflow Documentation](../../docs/workflows.md)
- GitHub Issues: 문제 보고 및 질문

## 📚 다음 단계

### 학습 리소스
1. **QUICK_TEST_CHECKLIST.md** - 빠른 테스트 가이드
2. **MANUAL_TESTING_GUIDE.md** - 상세 테스트 가이드
3. **MULTIPLE_EDGES_GUIDE.md** - 다중 연결 기능

### 실전 예제
- `08-complex-workflows/` - 복잡한 워크플로우 예제
- `09-real-world/` - 실제 사용 사례

### 커스터마이징
- 자신만의 워크플로우 설계
- 새로운 도구 조합 시도
- 팀과 워크플로우 공유

## 🎉 축하합니다!

워크플로우 테스트 시스템을 성공적으로 시작했습니다!

**다음 목표**:
- [ ] 5개 이상의 워크플로우 생성
- [ ] 모든 주요 도구 테스트
- [ ] 실제 업무에 워크플로우 적용

---

**질문이나 피드백이 있으신가요?**
- 팀 채널에 공유
- GitHub Issues에 등록
- 문서 개선 제안

**Happy Testing! 🚀**
