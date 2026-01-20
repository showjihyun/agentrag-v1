# AgenticBuilder 세미나 개요

## 세미나 소개

이 세미나는 AgenticBuilder 플랫폼의 전체 아키텍처, 핵심 기능, 그리고 실제 구현 방법을 다룹니다.

## 대상 청중

- **개발자**: 시스템 아키텍처와 API 이해
- **아키텍트**: 기술 스택과 설계 패턴 학습
- **DevOps**: 배포 및 운영 방법 습득
- **프로덕트 매니저**: 기능과 비즈니스 가치 파악

## 세미나 구성

### 1. 시스템 아키텍처 (30분)
📄 **문서**: [01-architecture.md](01-architecture.md)

**주요 내용:**
- 전체 시스템 구조
- 레이어별 역할과 책임
- 기술 스택 상세
- 데이터 흐름
- 확장성 및 성능 전략

**핵심 포인트:**
- 5개 레이어 아키텍처 (Frontend, API Gateway, Core Engine, AI/ML, Data)
- 비동기 처리 및 이벤트 기반 아키텍처
- 마이크로서비스 지향 설계
- 수평 확장 가능한 구조

### 2. 데이터베이스 스키마 (20분)
📄 **문서**: [02-database-schema.md](02-database-schema.md)

**주요 내용:**
- 47개 테이블 구조
- 도메인별 테이블 그룹
- 관계 및 인덱스 전략
- 성능 최적화 기법

**핵심 포인트:**
- 사용자, 에이전트, 워크플로우, 실행 이력 등 핵심 도메인
- PostgreSQL + Milvus 하이브리드 데이터베이스
- Connection Pooling 및 쿼리 최적화
- 백업 및 복구 전략

### 3. API 레퍼런스 (25분)
📄 **문서**: [03-api-reference.md](03-api-reference.md)

**주요 내용:**
- RESTful API 설계
- 인증 및 권한 관리
- 주요 엔드포인트 상세
- 실시간 스트리밍 (SSE, WebSocket)

**핵심 포인트:**
- JWT 기반 인증
- 8개 주요 API 그룹 (인증, 에이전트, 워크플로우, 블록, 지식베이스, 모니터링, 플러그인, 헬스체크)
- Rate Limiting 및 에러 처리
- OpenAPI/Swagger 자동 문서화

**실습:**
- Postman/Insomnia로 API 호출
- 워크플로우 생성 및 실행
- 실시간 스트리밍 체험

### 4. 워크플로우 시스템 (30분)
📄 **문서**: [04-workflow-system.md](04-workflow-system.md)

**주요 내용:**
- 워크플로우 구성 요소 (블록, 연결, 정의)
- 17가지 오케스트레이션 패턴
- 실행 프로세스 및 상태 관리
- 에러 처리 및 성능 최적화

**핵심 포인트:**
- 50+ 사전 구축 블록
- Sequential, Parallel, Hierarchical, Adaptive 등 다양한 패턴
- 실시간 모니터링 및 디버깅
- 버전 관리 및 테스팅

**데모:**
- 시각적 워크플로우 빌더 시연
- 실시간 실행 모니터링
- 에러 처리 및 재시도 로직

### 5. 설치 및 배포 (20분)
📄 **문서**: [05-installation-guide.md](05-installation-guide.md)

**주요 내용:**
- 시스템 요구사항
- Docker Compose 설치
- 로컬 개발 환경 설정
- 프로덕션 배포 (Kubernetes)

**핵심 포인트:**
- Docker 기반 간편 설치
- 환경 변수 설정
- 데이터베이스 마이그레이션
- 백업 및 복구

**실습:**
- Docker Compose로 전체 스택 실행
- 헬스 체크 및 로그 확인
- 첫 번째 워크플로우 생성

### 6. 핵심 기능 및 특장점 (25분)
📄 **문서**: [06-key-features.md](06-key-features.md)

**주요 내용:**
- 시각적 워크플로우 빌더
- 멀티 에이전트 오케스트레이션
- 멀티 LLM 지원
- 엔터프라이즈 RAG 시스템
- 실시간 스트리밍
- 플러그인 시스템
- 보안 및 성능

**핵심 포인트:**
- ReactFlow 기반 드래그 앤 드롭 에디터
- 17가지 오케스트레이션 패턴
- OpenAI, Claude, Gemini, Groq, Ollama 등 멀티 LLM
- Milvus Vector DB + Hybrid Search
- 엔터프라이즈급 보안 (JWT, OAuth2, 암호화)

**경쟁 우위:**
- vs Zapier: AI 네이티브, 오픈소스
- vs n8n: 멀티 에이전트, 17가지 패턴
- vs LangFlow: 프로덕션 레디, 엔터프라이즈 보안

## 세미나 일정

### 전체 일정 (2.5시간)

```
09:00 - 09:10  환영 및 소개
09:10 - 09:40  시스템 아키텍처
09:40 - 10:00  데이터베이스 스키마
10:00 - 10:25  API 레퍼런스 + 실습
10:25 - 10:35  휴식
10:35 - 11:05  워크플로우 시스템 + 데모
11:05 - 11:25  설치 및 배포 + 실습
11:25 - 11:50  핵심 기능 및 특장점
11:50 - 12:00  Q&A 및 마무리
```

## 사전 준비사항

### 필수 사항

1. **Docker 설치**
   - Docker Desktop (Windows/Mac)
   - Docker Engine (Linux)
   - Docker Compose 2.0+

2. **개발 도구**
   - VS Code 또는 선호하는 IDE
   - Git
   - Postman 또는 Insomnia (API 테스트)

3. **계정 준비**
   - GitHub 계정
   - OpenAI API Key (선택)
   - Anthropic API Key (선택)

### 권장 사항

1. **시스템 사양**
   - CPU: 4코어 이상
   - RAM: 8GB 이상
   - 디스크: 50GB 여유 공간

2. **사전 학습**
   - Python 기본 문법
   - REST API 개념
   - Docker 기본 사용법
   - AI/LLM 기본 개념

## 실습 환경

### 제공 자료

1. **소스 코드**
   ```bash
   git clone https://github.com/yourusername/agenticbuilder.git
   ```

2. **샘플 데이터**
   - 예제 워크플로우
   - 테스트 데이터셋
   - API 컬렉션 (Postman)

3. **문서**
   - 기술 문서 (docs/)
   - API 레퍼런스
   - 튜토리얼

### 실습 시나리오

**시나리오 1: 고객 지원 자동화**
- 웹훅 트리거로 고객 문의 수신
- AI 에이전트로 문의 분석
- 데이터베이스에 티켓 생성
- Slack으로 알림 발송

**시나리오 2: 문서 분석 파이프라인**
- 문서 업로드
- OCR 처리
- 벡터 임베딩 생성
- 지식 베이스 저장
- 검색 테스트

**시나리오 3: 멀티 에이전트 협업**
- 병렬 에이전트 실행
- 결과 합의 (Consensus)
- 최종 의사결정
- 실행 결과 모니터링

## 학습 목표

### 이해 (Understanding)

- [ ] AgenticBuilder의 전체 아키텍처 이해
- [ ] 각 레이어의 역할과 책임 파악
- [ ] 데이터베이스 스키마 구조 이해
- [ ] API 설계 원칙 학습

### 적용 (Application)

- [ ] Docker로 전체 스택 실행
- [ ] API를 통한 워크플로우 생성
- [ ] 시각적 에디터로 워크플로우 구축
- [ ] 실시간 모니터링 활용

### 분석 (Analysis)

- [ ] 오케스트레이션 패턴 비교 분석
- [ ] 성능 최적화 전략 이해
- [ ] 보안 메커니즘 분석
- [ ] 확장성 설계 평가

### 평가 (Evaluation)

- [ ] 경쟁 제품과 비교
- [ ] 사용 사례별 적합성 판단
- [ ] 기술 스택 선택 근거 이해
- [ ] 프로덕션 준비도 평가

## 추가 자료

### 공식 문서

- **GitHub**: https://github.com/yourusername/agenticbuilder
- **문서 사이트**: https://docs.agenticbuilder.com
- **API 문서**: http://localhost:8000/docs

### 커뮤니티

- **Discord**: https://discord.gg/agenticbuilder
- **GitHub Discussions**: https://github.com/yourusername/agenticbuilder/discussions
- **Reddit**: https://reddit.com/r/agenticbuilder

### 학습 리소스

- **튜토리얼**: docs/tutorials/
- **예제 코드**: examples/
- **비디오**: YouTube 채널
- **블로그**: Medium/Dev.to

## Q&A 가이드

### 자주 묻는 질문

**Q1: 온프레미스 배포가 가능한가요?**
A: 네, Docker 또는 Kubernetes를 통해 온프레미스 배포가 가능합니다.

**Q2: 어떤 LLM을 지원하나요?**
A: OpenAI, Claude, Gemini, Groq, Ollama 등 주요 LLM을 모두 지원합니다.

**Q3: 프로덕션 환경에서 사용 가능한가요?**
A: 네, 엔터프라이즈급 보안, 모니터링, 확장성을 갖추고 있습니다.

**Q4: 커스텀 블록을 만들 수 있나요?**
A: 네, 플러그인 시스템을 통해 커스텀 블록을 개발할 수 있습니다.

**Q5: 비용은 어떻게 되나요?**
A: 오픈소스이며 MIT 라이선스로 무료입니다. LLM API 비용만 발생합니다.

## 연락처

**기술 지원**: support@agenticbuilder.com  
**영업 문의**: sales@agenticbuilder.com  
**보안 이슈**: security@agenticbuilder.com

---

**세미나 버전**: 1.0  
**최종 업데이트**: 2026-01-20  
**발표자**: AgenticBuilder Team
