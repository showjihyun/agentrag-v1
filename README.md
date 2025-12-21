# 🤖 Workflow Platform - Visual AI Agent Builder

**Enterprise-Grade No-Code AI Workflow Platform with 70+ Integrations**

Build sophisticated AI automations with drag-and-drop simplicity. From simple task automation to complex multi-agent workflows - no coding required.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen.svg)](#-production-ready)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

---

## 🎯 What is Workflow Platform?

A comprehensive **no-code AI workflow builder** that empowers users to create sophisticated AI automations without programming knowledge. Think of it as **n8n + Zapier + Make** but specifically designed for AI workflows with advanced multi-agent orchestration.

### 🌟 Key Highlights

- 🎨 **Visual Workflow Designer** - Drag-and-drop interface for building AI workflows
- 🤖 **Multi-Agent Orchestration** - Coordinate multiple AI agents within workflows  
- 🔧 **70+ Pre-built Nodes** - Extensive library of tools, triggers, and integrations
- ⚡ **Real-time Execution** - Live monitoring with Server-Sent Events (SSE)
- 🧠 **AI-Powered** - Support for GPT-4, Claude, Gemini, Grok, and local models
- 🔗 **50+ Integrations** - Connect with popular services and APIs
- 📊 **Advanced Analytics** - Detailed execution metrics and performance insights
- 🔐 **Enterprise Security** - Secure API key management and access controls

---

## 🚀 Quick Demo

### Visual Workflow Builder
![Workflow Builder Demo](https://github.com/user-attachments/assets/23c7ce2c-decf-445a-89b6-2f5e8b2bc550)

### Example: Automated Customer Support Workflow
```mermaid
graph LR
    A[Webhook Trigger] --> B[AI Agent: Intent Analysis]
    B --> C{Intent Type?}
    C -->|FAQ| D[AI Agent: FAQ Search]
    C -->|Technical| E[AI Agent: Create Ticket]
    C -->|Other| F[Human Approval]
    D --> G[Slack: Send Response]
    E --> H[Email: Notify Team]
    F --> I[AI Agent: Generate Response]
```

---

## ✨ Key Features

### 🎨 Visual Workflow Builder

**No-code AI workflow platform inspired by n8n, Zapier, and Make** - Build complex AI automations with drag-and-drop simplicity.

#### 🧩 Node Types (70+ Nodes)

**Control Nodes** (Flow Control):
- Start, End, Condition (Branching)
- Loop (Iteration), Parallel (Concurrent Execution)
- Delay (Wait), Merge (Combine)
- Switch (Multi-branch)

**Trigger Nodes** (Workflow Initiators):
- Manual Trigger (On-demand execution)
- Schedule Trigger (Cron scheduling)
- Webhook Trigger (HTTP webhooks)
- Email Trigger (Email reception)
- Event Trigger (System events)
- Database Trigger (DB change detection)

**Agent Nodes** (AI Agents):
- Custom Agents (User-defined agents)
- Template-based Agents
- Multi-agent Collaboration
- Manager Agent (Agent coordinator)
- Consensus Agent (Agreement-based)

**Integration Nodes** (50+ Integrations):
- **Communication**: Slack, Discord, Email, SMS
- **Storage**: Google Drive, S3, Dropbox, OneDrive
- **Database**: PostgreSQL, MySQL, MongoDB, Redis
- **APIs**: HTTP Request, GraphQL, REST API
- **AI/ML**: OpenAI, Anthropic, Hugging Face, Gemini, Grok
- **Productivity**: Notion, Airtable, Google Sheets
- **And more...**

**Logic Nodes**:
- Code Execution (Python, JavaScript)
- Data Transformation
- Condition Evaluation
- Memory Operations (STM/LTM)
- Human Approval (Human-in-the-loop)

#### 🚀 Core Capabilities

✅ **Drag-and-Drop Interface** - Intuitive visual editor
✅ **Real-time Execution Monitoring** - Track each node's execution status
✅ **Conditional Branching & Loops** - Implement complex logic
✅ **Error Handling & Retry** - Automatic retry and fallback
✅ **Variables & Expressions** - Dynamic data processing (`{{$json.field}}`)
✅ **Template Library** - Pre-configured workflows
✅ **AI Workflow Generator** - Create workflows from natural language
✅ **Version Control** - Track workflow versions
✅ **Execution History** - Store all execution records
✅ **API Key Management** - Secure credential management

#### 📊 Agent Builder Menu

```
Agent Builder
├── 🏠 Dashboard        (Overview & Analytics)
├── 🤖 Agents          (AI Agent Management)
├── 🧩 Blocks          (Reusable Components)
├── 🔧 Tools           (Integration Tools)
├── ⚡ Triggers        (Trigger Management)
├── 🔄 Workflows       (Workflow Configuration)
├── 📚 Knowledgebases  (Knowledge Bases)
├── 📝 Variables       (Environment Variables)
├── 🔐 API Keys        (API Key Management)
├── ✅ Approvals       (Pending Approvals)
├── 📊 Analytics       (Insights & Metrics)
└── ⚙️ Settings        (Configuration)
    ├── LLM Settings   (LLM Provider Setup)
    └── Environment    (Environment Variables)
```

#### 🎯 Workflow Examples

**1. Automated Customer Support Bot**
```
Webhook Trigger (Customer Inquiry)
  → Agent (Intent Analysis)
  → Condition (Inquiry Type)
    ├─ FAQ → Agent (FAQ Search) → Slack (Send Response)
    ├─ Technical Support → Agent (Create Ticket) → Email (Notify)
    └─ Other → Human Approval → Agent (Generate Response)
```

**2. Daily Report Automation**
```
Schedule Trigger (Daily at 9 AM)
  → Database (Collect Data)
  → Agent (Analyze Data)
  → Agent (Generate Report)
  → Parallel
    ├─ Email (Send Report)
    ├─ Slack (Notify)
    └─ Google Drive (Save)
```

**3. Social Media Monitoring**
```
Schedule Trigger (Every Hour)
  → HTTP Request (Social Media API)
  → Loop (Each Post)
    → Agent (Sentiment Analysis)
    → Condition (Negative Sentiment?)
      └─ True → Discord (Alert) → Human Approval
```

### 🚀 Advanced Workflow Features

#### 🎯 Smart Execution Engine
- **Conditional Branching**: Dynamic workflow paths based on data
- **Loop Processing**: Iterate over datasets and API responses
- **Parallel Execution**: Run multiple tasks simultaneously
- **Error Handling**: Automatic retry and fallback mechanisms

#### 📊 Real-time Monitoring
- **Live Execution Tracking**: Watch your workflows run in real-time
- **Performance Analytics**: Detailed metrics and insights
- **Debug Mode**: Step-by-step execution debugging
- **Cost Tracking**: Monitor API usage and costs

#### 🔗 Extensive Integrations
**Communication**: Slack, Discord, Email, SMS, Teams
**Storage**: Google Drive, S3, Dropbox, OneDrive, Box
**Database**: PostgreSQL, MySQL, MongoDB, Redis, Supabase
**AI/ML**: OpenAI, Anthropic, Google AI, Hugging Face, Ollama
**Productivity**: Notion, Airtable, Google Sheets, Trello

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
Edit the `.env` file to configure necessary settings:

```env
# LLM Provider (ollama, openai, claude, gemini, grok)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.3:70b

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
| 🌐 **Frontend** | http://localhost:3000 | Workflow Platform (redirects to Agent Builder) |
| 🤖 **Agent Builder** | http://localhost:3000/agent-builder | Main workflow builder interface |
| 🚀 **Backend API** | http://localhost:8000 | REST API |
| 📚 **API Docs** | http://localhost:8000/docs | Swagger UI |
| 🗄️ **PostgreSQL** | localhost:5433 | Database |
| 🔍 **Milvus** | localhost:19530 | Vector DB (for workflow tools) |
| 💾 **Redis** | localhost:6380 | Cache |

### 5. Create Your First Workflow

1. **Access Platform**: http://localhost:3000 (automatically redirects to Agent Builder)
2. **Choose Workflow Type**:
   - **Agentflow**: Multi-agent task automation
   - **Chatflow**: Conversational AI workflows
3. **Build Your Workflow**:
   - Drag & drop nodes from the sidebar
   - Connect nodes to create your flow
   - Configure each node's settings
4. **Test & Deploy**: Use the built-in testing tools and deploy when ready

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
- **Embeddings**: jhgan/ko-sroberta-multitask (Korean-optimized)

**Frontend**:
- **Framework**: Next.js 15 (App Router)
- **UI**: React 19, Tailwind CSS 4, Shadcn/ui
- **Workflow**: ReactFlow (visual editor)
- **State**: Zustand, TanStack Query

**Infrastructure**:
- **Containerization**: Docker, Docker Compose
- **LLM Runtime**: Ollama (optional, for local models)

---

## 📊 Performance Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Fast Mode Response | < 1s | ✅ 0.8s |
| Balanced Mode | < 3s | ✅ 2.5s |
| Deep Mode | < 10s | ✅ 8s |
| Cache Hit Rate | 60%+ | ✅ 65% |
| OCR Accuracy | 95%+ | ✅ 98% |
| Table Recognition | 95%+ | ✅ 98% |
| Workflow Execution | < 5s | ✅ 3s |

---

## 🛠️ Configuration

### Environment Variables

**LLM Configuration**:
```env
LLM_PROVIDER=ollama              # ollama, openai, claude, gemini, grok
LLM_MODEL=llama3.3:70b          # Model name
OPENAI_API_KEY=sk-...           # OpenAI API key (if using)
ANTHROPIC_API_KEY=sk-ant-...    # Anthropic API key (if using)
GOOGLE_API_KEY=...              # Google Gemini API key (if using)
XAI_API_KEY=...                 # xAI Grok API key (if using)
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
- ✅ Support for latest LLMs (GPT-5, o3, Claude 4.5, Gemini 2.0, Grok 3)

### 🚧 v1.1 (In Progress)
- 🔄 GraphRAG integration
- 🔄 Advanced analytics dashboard
- 🔄 Workflow marketplace
- 🔄 Mobile app (React Native)
- � Voic.e input/output
- � Reatl-time collaboration

### � v2.n0 (Planned)
- 📋 Multi-tenant support
- 📋 Custom agent builder UI
- 📋 Plugin system
- 📋 Edge deployment
- 📋 Kubernetes support
- 📋 Advanced monitoring & alerting

---

## 🏆 Use Cases

### 1. Customer Support Automation
Build AI bots that automatically analyze and respond to customer inquiries.

### 2. Document Intelligence
Automatically process large volumes of documents and extract insights.

### 3. Data Pipeline Automation
Visually configure and automate complex data pipelines.

### 4. Content Generation
Create automated content generation workflows powered by AI.

### 5. Business Process Automation
Automate repetitive business processes with AI.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## � Supsport & Community

- � ***Documentation**: [docs/](docs/)
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
