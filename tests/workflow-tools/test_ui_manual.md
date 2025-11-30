# Workflow Tools UI/UX 수동 테스트 가이드

## 테스트 환경
- Frontend: http://localhost:3001
- Backend: http://localhost:8000

## 1. 도구 팔레트 테스트

### 1.1 카테고리 표시 확인
- [ ] AI 카테고리 표시 (OpenAI, Claude, Gemini, AI Agent)
- [ ] Communication 카테고리 표시 (Slack, Discord, Telegram)
- [ ] Data 카테고리 표시 (PostgreSQL, MongoDB, Redis)
- [ ] Search 카테고리 표시 (Tavily, DuckDuckGo, Wikipedia)
- [ ] Developer 카테고리 표시 (HTTP Request)

### 1.2 도구 아이콘 및 색상
- [ ] 각 도구별 고유 아이콘 표시
- [ ] 카테고리별 색상 구분

## 2. 도구 설정 패널 테스트

### 2.1 HTTP Request Config
- [ ] Method 선택 (GET, POST, PUT, DELETE)
- [ ] URL 입력 필드
- [ ] Headers 탭 - 헤더 추가/삭제
- [ ] Query 탭 - 쿼리 파라미터 추가/삭제
- [ ] Body 탭 - JSON 본문 입력
- [ ] Auth 탭 - Bearer/Basic/API Key 인증
- [ ] Settings 탭 - Timeout, Retry 설정
- [ ] Test Request 버튼

### 2.2 Slack Config
- [ ] Bot Token 입력 (마스킹 처리)
- [ ] Action 선택 드롭다운
- [ ] Channel 입력 필드
- [ ] Message 텍스트 영역
- [ ] Thread TS 옵션
- [ ] Test Connection 버튼

### 2.3 OpenAI Chat Config
- [ ] API Key 입력
- [ ] Model 선택 (gpt-4, gpt-3.5-turbo)
- [ ] Temperature 슬라이더
- [ ] Max Tokens 입력
- [ ] System Prompt 입력

### 2.4 AI Agent Config
- [ ] Task 설명 입력
- [ ] LLM Provider 선택
- [ ] Model 선택
- [ ] Memory Type 선택
- [ ] Tools 선택

## 3. 워크플로우 캔버스 테스트

### 3.1 노드 추가
- [ ] 드래그 앤 드롭으로 노드 추가
- [ ] 더블 클릭으로 노드 추가
- [ ] 컨텍스트 메뉴로 노드 추가

### 3.2 노드 연결
- [ ] 출력 핸들에서 입력 핸들로 드래그
- [ ] 연결선 표시
- [ ] 연결 삭제

### 3.3 노드 편집
- [ ] 노드 클릭 시 설정 패널 열림
- [ ] 설정 변경 시 자동 저장
- [ ] 노드 삭제

## 4. 워크플로우 실행 테스트

### 4.1 실행 버튼
- [ ] Execute/Run 버튼 표시
- [ ] 실행 중 로딩 상태
- [ ] 실행 결과 표시

### 4.2 실행 결과
- [ ] 각 노드별 실행 상태 (성공/실패)
- [ ] 출력 데이터 표시
- [ ] 에러 메시지 표시

## 5. 반응형 테스트

### 5.1 데스크톱 (1920x1080)
- [ ] 전체 레이아웃 정상
- [ ] 사이드바 표시

### 5.2 태블릿 (1024x768)
- [ ] 레이아웃 조정
- [ ] 사이드바 토글

### 5.3 모바일 (375x667)
- [ ] 모바일 레이아웃
- [ ] 터치 인터랙션

## 6. 접근성 테스트

- [ ] 키보드 네비게이션
- [ ] 스크린 리더 호환
- [ ] 색상 대비
- [ ] 포커스 표시

## 테스트 결과 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| 도구 팔레트 | | |
| HTTP Request Config | | |
| Slack Config | | |
| OpenAI Config | | |
| AI Agent Config | | |
| 노드 추가/연결 | | |
| 워크플로우 실행 | | |
| 반응형 | | |
| 접근성 | | |

## 발견된 이슈

1. 
2. 
3. 

## 개선 제안

1. 
2. 
3. 
