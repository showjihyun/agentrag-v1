# Product Overview

## Agentic RAG System

An intelligent document search and question-answering system that combines multi-agent architecture with multimodal RAG capabilities, featuring a visual Agent Builder for creating custom AI workflows.

## Core Value Proposition

Agentic RAG goes beyond traditional RAG systems by using adaptive query routing and multi-agent orchestration to deliver fast, accurate responses across diverse document types and query complexities. The Agent Builder enables users to create, customize, and deploy AI agents without coding.

## Key Features

### RAG Core
- **Multi-Agent Architecture**: Aggregator agent orchestrates specialized agents (Vector Search, Local Data, Web Search) using ReAct + Chain of Thought reasoning
- **Adaptive Query Routing**: Automatically analyzes query complexity and routes to optimal processing mode (Fast <1s, Balanced <3s, Deep <10s)
- **Multimodal Document Processing**: Supports PDF, DOCX, HWP/HWPX, PPT/PPTX, XLSX, images with advanced OCR (PaddleOCR, PP-OCRv5, PP-StructureV3)
- **Hybrid Search**: Combines vector search (semantic) with BM25 (keyword) for optimal retrieval
- **Real-time Streaming**: Server-Sent Events (SSE) for live agent reasoning and response generation
- **Multi-LLM Support**: Works with Ollama (local), OpenAI, Anthropic with automatic fallback
- **Web Search Integration**: DuckDuckGo-based search (no API key required)
- **Korean Language Optimized**: Uses jhgan/ko-sroberta-multitask embeddings and Korean-specific rerankers

### Agent Builder
- **Visual Workflow Designer**: Drag-and-drop interface for building AI workflows
- **Chatflows**: Conversational AI flows with memory and context
- **Agentflows**: Task-oriented agent workflows with tool integration
- **Block Library**: Pre-built blocks (LLM, HTTP, Code, Condition, Loop, etc.)
- **Tool Integration**: Slack, Gmail, PostgreSQL, Vector Search, and more
- **Template Marketplace**: Share and discover workflow templates
- **Execution Monitoring**: Real-time execution tracking and debugging
- **API Keys Management**: Secure API key generation for external access
- **Embed Support**: Embed chatflows in external applications

## Target Users

- Organizations needing intelligent document search across large knowledge bases
- Teams requiring multilingual document understanding (especially Korean)
- Users wanting local-first LLM deployment with cloud fallback options
- Developers building RAG applications with advanced agent orchestration
- Business users creating custom AI workflows without coding

## Performance Targets

- Fast Mode: <1s response time for simple queries
- Balanced Mode: <3s for standard queries
- Deep Mode: <10s for complex multi-document analysis
- Cache hit rate: 60%+
- Document processing: 95%+ accuracy
- Agent Builder execution: <5s for typical workflows

## Architecture Highlights

- **Domain-Driven Design**: Agent Builder uses DDD with clear domain boundaries
- **Event-Driven**: Decoupled components communicate via event bus
- **Multi-Level Caching**: L1 (memory) + L2 (Redis) for optimal performance
- **Resilience Patterns**: Circuit breaker, retry, saga for reliability
