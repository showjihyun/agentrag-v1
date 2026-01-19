# Product Overview

AgenticBuilder is a visual AI workflow builder platform that enables developers to create sophisticated multi-agent AI systems through a drag-and-drop interface.

## Core Concept

Think "Zapier for AI Agents" - a visual workflow builder with enterprise-grade capabilities for orchestrating multiple AI agents, integrations, and data sources.

## Key Features

- **Visual Workflow Builder**: ReactFlow-based drag-and-drop editor with 50+ pre-built blocks
- **Multi-Agent Orchestration**: 17+ orchestration patterns (sequential, parallel, hierarchical, consensus, swarm intelligence, etc.)
- **Real-time Execution**: Live workflow monitoring with Server-Sent Events
- **50+ Integrations**: Communication (Slack, Discord), databases (PostgreSQL, MongoDB, Milvus), cloud services (AWS, GCP, Azure), AI services (OpenAI, Anthropic, Google AI)
- **Enterprise RAG**: Vector search (Milvus), hybrid search (BM25), knowledge graphs
- **Multi-LLM Support**: OpenAI, Claude, Gemini, Grok, Ollama with intelligent routing

## Architecture Philosophy

- **Frontend-First**: Next.js 15 + React 19 with TypeScript for the visual builder
- **API-Driven**: FastAPI backend with async/await for high performance
- **Agent-Centric**: LangChain/LangGraph for AI agent orchestration
- **Production-Ready**: Docker-based deployment, monitoring, security, and scaling built-in

## Target Use Cases

- Business automation (customer support, content creation, data processing)
- Research & development (literature review, experiment design, data analysis)
- Creative industries (content production, design automation, media processing)
- Enterprise workflows (multi-step AI-powered processes)

## Platform Focus

This is a **workflow-focused platform**, not a traditional RAG system. While RAG capabilities exist, the primary focus is on building and executing visual AI agent workflows.
