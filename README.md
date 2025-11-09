# 🤖 Agentic RAG System

**차세대 AI 문서 검색 & 질의응답 시스템**

멀티 에이전트 아키텍처 | 멀티모달 RAG | 실시간 스트리밍 | Workflow Builder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)

---

## ✨ 주요 기능

### 🤖 Multi-Agent Architecture
- **Aggregator Agent**: ReAct + Chain of Thought 기반 마스터 코디네이터
- **Vector Search Agent**: Milvus 기반 의미론적 검색
- **Local Data Agent**: 파일 시스템 & 데이터베이스 접근
- **Web Search Agent**: 실시간 웹 검색 (DuckDuckGo)

### 🎨 Adaptive Query Routing
쿼리 복잡도를 자동 분석하여 최적의 처리 방식 선택:
- **Fast Mode**: < 1초 (간단한 질문)
- **Balanced Mode**: < 3초 (일반 질문)
- **Deep Mode**: < 10초 (복잡한 분석)

### 📄 Multimodal Document Processing
**지원 포맷**: PDF, DOCX, HWP, HWPX, PPT, PPTX, XLSX, TXT, MD, 이미지

**고급 문서 처리** (PaddleOCR Advanced):
- PP-OCRv5: 98%+ 텍스트 인식
- PP-StructureV3: 98%+ 표 인식
- PaddleOCR-VL: 멀티모달 문서 이해
- PP-ChatOCRv4: 문서 기반 대화형 AI
- PP-DocTranslation: 레이아웃 보존 문서 번역

### 🔧 Workflow Builder (sim.ai 스타일)
시각적 워크플로우 빌더로 복잡한 AI 워크플로우 구성:

**노드 타입**:
- **Control**: Start, End, Condition (조건 분기)
- **Triggers**: Manual, Schedule, Webhook, Email, Event, Database
- **Agents**: AI 에이전트 (4개)
- **Blocks**: 재사용 가능한 블록 (5개)
- **Tools**: 통합 도구 (53개)

**기능**:
- ✅ 드래그 앤 드롭 인터페이스
- ✅ 실시간 노드 설정
- ✅ 조건 분기 지원
- ✅ Trigger 기반 자동 실행
- ✅ 복잡한 워크플로우 구성

### 🌐 Multi-LLM Support
- **Local**: Ollama (Llama 3.1, Mistral 등)
- **Cloud**: OpenAI (GPT-4), Anthropic (Claude 3)
- **Features**: 자동 폴백, 로드 밸런싱, 비용 최적화

### 🔍 Web Search Integration
- DuckDuckGo 기반 무료 웹 검색
- 다국어 지원 (한국어, 영어 등)
- 쿼리 향상 및 관련성 필터링

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

### 2. Start with Docker
```bash
docker-compose up -d
```

### 3. Access Services
- 🌐 **Frontend**: http://localhost:3000
- 🚀 **Backend API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🤖 **Agent Builder**: http://localhost:3000/agent-builder
- ⚡ **Triggers**: http://localhost:3000/agent-builder/triggers
- 🔄 **Workflows**: http://localhost:3000/agent-builder/workflows

---

## 📚 Documentation

### 🎓 Getting Started
- [Quick Start Guide](docs/QUICK_START_GUIDE.md)
- [Product Overview](.kiro/steering/product.md)
- [Tech Stack](.kiro/steering/tech.md)
- [Project Structure](.kiro/steering/structure.md)

### 🔧 Features
- [Workflow Builder Guide](docs/WORKFLOW_BUILDER_GUIDE.md)
- [Triggers Guide](docs/TRIGGERS_GUIDE.md)
- [Custom Tools Guide](docs/CUSTOM_TOOLS_GUIDE.md)
- [Features Overview](docs/FEATURES.md)
- [Comparison](docs/COMPARISON.md)

---

## 🏗️ Architecture

### System Overview
```
Frontend (Next.js 15)
    ↕ SSE/REST API
Backend API (FastAPI)
    ├─ Intelligent Query Router
    ├─ Aggregator Agent (ReAct + CoT)
    │   ├─ Vector Search Agent
    │   ├─ Local Data Agent
    │   └─ Web Search Agent
    └─ Document Processing Pipeline
        └─ PaddleOCR Processor
    ↓
Data & Storage Layer
    ├─ PostgreSQL (Metadata)
    ├─ Milvus (Vectors)
    ├─ Redis (Cache)
    └─ LLM (Ollama/OpenAI/Claude)
```

### Tech Stack

**Backend**:
- FastAPI (Python 3.10+)
- LangChain/LangGraph (Agent orchestration)
- PaddleOCR Advanced (Document processing)
- PostgreSQL, Milvus, Redis

**Frontend**:
- Next.js 15 (App Router)
- React 19
- Tailwind CSS
- Shadcn/ui

---

## 🎨 Agent Builder

### Menu Structure
```
Agent Builder
├── Agents          (AI 에이전트 관리)
├── Blocks          (재사용 가능한 블록)
├── Triggers        (워크플로우 시작점)
├── Workflows       (워크플로우 구성)
├── Knowledgebases  (지식 베이스)
├── Variables       (변수 관리)
└── Executions      (실행 기록)
```

### Workflow Example
```
Schedule Trigger (매일 9시)
  → Agent (데이터 수집)
  → Tool (Web Search)
  → Agent (분석)
  → Condition (품질 체크)
    ├─ True → Agent (리포트 생성) → End
    └─ False → Agent (재처리) → End
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| Fast Mode | < 1초 |
| Balanced Mode | < 3초 |
| Deep Mode | < 10초 |
| Cache Hit Rate | 60%+ |
| OCR Accuracy | 98%+ |
| Table Recognition | 98%+ |

---

## 🛠️ Configuration

### Key Environment Variables
```env
# LLM
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1

# Database
DATABASE_URL=postgresql://raguser:ragpassword@localhost:5433/agentic_rag
MILVUS_HOST=localhost
REDIS_HOST=localhost

# Features
ENABLE_HYBRID_SEARCH=true
ENABLE_ADAPTIVE_RERANKING=true
ADAPTIVE_ROUTING_ENABLED=true
```

---

## 🧪 Testing

```bash
# Backend
cd backend
pytest --cov=backend

# Frontend
cd frontend
npm test
npm run e2e
```

---

## 🤝 Contributing

We welcome contributions! 🎉

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## 🗺️ Roadmap

### ✅ v1.0 (Completed)
- Multi-agent architecture
- Adaptive query routing
- Multimodal document processing
- Workflow Builder (sim.ai style)
- Triggers system
- Web search integration

### 🚧 v1.1 (In Progress)
- GraphRAG integration
- Advanced analytics
- Mobile app
- Voice input/output

### 🔮 v2.0 (Future)
- Multi-tenant support
- Custom agent builder UI
- Plugin system
- Edge deployment

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 💬 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/showjihyun/agentrag-v1/issues)
- 📧 Email: showjihyun@gmail.com

---

<div align="center">

**Made with ❤️ by the Agentic RAG Team**

⭐ **Star us on GitHub** — it motivates us to keep improving!

</div>
