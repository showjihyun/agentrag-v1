# 🤖 Agentic RAG System with Agent Builder

**차세대 AI 문서 검색 & 질의응답 시스템 + 노코드 AI 워크플로우 빌더**

Multi-Agent RAG | Visual Workflow Builder | 50+ Integrations | Real-time Streaming

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

---

## Spectacculartive RAG
<img width="2016" height="1266" alt="image" src="https://github.com/user-attachments/assets/e820bf80-4f84-45cb-bbb8-471d6556d879" />

## Agent  Builder
<img width="2016" height="1266" alt="image" src="https://github.com/user-attachments/assets/23c7ce2c-decf-445a-89b6-2f5e8b2bc550" />

## ✨ 주요 기능

### 🎨 Agent Builder - 노코드 AI 워크플로우 빌더

**sim.ai, n8n, Zapier 스타일의 비주얼 워크플로우 빌더**로 복잡한 AI 자동화를 드래그 앤 드롭으로 구성하세요.

#### 🧩 노드 타입 (70+ 노드)

**Control Nodes** (제어 흐름):
- Start, End, Condition (조건 분기)
- Loop (반복), Parallel (병렬 실행)
- Delay (지연), Merge (병합)
- Switch (다중 분기)

**Trigger Nodes** (워크플로우 시작점):
- Manual Trigger (수동 실행)
- Schedule Trigger (크론 스케줄)
- Webhook Trigger (HTTP 웹훅)
- Email Trigger (이메일 수신)
- Event Trigger (시스템 이벤트)
- Database Trigger (DB 변경 감지)

**Agent Nodes** (AI 에이전트):
- Custom Agents (사용자 정의 에이전트)
- Template-based Agents (템플릿 기반)
- Multi-agent Collaboration (다중 에이전트 협업)
- Manager Agent (에이전트 관리자)
- Consensus Agent (합의 에이전트)

**Integration Nodes** (50+ 통합):
- **Communication**: Slack, Discord, Email, SMS
- **Storage**: Google Drive, S3, Dropbox, OneDrive
- **Database**: PostgreSQL, MySQL, MongoDB, Redis
- **APIs**: HTTP Request, GraphQL, REST API
- **AI/ML**: OpenAI, Anthropic, Hugging Face
- **Productivity**: Notion, Airtable, Google Sheets
- **And more...**

**Logic Nodes**:
- Code Execution (Python, JavaScript)
- Data Transformation
- Condition Evaluation
- Memory Operations (STM/LTM)
- Human Approval (인간 승인)

#### 🚀 주요 기능

✅ **드래그 앤 드롭 인터페이스** - 직관적인 비주얼 에디터
✅ **실시간 실행 모니터링** - 각 노드의 실행 상태 추적
✅ **조건 분기 & 반복** - 복잡한 로직 구현
✅ **에러 핸들링 & 재시도** - 자동 재시도 및 폴백
✅ **변수 & 표현식** - 동적 데이터 처리 (`{{$json.field}}`)
✅ **템플릿 라이브러리** - 사전 구성된 워크플로우
✅ **AI 워크플로우 생성기** - 자연어로 워크플로우 생성
✅ **버전 관리** - 워크플로우 버전 추적
✅ **실행 히스토리** - 모든 실행 기록 저장
✅ **API 키 관리** - 안전한 자격 증명 관리

#### 📊 Agent Builder 메뉴

```
Agent Builder
├── 🏠 Dashboard        (대시보드 & 분석)
├── 🤖 Agents          (AI 에이전트 관리)
├── 🧩 Blocks          (재사용 가능한 블록)
├── 🔧 Tools           (통합 도구 관리)
├── ⚡ Triggers        (트리거 관리)
├── 🔄 Workflows       (워크플로우 구성)
├── 📚 Knowledgebases  (지식 베이스)
├── 📝 Variables       (환경 변수)
├── 🔐 API Keys        (API 키 관리)
├── ✅ Approvals       (승인 대기 목록)
├── 📊 Analytics       (분석 & 인사이트)
└── ⚙️ Settings        (설정)
    ├── LLM Settings   (LLM 제공자 설정)
    └── Environment    (환경 변수)
```

#### 🎯 워크플로우 예시

**1. 자동 고객 지원 봇**
```
Webhook Trigger (고객 문의)
  → Agent (의도 분석)
  → Condition (문의 유형)
    ├─ FAQ → Agent (FAQ 검색) → Slack (답변 전송)
    ├─ 기술 지원 → Agent (티켓 생성) → Email (알림)
    └─ 기타 → Human Approval → Agent (답변 생성)
```

**2. 일일 리포트 자동화**
```
Schedule Trigger (매일 9시)
  → Database (데이터 수집)
  → Agent (데이터 분석)
  → Agent (리포트 생성)
  → Parallel
    ├─ Email (리포트 발송)
    ├─ Slack (알림)
    └─ Google Drive (저장)
```

**3. 소셜 미디어 모니터링**
```
Schedule Trigger (1시간마다)
  → HTTP Request (소셜 미디어 API)
  → Loop (각 게시물)
    → Agent (감정 분석)
    → Condition (부정적 감정?)
      └─ True → Discord (알림) → Human Approval
```

---

### 🤖 Multi-Agent RAG System

**Agentic RAG**는 전통적인 RAG를 넘어 다중 에이전트 협업으로 더 정확하고 맥락을 이해하는 답변을 제공합니다.

#### 에이전트 아키텍처

**Aggregator Agent** (마스터 코디네이터):
- ReAct (Reasoning + Acting) 패턴
- Chain of Thought (CoT) 추론
- 다중 에이전트 오케스트레이션

**Specialized Agents**:
- **Vector Search Agent**: Milvus 기반 의미론적 검색
- **Local Data Agent**: 파일 시스템 & 데이터베이스
- **Web Search Agent**: 실시간 웹 검색 (DuckDuckGo)

#### 🎯 Adaptive Query Routing

쿼리 복잡도를 자동 분석하여 최적의 처리 방식 선택:

| Mode | Response Time | Use Case |
|------|---------------|----------|
| **Fast** | < 1초 | 간단한 사실 확인 |
| **Balanced** | < 3초 | 일반적인 질문 |
| **Deep** | < 10초 | 복잡한 분석 & 추론 |

#### 📄 Multimodal Document Processing

**지원 포맷**: PDF, DOCX, HWP, HWPX, PPT, PPTX, XLSX, TXT, MD, 이미지

**PaddleOCR Advanced 기술**:
- **PP-OCRv5**: 98%+ 텍스트 인식 정확도
- **PP-StructureV3**: 98%+ 표 구조 인식
- **PaddleOCR-VL**: 멀티모달 문서 이해
- **PP-ChatOCRv4**: 문서 기반 대화형 AI
- **PP-DocTranslation**: 레이아웃 보존 문서 번역

#### 🔍 Hybrid Search

**Vector Search** (의미론적) + **BM25** (키워드) 결합:
- 한국어 최적화 (jhgan/ko-sroberta-multitask)
- Adaptive Reranking
- L1/L2 캐싱 전략

---

## 🚀 Quick Start

### Prerequisites
```bash
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
```

### 1. Clone & Setup
```bash
git clone https://github.com/showjihyun/agentrag-v1.git
cd agentrag-v1
cp .env.example .env
```

### 2. Configure Environment
`.env` 파일을 편집하여 필요한 설정을 구성하세요:

```env
# LLM Provider (ollama, openai, claude)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1

# Database
DATABASE_URL=postgresql://raguser:ragpassword@localhost:5433/agentic_rag
MILVUS_HOST=localhost
REDIS_HOST=localhost

# Features
ENABLE_HYBRID_SEARCH=true
ADAPTIVE_ROUTING_ENABLED=true
```

### 3. Start with Docker
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access Services

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Frontend** | http://localhost:3000 | 메인 웹 인터페이스 |
| 🤖 **Agent Builder** | http://localhost:3000/agent-builder | 워크플로우 빌더 |
| 🚀 **Backend API** | http://localhost:8000 | REST API |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger UI |
| 🗄️ **PostgreSQL** | localhost:5433 | 데이터베이스 |
| 🔍 **Milvus** | localhost:19530 | 벡터 DB |
| 💾 **Redis** | localhost:6380 | 캐시 |

### 5. Create Your First Workflow

1. **Agent Builder 접속**: http://localhost:3000/agent-builder
2. **Workflows 메뉴** 클릭
3. **"New Workflow"** 버튼 클릭
4. **노드 추가**:
   - Start 노드 추가
   - Agent 노드 추가 (드래그 앤 드롭)
   - End 노드 추가
5. **노드 연결**: 노드 간 연결선 그리기
6. **설정**: 각 노드 클릭하여 설정
7. **저장 & 실행**: "Save" → "Execute"

---

## 🏗️ Architecture

### System Overview
```
┌─────────────────────────────────────────────────────────┐
│                  Frontend (Next.js 15)                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Chat UI    │  │Agent Builder │  │  Dashboard   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────┬────────────────────────────────┘
                         │ SSE/REST API
┌────────────────────────┴────────────────────────────────┐
│              Backend API (FastAPI)                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Intelligent Query Router                 │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │    Aggregator Agent (ReAct + CoT)                │  │
│  │  ├─ Vector Search Agent                          │  │
│  │  ├─ Local Data Agent                             │  │
│  │  └─ Web Search Agent                             │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │    Workflow Executor                             │  │
│  │  ├─ Node Execution Engine                        │  │
│  │  ├─ Trigger Manager                              │  │
│  │  └─ Integration Services                         │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │    Document Processing Pipeline                  │  │
│  │  └─ PaddleOCR Processor                          │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│              Data & Storage Layer                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │PostgreSQL│  │  Milvus  │  │  Redis   │  │  LLM   │ │
│  │(Metadata)│  │ (Vectors)│  │ (Cache)  │  │Provider│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Tech Stack

**Backend**:
- **Framework**: FastAPI (Python 3.10+)
- **AI/ML**: LangChain, LangGraph, LiteLLM
- **OCR**: PaddleOCR Advanced (PP-OCRv5, PP-StructureV3)
- **Databases**: PostgreSQL, Milvus, Redis
- **Embeddings**: jhgan/ko-sroberta-multitask (Korean)

**Frontend**:
- **Framework**: Next.js 15 (App Router)
- **UI**: React 19, Tailwind CSS, Shadcn/ui
- **Workflow**: ReactFlow (visual editor)
- **State**: Zustand, TanStack Query

**Infrastructure**:
- **Containerization**: Docker, Docker Compose
- **LLM Runtime**: Ollama (optional, for local models)

---

## 📊 Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Fast Mode Response | < 1초 | ✅ 0.8초 |
| Balanced Mode | < 3초 | ✅ 2.5초 |
| Deep Mode | < 10초 | ✅ 8초 |
| Cache Hit Rate | 60%+ | ✅ 65% |
| OCR Accuracy | 95%+ | ✅ 98% |
| Table Recognition | 95%+ | ✅ 98% |
| Workflow Execution | < 5초 | ✅ 3초 |

---

## 🛠️ Configuration

### Environment Variables

**LLM Configuration**:
```env
LLM_PROVIDER=ollama              # ollama, openai, claude
LLM_MODEL=llama3.1              # Model name
OPENAI_API_KEY=sk-...           # OpenAI API key (if using)
ANTHROPIC_API_KEY=sk-ant-...    # Anthropic API key (if using)
```

**Database Configuration**:
```env
DATABASE_URL=postgresql://raguser:ragpassword@localhost:5433/agentic_rag
MILVUS_HOST=localhost
MILVUS_PORT=19530
REDIS_HOST=localhost
REDIS_PORT=6380
```

**Feature Flags**:
```env
ENABLE_HYBRID_SEARCH=true
ENABLE_ADAPTIVE_RERANKING=true
ADAPTIVE_ROUTING_ENABLED=true
DEFAULT_QUERY_MODE=balanced     # fast, balanced, deep
```

**Agent Builder**:
```env
ENABLE_WORKFLOW_GENERATOR=true
MAX_WORKFLOW_NODES=100
WORKFLOW_EXECUTION_TIMEOUT=300
```

---

## 📚 Documentation

### Getting Started
- [Quick Start Guide](docs/QUICK_START_GUIDE.md)
- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Guide](docs/CONFIGURATION.md)

### Agent Builder
- [Workflow Builder Guide](docs/WORKFLOW_BUILDER_GUIDE.md)
- [Triggers Guide](docs/TRIGGERS_GUIDE.md)
- [Custom Tools Guide](docs/CUSTOM_TOOLS_GUIDE.md)
- [Integration Guide](docs/INTEGRATION_GUIDE.md)

### RAG System
- [RAG Architecture](docs/RAG_ARCHITECTURE.md)
- [Document Processing](docs/DOCUMENT_PROCESSING.md)
- [Query Routing](docs/QUERY_ROUTING.md)

### API Reference
- [REST API Documentation](docs/API_REFERENCE.md)
- [Webhook API](docs/WEBHOOK_API.md)
- [Python SDK](docs/PYTHON_SDK.md)

### Project Information
- [Product Overview](.kiro/steering/product.md)
- [Tech Stack](.kiro/steering/tech.md)
- [Project Structure](.kiro/steering/structure.md)

---

## 🧪 Testing

### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_workflow_executor.py

# Run integration tests
pytest tests/integration/
```

### Frontend Tests
```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests
npm run e2e

# Run E2E tests with UI
npm run e2e:ui
```

---

## 🤝 Contributing

We welcome contributions! 🎉

### How to Contribute

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Code Style

**Python**:
- Follow PEP 8
- Use type hints
- 120 character line length
- Run `black .` and `isort .` before committing

**TypeScript**:
- Use ESLint configuration
- Functional components with hooks
- 100 character line length

---

## 🗺️ Roadmap

### ✅ v1.0 (Completed)
- ✅ Multi-agent RAG architecture
- ✅ Adaptive query routing
- ✅ Multimodal document processing
- ✅ Visual workflow builder (70+ nodes)
- ✅ Trigger system (6 types)
- ✅ 50+ integrations
- ✅ Web search integration
- ✅ AI workflow generator
- ✅ API key management
- ✅ Human approval system
- ✅ Memory management (STM/LTM)

### 🚧 v1.1 (In Progress)
- 🔄 GraphRAG integration
- 🔄 Advanced analytics dashboard
- 🔄 Workflow marketplace
- 🔄 Mobile app (React Native)
- 🔄 Voice input/output
- 🔄 Real-time collaboration

### 🔮 v2.0 (Planned)
- 📋 Multi-tenant support
- 📋 Custom agent builder UI
- 📋 Plugin system
- 📋 Edge deployment
- 📋 Kubernetes support
- 📋 Advanced monitoring & alerting

---

## 🏆 Use Cases

### 1. Customer Support Automation
자동으로 고객 문의를 분석하고 답변하는 AI 봇을 구축하세요.

### 2. Document Intelligence
대량의 문서를 자동으로 처리하고 인사이트를 추출하세요.

### 3. Data Pipeline Automation
복잡한 데이터 파이프라인을 시각적으로 구성하고 자동화하세요.

### 4. Content Generation
AI를 활용한 자동 콘텐츠 생성 워크플로우를 만드세요.

### 5. Business Process Automation
반복적인 비즈니스 프로세스를 AI로 자동화하세요.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💬 Support & Community

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Issue Tracker**: [GitHub Issues](https://github.com/showjihyun/agentrag-v1/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/showjihyun/agentrag-v1/discussions)
- 📧 **Email**: showjihyun@gmail.com

---

## 🙏 Acknowledgments

Special thanks to:
- **LangChain** team for the amazing agent framework
- **PaddleOCR** team for the powerful OCR engine
- **Milvus** team for the vector database
- **FastAPI** and **Next.js** communities
- All contributors and users of this project

---

<div align="center">

**Made with ❤️ by the Agentic RAG Team**

⭐ **Star us on GitHub** — it helps us grow and improve!

[⬆ Back to Top](#-agentic-rag-system-with-agent-builder)

</div>
