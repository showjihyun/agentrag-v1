# Agent Builder - Sim Integration Spec

## Overview

This specification defines the integration of **Sim Workflows LLM's** core features into the **AgenticRAG agent-builder** system. The goal is to transform the current basic workflow system into a comprehensive visual workflow builder with 70+ integrated tools, advanced execution capabilities, and multiple trigger options.

## Project Goals

1. **Visual Workflow Builder**: Implement ReactFlow-based drag-and-drop workflow editor
2. **Block System**: Create extensible block system with 70+ pre-built tool integrations
3. **Execution Engine**: Build robust execution engine supporting conditions, loops, and parallel execution
4. **Trigger System**: Add webhook, schedule, API, and chat triggers
5. **Knowledge Base**: Integrate pgvector-based semantic search
6. **Developer Experience**: Provide intuitive UI and comprehensive documentation

## Key Features

### 1. Block System
- **70+ Tool Blocks**: OpenAI, Anthropic, Slack, GitHub, MongoDB, PostgreSQL, etc.
- **20+ SubBlock Types**: Input fields, dropdowns, code editors, OAuth flows, etc.
- **Flexible Configuration**: Dynamic UI based on block type and configuration
- **Extensible Architecture**: Easy to add new blocks and tools

### 2. Execution Engine
- **Sequential Execution**: Execute blocks in topological order
- **Conditional Branching**: Route execution based on conditions
- **Loop Support**: For-loops and forEach-loops with iteration tracking
- **Parallel Execution**: Execute multiple branches concurrently
- **Error Handling**: Comprehensive error logging and recovery
- **Streaming Support**: Real-time output streaming for long-running operations

### 3. Visual Editor
- **ReactFlow Integration**: Professional graph editor with zoom, pan, and minimap
- **Block Palette**: Categorized block library with search
- **Configuration Panel**: Dynamic form generation based on SubBlocks
- **Validation**: Real-time validation with error highlighting
- **Auto-save**: Automatic workflow persistence

### 4. Trigger System
- **Webhooks**: Unique URLs for each workflow with signature verification
- **Schedules**: Cron-based scheduling with timezone support
- **API**: REST API endpoints with authentication
- **Chat**: Conversational interface for workflow execution
- **Manual**: On-demand execution from UI

### 5. Knowledge Base
- **Vector Search**: Milvus-based semantic search with HNSW indexing
- **Document Processing**: Upload and parse PDF, DOCX, TXT files
- **Chunking**: Intelligent text chunking with overlap
- **Embeddings**: Sentence-transformers embeddings with caching
- **Metadata Filtering**: Rich metadata filtering (author, date, language, keywords)

## Architecture

```
Frontend (Next.js + React)
├── Workflow Editor (ReactFlow)
├── Block Palette
├── Configuration Panel
└── Execution Console

Backend (FastAPI + Python)
├── Block Registry
├── Workflow Executor
├── Tool Registry
├── Trigger Manager
└── Knowledge Base Service

Database
├── PostgreSQL
│   ├── Workflows & Blocks
│   ├── Execution Logs
│   └── Schedules & Webhooks
└── Milvus
    └── Vector Embeddings & Document Chunks
```

## Implementation Phases

### Phase 1: Database & Models (Week 1-2)
- Create database migrations for 6 new tables
- Implement SQLAlchemy models
- Add Pydantic schemas
- Write database tests

### Phase 2: Block System (Week 3-5)
- Implement Block Registry
- Create Base Block class
- Build 5-10 essential blocks (OpenAI, HTTP, Condition, Loop, Parallel)
- Add SubBlock rendering

### Phase 3: Execution Engine (Week 6-8)
- Implement Workflow Executor
- Add execution context management
- Implement control flow (conditions, loops, parallel)
- Add execution logging

### Phase 4: Frontend (Week 9-11)
- Build ReactFlow workflow editor
- Create Block Palette component
- Implement configuration panel
- Add SubBlock components

### Phase 5: Tool Integration (Week 12-14)
- Create Tool Registry
- Integrate 70+ tools across categories:
  - AI/LLM (10+ tools)
  - Communication (10+ tools)
  - Productivity (10+ tools)
  - Data (10+ tools)
  - Search (5+ tools)

### Phase 6: Triggers (Week 15-16)
- Implement webhook triggers
- Add schedule triggers (Celery)
- Create API triggers
- Build chat triggers

### Phase 7: Knowledge Base (Week 17-18)
- Integrate existing Milvus collections
- Implement document processing workflow
- Add vector search block
- Create Knowledge Base block

### Phase 8: Advanced Features (Week 19-20)
- Add workflow variables
- Build execution console
- Implement validation
- Create templates and versioning

## Technology Stack

### Backend
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL 14+
- **Vector DB**: Milvus 2.3+
- **Validation**: Pydantic
- **Task Queue**: Celery + Redis
- **Testing**: pytest

### Frontend
- **Framework**: Next.js 14
- **UI Library**: React 18
- **Flow Editor**: ReactFlow
- **State Management**: Zustand
- **UI Components**: shadcn/ui
- **Testing**: Vitest + Playwright

### Infrastructure
- **Database**: PostgreSQL 14+
- **Vector DB**: Milvus 2.3+ (existing)
- **Cache**: Redis
- **Queue**: Celery with Redis broker
- **Storage**: S3-compatible object storage

## File Structure

```
.kiro/specs/agent-builder-sim-integration/
├── README.md              # This file - project overview
├── requirements.md        # Detailed requirements with user stories
├── design.md             # Architecture and design decisions
├── tasks.md              # Implementation tasks organized by phase
└── INTEGRATION_GUIDE.md  # 🔑 Guide for reusing existing agent-builder code
```

## 🔑 Important: Code Reuse Strategy

**Before implementing any task, read `INTEGRATION_GUIDE.md`**

This project builds on top of the existing agent-builder implementation. The integration guide shows:
- Which components to **REUSE** (60% of code)
- Which components to **EXTEND** (30% of code)
- Which components to **CREATE NEW** (10% of code)

Key reuse areas:
- ✅ **Database Models**: Extend existing agent_builder.py (don't create new file)
- ✅ **Services**: Extend existing services (agent_service, workflow_service, variable_resolver)
- ✅ **API Endpoints**: Extend existing routers (workflows.py, executions.py)
- ✅ **Milvus**: Use existing infrastructure 100% (no changes needed)
- ✅ **LangGraph**: Extend existing WorkflowExecutor (don't create new one)
- ✅ **Frontend**: Extend existing pages (workflows, executions, variables)

## Getting Started

### For Developers

1. **Review Requirements**: Read `requirements.md` to understand user stories and acceptance criteria
2. **Study Design**: Review `design.md` for architecture and component details
3. **Check Tasks**: See `tasks.md` for implementation plan and current progress
4. **Start Phase 1**: Begin with database schema and models

### For Product Managers

1. **Review User Stories**: Check `requirements.md` for feature requirements
2. **Track Progress**: Monitor task completion in `tasks.md`
3. **Validate Features**: Ensure acceptance criteria are met for each requirement

### For Designers

1. **Review UI Requirements**: Check SubBlock types and UI components in `design.md`
2. **Design Mockups**: Create mockups for workflow editor, block palette, and configuration panel
3. **Validate UX**: Ensure design meets usability requirements

## Success Criteria

### Functional Requirements
- ✅ All 15 requirements implemented with acceptance criteria met
- ✅ 70+ tool integrations working correctly
- ✅ Execution engine handles conditions, loops, and parallel execution
- ✅ All trigger types (webhook, schedule, API, chat) functional
- ✅ Knowledge Base integration with vector search working

### Non-Functional Requirements
- ✅ Workflow execution completes within 30 seconds for typical workflows
- ✅ UI responds within 100ms for user interactions
- ✅ System handles 100+ concurrent workflow executions
- ✅ 99.9% uptime for webhook and schedule triggers
- ✅ Comprehensive test coverage (>80%)

### User Experience
- ✅ Intuitive drag-and-drop workflow creation
- ✅ Clear error messages and validation feedback
- ✅ Responsive UI on desktop and tablet
- ✅ Comprehensive documentation and examples
- ✅ Smooth onboarding experience

## Related Documents

- **AGENT_BUILDER_ENHANCEMENT_SPEC.md**: Original analysis and integration plan
- **IMPLEMENTATION_PHASE1.md**: Detailed Phase 1 implementation guide
- **AGENT_BUILDER_INTEGRATION_SUMMARY.md**: Executive summary of integration

## Support

For questions or issues:
1. Review the requirements and design documents
2. Check the tasks list for implementation status
3. Consult the related documents for additional context
4. Reach out to the development team

## License

This specification is part of the AgenticRAG project and follows the same license terms.

---

**Last Updated**: 2025-01-30
**Status**: Ready for Implementation
**Next Phase**: Phase 1 - Database Schema & Backend Models
