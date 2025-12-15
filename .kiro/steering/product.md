# Product Overview

## Workflow Platform - Visual AI Agent Builder

A comprehensive no-code platform for building, managing, and executing AI workflows with drag-and-drop simplicity. Features multi-agent orchestration, 70+ integrations, and advanced automation capabilities.

## Core Value Proposition

The Workflow Platform empowers users to create sophisticated AI automations without coding. By combining visual workflow design with multi-agent orchestration, users can build everything from simple task automation to complex AI-powered business processes. RAG capabilities are available as workflow tools for document processing and knowledge retrieval.

## Key Features

### Core Workflow Platform
- **Visual Workflow Designer**: Drag-and-drop interface for building AI workflows
- **Chatflows**: Conversational AI flows with memory and context
- **Agentflows**: Task-oriented agent workflows with tool integration
- **Block Library**: Pre-built blocks (LLM, HTTP, Code, Condition, Loop, etc.)
- **70+ Tool Integrations**: Slack, Gmail, PostgreSQL, Vector Search, and more
- **Template Marketplace**: Share and discover workflow templates
- **Execution Monitoring**: Real-time execution tracking and debugging
- **API Keys Management**: Secure API key generation for external access
- **Embed Support**: Embed chatflows in external applications

### Advanced AI Capabilities (Available as Workflow Tools)
- **Multi-Agent Orchestration**: Coordinate multiple AI agents within workflows
- **Document Processing**: PDF, DOCX, HWP/HWPX, PPT/PPTX, XLSX processing with OCR
- **Vector Search**: Semantic search capabilities using Milvus
- **Hybrid Search**: Combines vector search with keyword search (BM25)
- **Web Search Integration**: DuckDuckGo-based search tool
- **Multi-LLM Support**: Works with Ollama (local), OpenAI, Anthropic, Google AI
- **Real-time Streaming**: Server-Sent Events (SSE) for live execution updates
- **Korean Language Support**: Optimized for Korean text processing

## Target Users

- **Business Users**: Create custom AI workflows without coding knowledge
- **Operations Teams**: Automate repetitive tasks and business processes
- **Developers**: Build complex AI applications with visual tools
- **Content Teams**: Automate content creation and processing workflows
- **Customer Support**: Build intelligent chatbots and support automation
- **Data Teams**: Create data processing and analysis pipelines
- **Marketing Teams**: Automate campaigns and lead processing

## Performance Targets

- **Workflow Execution**: <5s for typical workflows
- **Simple Automations**: <1s response time
- **Complex Multi-Agent Flows**: <10s execution time
- **Cache Hit Rate**: 60%+ for repeated operations
- **Tool Integration**: <2s average API response time
- **Real-time Updates**: <100ms latency for live monitoring
- **Uptime**: 99.9% availability target

## Architecture Highlights

- **Domain-Driven Design**: Agent Builder uses DDD with clear domain boundaries
- **Event-Driven**: Decoupled components communicate via event bus
- **Multi-Level Caching**: L1 (memory) + L2 (Redis) for optimal performance
- **Resilience Patterns**: Circuit breaker, retry, saga for reliability
