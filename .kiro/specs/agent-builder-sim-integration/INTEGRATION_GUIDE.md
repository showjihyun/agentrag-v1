# Integration Guide: Reusing Existing Agent Builder Infrastructure

## Overview

This document maps the existing agent-builder implementation to the new sim-integration features, identifying components that can be reused, extended, or need to be created from scratch.

---

## 🔄 Reusable Components

### 1. Database Infrastructure

#### ✅ Already Implemented (Reuse As-Is)
```python
# From: backend/db/models/agent_builder.py
- Agent, AgentVersion, AgentTool, Tool models
- AgentExecution, ExecutionStep, ExecutionMetrics models
- Permission, ResourceShare, AuditLog models
- Variable, Secret models
```

#### 🔧 Extend for Sim Integration
```python
# Add to existing agent_builder.py:
- AgentBlock model (new - for visual blocks)
- AgentEdge model (new - for block connections)
- WorkflowSubflow model (new - for loops/parallel)
- WorkflowSchedule model (new - for cron schedules)
- WorkflowWebhook model (new - for webhook triggers)
```

**Action**: Extend existing models file, don't create new one.

---

### 2. Backend Services

#### ✅ Already Implemented (Reuse)
```python
# From: backend/services/agent_builder/

✅ agent_service.py
   - CRUD operations for agents
   - Agent cloning, export/import
   - Version management
   → Reuse for agent management in workflows

✅ variable_resolver.py
   - Variable resolution with scope precedence
   - Redis caching
   → Reuse for workflow variable resolution

✅ secret_manager.py
   - AES-256 encryption for secrets
   → Reuse for block credentials

✅ tool_registry.py
   - Tool registration and validation
   → Extend with 70+ new tool blocks
```

#### 🔧 Extend for Sim Integration
```python
# Extend existing services:

workflow_service.py (EXISTS)
   ✅ Basic workflow CRUD
   🔧 ADD: Block management
   🔧 ADD: Edge management
   🔧 ADD: Workflow validation (cycles, disconnected nodes)

# Create new services:

block_service.py (NEW)
   - Block CRUD operations
   - Block execution
   - SubBlock rendering logic

workflow_executor.py (EXISTS - using LangGraph)
   ✅ LangGraph StateGraph compilation
   ✅ Streaming execution
   🔧 ADD: Block-based execution
   🔧 ADD: Loop/parallel support
   🔧 ADD: Condition branching
```

**Action**: Extend existing services, add new block-specific services.

---

### 3. API Endpoints

#### ✅ Already Implemented (Reuse)
```python
# From: backend/api/agent_builder/

✅ agents.py
   - POST /api/agent-builder/agents
   - GET /api/agent-builder/agents/{id}
   - PUT /api/agent-builder/agents/{id}
   - DELETE /api/agent-builder/agents/{id}
   → Reuse for agent management

✅ workflows.py
   - POST /api/agent-builder/workflows
   - GET /api/agent-builder/workflows/{id}
   - PUT /api/agent-builder/workflows/{id}
   - DELETE /api/agent-builder/workflows/{id}
   → Extend with block/edge endpoints

✅ executions.py
   - POST /api/agent-builder/executions/agents/{id}
   - POST /api/agent-builder/executions/workflows/{id}
   - GET /api/agent-builder/executions/{id}
   → Reuse for workflow execution

✅ variables.py
   - Variable CRUD endpoints
   → Reuse for workflow variables

✅ knowledgebases.py
   - Knowledgebase CRUD endpoints
   → Reuse for Knowledge Base blocks
```

#### 🔧 Extend for Sim Integration
```python
# Extend workflows.py:
POST /api/agent-builder/workflows/{id}/blocks
GET /api/agent-builder/workflows/{id}/blocks
PUT /api/agent-builder/workflows/{id}/blocks/{block_id}
DELETE /api/agent-builder/workflows/{id}/blocks/{block_id}

POST /api/agent-builder/workflows/{id}/edges
DELETE /api/agent-builder/workflows/{id}/edges/{edge_id}

# Create new endpoints:
POST /api/agent-builder/workflows/{id}/schedules
POST /api/agent-builder/workflows/{id}/webhooks
```

**Action**: Extend existing API routers, don't create duplicate endpoints.

---

### 4. Frontend Components

#### ✅ Already Implemented (Reuse)
```typescript
// From: frontend/app/agent-builder/

✅ layout.tsx
   - Sidebar navigation
   - Responsive layout
   → Reuse as main layout

✅ agents/page.tsx
   - Agent list with cards
   - Search and filtering
   → Reuse for agent management

✅ workflows/page.tsx
   - Workflow list
   → Extend with visual preview

✅ executions/page.tsx
   - Execution monitoring
   - Real-time updates
   → Reuse for workflow execution monitoring

✅ variables/page.tsx
   - Variable management
   → Reuse for workflow variables

✅ knowledgebases/page.tsx
   - Knowledgebase management
   → Reuse for Knowledge Base blocks
```

#### 🔧 Extend for Sim Integration
```typescript
// Extend workflows/[id]/page.tsx:
✅ Basic workflow view
🔧 ADD: Visual workflow editor (ReactFlow)
🔧 ADD: Block palette
🔧 ADD: Configuration panel

// Create new components:
components/agent-builder/
  ├── WorkflowEditor.tsx (NEW - ReactFlow canvas)
  ├── BlockPalette.tsx (NEW - draggable blocks)
  ├── BlockConfigPanel.tsx (NEW - block settings)
  ├── SubBlockRenderer.tsx (NEW - dynamic forms)
  └── ExecutionConsole.tsx (NEW - real-time logs)
```

**Action**: Extend existing pages, add new visual components.

---

### 5. Milvus Integration

#### ✅ Already Implemented (Reuse Completely)
```python
# From: backend/models/milvus_schema.py
✅ get_document_collection_schema()
   - 12-field schema with embeddings
   - HNSW indexing
   - COSINE metric

✅ get_index_params()
   - Optimized index configuration
   
✅ get_search_params()
   - Search parameter optimization

# From: backend/services/
✅ embedding.py - EmbeddingService
✅ document_processor.py - DocumentProcessor
✅ hybrid_search.py - HybridSearch

# From: backend/config.py
✅ MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION_NAME
```

**Action**: Use existing Milvus infrastructure completely. No changes needed.

---

### 6. LangGraph Integration

#### ✅ Already Implemented (Extend)
```python
# From: backend/services/agent_builder/workflow_executor.py

✅ WorkflowExecutor class
   - StateGraph compilation
   - Streaming execution
   - Error handling

🔧 EXTEND:
   - Add block-based node creation
   - Add loop node support
   - Add parallel node support
   - Add condition node support
```

**Action**: Extend existing WorkflowExecutor, don't create new one.

---

## 📋 Implementation Strategy

### Phase 1: Database Schema Extension
```python
# File: backend/db/models/agent_builder.py (EXTEND EXISTING)

# Add to existing file:
class AgentBlock(Base):
    __tablename__ = "agent_blocks"
    # ... (from IMPLEMENTATION_PHASE1.md)

class AgentEdge(Base):
    __tablename__ = "agent_edges"
    # ... (from IMPLEMENTATION_PHASE1.md)

# Update existing Workflow model:
class Workflow(Base):
    # ... existing fields ...
    
    # ADD new relationships:
    blocks = relationship("AgentBlock", back_populates="workflow")
    edges = relationship("AgentEdge", back_populates="workflow")
    schedules = relationship("WorkflowSchedule", back_populates="workflow")
    webhooks = relationship("WorkflowWebhook", back_populates="workflow")
```

### Phase 2: Service Layer Extension
```python
# File: backend/services/agent_builder/workflow_service.py (EXTEND EXISTING)

class WorkflowService:
    # ... existing methods ...
    
    # ADD new methods:
    async def add_block(self, workflow_id: str, block_data: BlockCreate) -> AgentBlock:
        """Add block to workflow"""
        
    async def add_edge(self, workflow_id: str, edge_data: EdgeCreate) -> AgentEdge:
        """Add edge between blocks"""
        
    async def validate_workflow(self, workflow_id: str) -> ValidationResult:
        """Validate workflow graph"""
```

### Phase 3: API Extension
```python
# File: backend/api/agent_builder/workflows.py (EXTEND EXISTING)

# ADD new endpoints to existing router:

@router.post("/{workflow_id}/blocks")
async def add_block_to_workflow(
    workflow_id: str,
    block_data: BlockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add block to workflow"""
    # Implementation

@router.post("/{workflow_id}/edges")
async def add_edge_to_workflow(
    workflow_id: str,
    edge_data: EdgeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add edge between blocks"""
    # Implementation
```

### Phase 4: Frontend Extension
```typescript
// File: frontend/app/agent-builder/workflows/[id]/page.tsx (EXTEND EXISTING)

export default function WorkflowPage({ params }: { params: { id: string } }) {
  // ... existing code ...
  
  // ADD: Visual editor toggle
  const [viewMode, setViewMode] = useState<'visual' | 'json'>('visual')
  
  return (
    <div>
      {/* Existing workflow info */}
      
      {/* ADD: View mode toggle */}
      <Tabs value={viewMode} onValueChange={setViewMode}>
        <TabsList>
          <TabsTrigger value="visual">Visual Editor</TabsTrigger>
          <TabsTrigger value="json">JSON Editor</TabsTrigger>
        </TabsList>
        
        <TabsContent value="visual">
          <WorkflowEditor workflowId={params.id} />
        </TabsContent>
        
        <TabsContent value="json">
          {/* Existing JSON editor */}
        </TabsContent>
      </Tabs>
    </div>
  )
}
```

---

## 🎯 Key Integration Points

### 1. Workflow Execution
```python
# REUSE: backend/services/agent_builder/workflow_executor.py
# EXTEND: Add block execution support

class WorkflowExecutor:
    async def execute_workflow(self, workflow_id: str, input_data: dict):
        # ✅ EXISTING: Load workflow
        workflow = await self.workflow_service.get_workflow(workflow_id)
        
        # ✅ EXISTING: Compile to LangGraph
        graph = await self.compile_workflow(workflow)
        
        # 🔧 EXTEND: Add block-based nodes
        for block in workflow.blocks:
            graph.add_node(block.id, self._create_block_node(block))
        
        # ✅ EXISTING: Execute with streaming
        async for step in graph.astream(initial_state):
            yield step
```

### 2. Knowledge Base Integration
```python
# REUSE: Existing Milvus infrastructure completely

# File: backend/core/blocks/knowledge_base.py (NEW)
from backend.models.milvus_schema import get_document_collection_schema
from backend.services.embedding import EmbeddingService
from pymilvus import connections, Collection

@BlockRegistry.register('knowledge_base')
class KnowledgeBaseBlock(BaseBlock):
    async def execute(self, inputs, context):
        # ✅ REUSE: Existing Milvus connection
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # ✅ REUSE: Existing embedding service
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.embed_text(inputs['query'])
        
        # ✅ REUSE: Existing collection
        collection = Collection(settings.MILVUS_COLLECTION_NAME)
        results = collection.search(...)
        
        return {'results': results}
```

### 3. Variable Resolution
```python
# REUSE: backend/services/agent_builder/variable_resolver.py

# In block execution:
async def execute_block(self, block, inputs, context):
    # ✅ REUSE: Existing variable resolver
    resolved_inputs = await self.variable_resolver.resolve_variables(
        inputs,
        context
    )
    
    # Execute block with resolved inputs
    return await block.execute(resolved_inputs, context)
```

---

## ✅ Checklist for Implementation

### Before Starting Each Phase:
- [ ] Review existing implementation in agent-builder spec
- [ ] Identify reusable components
- [ ] Plan extensions vs new implementations
- [ ] Update import statements to use existing modules
- [ ] Test integration with existing features

### During Implementation:
- [ ] Extend existing files instead of creating duplicates
- [ ] Reuse existing database models where possible
- [ ] Call existing services instead of reimplementing
- [ ] Follow existing code patterns and conventions
- [ ] Maintain backward compatibility

### After Implementation:
- [ ] Verify existing features still work
- [ ] Test integration between old and new features
- [ ] Update documentation to reflect extensions
- [ ] Remove any duplicate code
- [ ] Optimize by consolidating similar logic

---

## 📊 Reuse vs New Implementation Summary

| Component | Reuse | Extend | New |
|-----------|-------|--------|-----|
| Database Models | 70% | 20% | 10% |
| Backend Services | 60% | 30% | 10% |
| API Endpoints | 50% | 40% | 10% |
| Frontend Pages | 40% | 40% | 20% |
| Frontend Components | 20% | 30% | 50% |
| Milvus Integration | 100% | 0% | 0% |
| LangGraph Integration | 70% | 30% | 0% |

**Overall**: ~60% reuse, ~30% extend, ~10% new

---

## 🚀 Quick Start Guide

1. **Read existing agent-builder spec**
   ```bash
   cat .kiro/specs/agent-builder/requirements.md
   cat .kiro/specs/agent-builder/design.md
   cat .kiro/specs/agent-builder/tasks.md
   ```

2. **Review existing implementation**
   ```bash
   # Database models
   cat backend/db/models/agent_builder.py
   
   # Services
   ls backend/services/agent_builder/
   
   # API endpoints
   ls backend/api/agent_builder/
   
   # Frontend
   ls frontend/app/agent-builder/
   ```

3. **Start with extensions**
   - Phase 1: Extend database models
   - Phase 2: Extend services
   - Phase 3: Extend API endpoints
   - Phase 4: Add new frontend components

4. **Test integration**
   - Run existing tests
   - Add integration tests
   - Verify backward compatibility

---

## 📝 Notes

- **Don't duplicate**: Always check if functionality exists before implementing
- **Extend, don't replace**: Prefer extending existing code over rewriting
- **Maintain compatibility**: Ensure existing features continue to work
- **Follow patterns**: Use existing code patterns and conventions
- **Reuse infrastructure**: Leverage existing Milvus, LangGraph, Redis, etc.

This approach will significantly reduce implementation time and maintain consistency across the codebase.
