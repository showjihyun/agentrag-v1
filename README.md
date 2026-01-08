<div align="center">

# 🧪 AgenticFlow

### Experimental Visual AI Workflow Builder

**An open-source experiment in building AI automations visually.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![Experimental](https://img.shields.io/badge/Status-Experimental-orange.svg)](#)

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Contributing](#-contributing)

</div>

---

## 🎯 What is this?

AgenticFlow is an **experimental project** exploring how to build AI workflows visually. Think n8n meets AI agents - drag, drop, connect, and run.

> ⚠️ **Experimental**: This is a learning/exploration project. Not production-ready, but functional and fun to play with!

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **Visual Builder** | Drag-and-drop workflow editor with ReactFlow |
| 🤖 **Multi-Agent** | Orchestrate multiple AI agents (ReAct + CoT) |
| 🔗 **50+ Integrations** | Slack, Email, HTTP, Databases, and more |
| ⚡ **Real-time** | Live execution monitoring via SSE |
| 🧠 **Multi-LLM** | OpenAI, Claude, Gemini, Grok, Ollama |
| 📊 **RAG Tools** | Vector search, hybrid search, document processing |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────┐
│           Frontend (Next.js 15 + React 19)       │
│              ReactFlow Visual Editor             │
└─────────────────────┬────────────────────────────┘
                      │ REST / SSE
┌─────────────────────┴────────────────────────────┐
│              Backend (FastAPI)                   │
│  ┌─────────────────┬─────────────────────────┐  │
│  │ Workflow Engine │   Multi-Agent System    │  │
│  │ • Node Executor │   • Aggregator (ReAct)  │  │
│  │ • Triggers      │   • Vector Search Agent │  │
│  │ • Integrations  │   • Web Search Agent    │  │
│  └─────────────────┴─────────────────────────┘  │
└─────────────────────┬────────────────────────────┘
                      │
┌─────────────────────┴────────────────────────────┐
│  PostgreSQL  │  Milvus  │  Redis  │  LLM APIs   │
└──────────────────────────────────────────────────┘
```

**Tech Stack:**
- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind, ReactFlow
- **Backend**: FastAPI, LangChain, LangGraph, LiteLLM
- **Storage**: PostgreSQL, Milvus (vectors), Redis (cache)
- **AI**: Multi-LLM support via LiteLLM

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/yourusername/agenticflow.git
cd agenticflow

# Configure
cp .env.example .env
# Edit .env with your LLM API keys

# Run
docker-compose up -d

# Access
open http://localhost:3000
```

**Default ports:**
- Frontend: `3000`
- Backend API: `8000`
- API Docs: `8000/docs`

---

## 📸 Screenshots

| Workflow Builder | Execution Monitor |
|-----------------|-------------------|
| ![Builder](docs/images/builder.png) | ![Monitor](docs/images/monitor.png) |

---

## 🛠 Development

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

---

## 🤝 Contributing

This is an experimental project - contributions, ideas, and feedback are welcome!

1. Fork it
2. Create your branch (`git checkout -b feature/cool-idea`)
3. Commit (`git commit -m 'Add cool idea'`)
4. Push (`git push origin feature/cool-idea`)
5. Open a PR

---

## 📝 License

MIT - do whatever you want with it.

---

<div align="center">

**⭐ If you find this interesting, a star would be appreciated!**

*Built with curiosity and too much coffee ☕*

</div>
