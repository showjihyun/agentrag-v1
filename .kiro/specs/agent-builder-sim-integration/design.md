# Design Document

## Overview

This document describes the design for integrating Sim Workflows LLM's core features into AgenticRAG's agent-builder. The integration will transform the current basic workflow system into a comprehensive visual workflow builder with 70+ tools, advanced execution capabilities, and multiple trigger options.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                    │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Workflow   │  │    Block     │  │   Execution  │     │
│  │    Editor    │  │   Palette    │  │   Console    │     │
│  │  (ReactFlow) │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │    Block     │  │   Workflow   │  │   Trigger    │     │
│  │   Registry   │  │   Executor   │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     Tool     │  │  Knowledge   │  │   Schedule   │     │
│  │   Registry   │  │     Base     │  │   Service    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│          PostgreSQL + Milvus + Redis                         │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Block System

#### Block Registry
```python
class BlockRegistry:
    """Central registry for all block types."""
    
    _blocks: Dict[str, Type[BaseBlock]] = {}
    
    @classmethod
    def register(cls, block_type: str):
        """Decorator to register a block class."""
        
    @classmethod
    def get_block(cls, block_type: str) -> Type[BaseBlock]:
        """Get block class by type."""
        
    @classmethod
    def list_blocks(cls) -> List[BlockConfig]:
        """List all registered blocks."""
```

#### Base Block
```python
class BaseBlock(ABC):
    """Base class for all blocks."""
    
    def __init__(self, config: BlockConfig):
        self.config = config
    
    @abstractmethod
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Execute the block logic."""
        
    @classmethod
    @abstractmethod
    def get_config(cls) -> BlockConfig:
        """Return block configuration."""
        
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate block inputs."""
```

#### Block Configuration
```python
@dataclass
class BlockConfig:
    type: str
    name: str
    description: str
    category: str  # 'blocks', 'tools', 'triggers'
    sub_blocks: List[SubBlockConfig]
    inputs: Dict[str, ParamConfig]
    outputs: Dict[str, OutputConfig]
    bg_color: str
    icon: str
    auth_mode: Optional[str] = None
    docs_link: Optional[str] = None
```

### 2. Execution Engine

#### Workflow Executor
```python
class WorkflowExecutor:
    """Executes workflows by processing blocks in order."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.block_registry = BlockRegistry
    
    async def execute(
        self,
        workflow_id: str,
        trigger: str,
        input_data: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a workflow."""
        
        # 1. Load workflow definition
        workflow = await self.load_workflow(workflow_id)
        
        # 2. Create execution context
        context = ExecutionContext(
            workflow_id=workflow_id,
            execution_id=generate_id(),
            block_states={},
            block_logs=[],
            environment_variables=await self.load_env_vars(),
            workflow_variables=workflow.variables
        )
        
        # 3. Find start blocks
        start_blocks = self.find_start_blocks(workflow)
        
        # 4. Execute blocks
        for block in start_blocks:
            await self.execute_block(block, context)
        
        # 5. Save execution log
        await self.save_execution_log(context)
        
        return ExecutionResult(
            success=True,
            output=self.get_final_output(context),
            logs=context.block_logs
        )
```

#### Execution Context
```python
@dataclass
class ExecutionContext:
    workflow_id: str
    execution_id: str
    block_states: Dict[str, BlockState]
    block_logs: List[BlockLog]
    environment_variables: Dict[str, str]
    workflow_variables: Dict[str, Any]
    loop_iterations: Dict[str, int]
    parallel_executions: Dict[str, ParallelExecution]
    decisions: Dict[str, str]  # For routing
```

### 3. Tool System

#### Tool Registry
```python
class ToolRegistry:
    """Registry for all tool integrations."""
    
    _tools: Dict[str, ToolConfig] = {}
    
    @classmethod
    def register_tool(cls, tool_id: str, config: ToolConfig):
        """Register a tool."""
        
    @classmethod
    def get_tool(cls, tool_id: str) -> ToolConfig:
        """Get tool configuration."""
        
    @classmethod
    def execute_tool(
        cls,
        tool_id: str,
        params: Dict[str, Any]
    ) -> ToolResponse:
        """Execute a tool."""
```

#### Tool Configuration
```python
@dataclass
class ToolConfig:
    id: str
    name: str
    description: str
    params: Dict[str, ParamDefinition]
    outputs: Dict[str, OutputDefinition]
    oauth: Optional[OAuthConfig]
    request: RequestConfig
    transform_response: Optional[Callable]
```

### 4. Frontend Components

#### Workflow Editor (ReactFlow)
```typescript
interface WorkflowEditorProps {
  workflowId: string
}

export function WorkflowEditor({ workflowId }: WorkflowEditorProps) {
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  
  // Load workflow
  useEffect(() => {
    loadWorkflow(workflowId)
  }, [workflowId])
  
  // Handle node addition
  const addBlock = (blockType: string) => {
    const newNode = createNode(blockType)
    setNodes([...nodes, newNode])
  }
  
  // Handle connection
  const onConnect = (connection: Connection) => {
    const newEdge = createEdge(connection)
    setEdges([...edges, newEdge])
  }
  
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
    >
      <Controls />
      <Background />
      <MiniMap />
    </ReactFlow>
  )
}
```

#### Block Palette
```typescript
export function BlockPalette({ onAddBlock }: BlockPaletteProps) {
  const [blocks, setBlocks] = useState<BlockConfig[]>([])
  const [category, setCategory] = useState<'all' | 'blocks' | 'tools' | 'triggers'>('all')
  
  // Load blocks
  useEffect(() => {
    loadBlocks()
  }, [])
  
  // Filter by category
  const filteredBlocks = blocks.filter(
    block => category === 'all' || block.category === category
  )
  
  return (
    <div className="block-palette">
      <CategoryTabs value={category} onChange={setCategory} />
      <BlockList blocks={filteredBlocks} onAdd={onAddBlock} />
    </div>
  )
}
```

#### SubBlock Renderer
```typescript
export function SubBlockRenderer({ subBlocks }: SubBlockRendererProps) {
  return (
    <>
      {subBlocks.map(subBlock => {
        switch (subBlock.type) {
          case 'short-input':
            return <Input key={subBlock.id} {...subBlock} />
          case 'long-input':
            return <Textarea key={subBlock.id} {...subBlock} />
          case 'dropdown':
            return <Select key={subBlock.id} {...subBlock} />
          case 'code':
            return <CodeEditor key={subBlock.id} {...subBlock} />
          case 'oauth-input':
            return <OAuthInput key={subBlock.id} {...subBlock} />
          // ... other types
        }
      })}
    </>
  )
}
```

## Data Models

### Database Schema

#### agent_blocks
```sql
CREATE TABLE agent_blocks (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    position_x NUMERIC NOT NULL,
    position_y NUMERIC NOT NULL,
    config JSONB NOT NULL DEFAULT '{}',
    sub_blocks JSONB NOT NULL DEFAULT '{}',
    inputs JSONB NOT NULL DEFAULT '{}',
    outputs JSONB NOT NULL DEFAULT '{}',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### agent_edges
```sql
CREATE TABLE agent_edges (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    source_block_id UUID REFERENCES agent_blocks(id) ON DELETE CASCADE,
    target_block_id UUID REFERENCES agent_blocks(id) ON DELETE CASCADE,
    source_handle VARCHAR(50),
    target_handle VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

#### workflow_execution_logs
```sql
CREATE TABLE workflow_execution_logs (
    id UUID PRIMARY KEY,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    trigger VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    ended_at TIMESTAMP,
    duration_ms INTEGER,
    execution_data JSONB NOT NULL DEFAULT '{}',
    cost JSONB,
    files JSONB,
    status VARCHAR(20) NOT NULL DEFAULT 'running',
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## Error Handling

### Error Types
1. **Validation Errors**: Invalid block configuration, missing required inputs
2. **Execution Errors**: Block execution failures, API errors
3. **System Errors**: Database errors, network errors

### Error Handling Strategy
```python
class WorkflowExecutor:
    async def execute_block(self, block, context):
        try:
            # Execute block
            output = await block.execute(inputs, context)
            
            # Update context
            context.block_states[block.id] = {
                'output': output,
                'executed': True
            }
            
        except ValidationError as e:
            # Log validation error
            context.block_logs.append({
                'block_id': block.id,
                'error': str(e),
                'error_type': 'validation'
            })
            raise
            
        except ExecutionError as e:
            # Log execution error
            context.block_logs.append({
                'block_id': block.id,
                'error': str(e),
                'error_type': 'execution'
            })
            raise
            
        except Exception as e:
            # Log system error
            context.block_logs.append({
                'block_id': block.id,
                'error': str(e),
                'error_type': 'system'
            })
            raise
```

## Testing Strategy

### Unit Tests
- Block execution logic
- Tool integrations
- Validation functions
- SubBlock rendering

### Integration Tests
- Workflow execution end-to-end
- Database operations
- API endpoints
- Trigger handling

### E2E Tests
- Visual workflow creation
- Block configuration
- Workflow execution
- Result visualization

## Performance Considerations

### Optimization Strategies
1. **Lazy Loading**: Load blocks and tools on demand
2. **Caching**: Cache block configurations and tool definitions
3. **Parallel Execution**: Execute independent blocks concurrently
4. **Database Indexing**: Index frequently queried columns
5. **Connection Pooling**: Reuse database connections

### Scalability
1. **Horizontal Scaling**: Multiple executor instances
2. **Queue System**: Celery for background execution
3. **Load Balancing**: Distribute execution across workers
4. **Caching Layer**: Redis for session and execution state

## Security Considerations

### Authentication & Authorization
- OAuth 2.0 for tool integrations
- API key authentication for workflow execution
- Role-based access control for workflows

### Data Protection
- Encrypt sensitive configuration (API keys, credentials)
- Secure webhook endpoints with signatures
- Validate all user inputs
- Sanitize execution outputs

### Rate Limiting
- Limit workflow executions per user
- Limit API calls per workflow
- Throttle webhook requests

## Deployment Strategy

### Phase 1: Database & Models (Week 1-2)
- Create database migrations
- Implement SQLAlchemy models
- Add Pydantic schemas

### Phase 2: Block System (Week 3-5)
- Implement Block Registry
- Create base blocks (5-10)
- Add SubBlock rendering

### Phase 3: Execution Engine (Week 6-8)
- Implement Workflow Executor
- Add control flow (conditions, loops, parallel)
- Implement execution logging

### Phase 4: Frontend (Week 9-11)
- Build ReactFlow editor
- Create Block Palette
- Add execution console

### Phase 5: Advanced Features (Week 12-15)
- Integrate 70+ tools
- Add triggers (webhook, schedule, API)
- Integrate existing Milvus Knowledge Base

## Knowledge Base Integration (Milvus)

### Existing Milvus Infrastructure

The AgenticRAG system already has a robust Milvus implementation:

```python
# Existing Milvus Schema (backend/models/milvus_schema.py)
- Document Collection: 12 fields including embeddings, metadata
- LTM Collection: Long-term memory storage
- HNSW Indexing: Optimized for fast similarity search
- COSINE Metric: Standard for RAG applications
```

### Integration Strategy

#### 1. Reuse Existing Components
```python
# Use existing Milvus connection
from backend.models.milvus_schema import (
    get_document_collection_schema,
    get_index_params,
    get_search_params
)

# Use existing embedding service
from backend.services.embedding import EmbeddingService

# Use existing document processing
from backend.services.document_processor import DocumentProcessor
```

#### 2. Knowledge Base Block Implementation
```python
@BlockRegistry.register('knowledge_base')
class KnowledgeBaseBlock(BaseBlock):
    """Block for searching Milvus document collection."""
    
    @classmethod
    def get_config(cls) -> BlockConfig:
        return BlockConfig(
            type='knowledge_base',
            name='Knowledge Base',
            description='Search documents using vector similarity',
            category='tools',
            sub_blocks=[
                SubBlockConfig(
                    id='query',
                    type='long-input',
                    title='Search Query',
                    required=True
                ),
                SubBlockConfig(
                    id='top_k',
                    type='short-input',
                    title='Number of Results',
                    defaultValue=5
                ),
                SubBlockConfig(
                    id='filters',
                    type='code',
                    title='Metadata Filters',
                    language='json',
                    placeholder='{"author": "John Doe"}'
                )
            ],
            inputs={
                'query': {'type': 'string'},
                'top_k': {'type': 'number'},
                'filters': {'type': 'json'}
            },
            outputs={
                'results': {'type': 'array'},
                'count': {'type': 'number'}
            }
        )
    
    async def execute(self, inputs, context):
        from pymilvus import connections, Collection
        from backend.config import settings
        
        # Connect to Milvus
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        
        # Get collection
        collection = Collection(settings.MILVUS_COLLECTION_NAME)
        collection.load()
        
        # Generate query embedding
        embedding_service = EmbeddingService()
        query_embedding = await embedding_service.embed_text(inputs['query'])
        
        # Build filter expression
        filter_expr = self._build_filter_expression(inputs.get('filters', {}))
        
        # Search
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=inputs.get('top_k', 5),
            expr=filter_expr,
            output_fields=["text", "document_name", "author", "keywords"]
        )
        
        # Format results
        formatted_results = [
            {
                'text': hit.entity.get('text'),
                'document': hit.entity.get('document_name'),
                'author': hit.entity.get('author'),
                'score': hit.score
            }
            for hit in results[0]
        ]
        
        return {
            'results': formatted_results,
            'count': len(formatted_results)
        }
    
    def _build_filter_expression(self, filters: dict) -> str:
        """Build Milvus filter expression from dict."""
        if not filters:
            return ""
        
        expressions = []
        for key, value in filters.items():
            if isinstance(value, str):
                expressions.append(f'{key} == "{value}"')
            else:
                expressions.append(f'{key} == {value}')
        
        return " && ".join(expressions)
```

#### 3. Metadata Filtering

Leverage existing Milvus metadata fields:
- `author`: Document author
- `creation_date`: Document creation timestamp
- `language`: Document language (ISO 639-1)
- `keywords`: Document keywords (comma-separated)
- `file_type`: Document file type
- `document_name`: Original filename

#### 4. UI Components

```typescript
// Knowledge Base SubBlock Renderer
export function KnowledgeBaseSelector({ value, onChange }: Props) {
  const [collections, setCollections] = useState<string[]>([])
  
  useEffect(() => {
    // Load available Milvus collections
    loadCollections()
  }, [])
  
  return (
    <Select value={value} onChange={onChange}>
      {collections.map(collection => (
        <option key={collection} value={collection}>
          {collection}
        </option>
      ))}
    </Select>
  )
}
```

### Benefits of Using Existing Milvus

1. **No Migration**: Reuse existing vector database
2. **Proven Performance**: Already optimized for RAG
3. **Rich Metadata**: 12-field schema with comprehensive metadata
4. **HNSW Indexing**: Fast similarity search
5. **Existing Tools**: Document upload, chunking, embedding already implemented
