# Product Overview

## Agentic RAG System

An intelligent document search and question-answering system that combines multi-agent architecture with multimodal RAG capabilities.

## Core Value Proposition

Agentic RAG goes beyond traditional RAG systems by using adaptive query routing and multi-agent orchestration to deliver fast, accurate responses across diverse document types and query complexities.

## Key Features

- **Multi-Agent Architecture**: Aggregator agent orchestrates specialized agents (Vector Search, Local Data, Web Search) using ReAct + Chain of Thought reasoning
- **Adaptive Query Routing**: Automatically analyzes query complexity and routes to optimal processing mode (Fast <1s, Balanced <3s, Deep <10s)
- **Multimodal Document Processing**: Supports PDF, DOCX, HWP/HWPX, PPT/PPTX, XLSX, images with advanced OCR (PaddleOCR, PP-OCRv5, PP-StructureV3)
- **Hybrid Search**: Combines vector search (semantic) with BM25 (keyword) for optimal retrieval
- **Real-time Streaming**: Server-Sent Events (SSE) for live agent reasoning and response generation
- **Multi-LLM Support**: Works with Ollama (local), OpenAI, Anthropic with automatic fallback
- **Web Search Integration**: DuckDuckGo-based search (no API key required)
- **Korean Language Optimized**: Uses jhgan/ko-sroberta-multitask embeddings and Korean-specific rerankers

## Target Users

- Organizations needing intelligent document search across large knowledge bases
- Teams requiring multilingual document understanding (especially Korean)
- Users wanting local-first LLM deployment with cloud fallback options
- Developers building RAG applications with advanced agent orchestration

## Performance Targets

- Fast Mode: <1s response time for simple queries
- Balanced Mode: <3s for standard queries
- Deep Mode: <10s for complex multi-document analysis
- Cache hit rate: 60%+
- Document processing: 95%+ accuracy
