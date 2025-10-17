# Product Overview

This is an Agentic RAG (Retrieval-Augmented Generation) system that combines vector search with intelligent agent-based reasoning to provide accurate, contextual responses to user queries.

## Core Capabilities

- **Multi-Agent Architecture**: Specialized agents (Vector Search, Local Data, Web Search) coordinated by an Aggregator Agent using ReAct and Chain of Thought patterns
- **Advanced Reasoning**: Uses ReAct (Reasoning + Acting) and Chain of Thought (CoT) for systematic query decomposition and problem-solving
- **Memory Management**: Dual memory system with Short-Term Memory (STM) for conversations and Long-Term Memory (LTM) for learned patterns
- **MCP Integration**: Model Context Protocol servers enable modular tool access for vector search, local data, and web search
- **Multi-LLM Support**: Flexible provider support including local Ollama, OpenAI, and Claude
- **Document Processing**: Upload and index PDF, TXT, DOCX, PPT, PPTX, HWP, HWPX, and MD documents with semantic chunking
- **Real-time Streaming**: Live updates showing agent reasoning steps and thought processes
- **Multimodal RAG**: Support for images, tables, and charts extraction from documents

## Key Features

- Vector similarity search using Milvus database
- Intelligent document retrieval with source citations
- Session-based conversation memory with Redis
- Responsive web interface built with Next.js/React
- RESTful API with Server-Sent Events for streaming responses
- Adaptive query routing with multiple processing modes (Fast, Balanced, Deep)
- Speculative RAG for improved response quality
- User authentication and document access control
