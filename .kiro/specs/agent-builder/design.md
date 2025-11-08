# Design Document

## Overview

The Agent Builder feature extends AgenticRAG with a comprehensive platform for creating, managing, and executing custom AI agents and workflows. The design leverages AgenticRAG's existing infrastructure including FastAPI, Next.js, SQLAlchemy, LangChain, LangGraph, Milvus, PostgreSQL, and Redis.

### Key Design Principles

1. **Modularity**: Agents, blocks, and workflows are composable building blocks
2. **Reusability**: Templates, blocks, and knowledgebases can be shared and reused
3. **Extensibility**: New tools, blocks, and agent types can be added without core changes
4. **Performance**: Caching, parallel execution, and streaming for optimal user experience
5. **Security**: Fine-grained permissions, encrypted secrets, and audit logging
6. **Observability**: Comprehensive monitoring, tracing, and debugging capabilities

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js 15 + React 19)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent Builder│  │   Workflow   │  │  Execution   │          │
│  │      UI      │  │   Designer   │  │   Monitor    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │    Block     │  │ Knowledgebase│  │  Variables   │          │
│  │   Library    │  │   Manager    │  │   Manager    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            ↕ REST API + SSE
┌─────────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Agent Builder Service Layer                  │  │
│  │  • AgentService  • BlockService  • WorkflowService       │  │
│  │  • KnowledgebaseService  • VariableService               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LangGraph Workflow Execution Engine            │  │
│  │  • StateGraph Compiler  • Node Executor  • Streaming     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer (SQLAlchemy ORM)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  PostgreSQL Database                      │  │
│  │  • agents  • agent_versions  • agent_executions          │  │
│  │  • blocks  • block_versions  • workflows                 │  │
│  │  • knowledgebases  • variables  • permissions            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Milvus Vector Store                          │  │
│  │  • Knowledgebase Collections  • LTM Collections          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Redis Cache                            │  │
│  │  • Execution Cache  • Variable Cache  • Rate Limiting    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture


### System Components

#### 1. Frontend Components (Next.js 15 + React 19)

**Agent Builder UI**
- Agent creation and configuration forms
- Tool selection and configuration
- Prompt template editor with Monaco Editor
- Template library browser
- Agent testing panel with real-time streaming

**Workflow Designer**
- React Flow-based visual canvas
- Drag-and-drop agent and block nodes
- Connection validation and edge creation
- Conditional branch and loop configuration
- Workflow validation and compilation

**Block Library**
- Block browser with search and filtering
- Block editor for creating custom blocks
- Block testing interface
- Composite block designer
- Block marketplace integration

**Knowledgebase Manager**
- Document upload and processing
- Knowledgebase creation and configuration
- Document viewer and search
- Version history and rollback
- Permission management

**Execution Monitor**
- Real-time execution dashboard
- Execution trace viewer with step-by-step details
- Performance metrics and charts
- Error analysis and debugging tools
- Resource utilization monitoring

**Variables Manager**
- Variable editor with scope selection
- Secret management with encryption
- Variable hierarchy visualization
- Bulk import/export
- Usage tracking

#### 2. Backend Services (FastAPI)

**AgentService**
```python
class AgentService:
    """Service for managing agents"""
    
    def create_agent(self, user_id: str, agent_data: AgentCreate) -> Agent
    def get_agent(self, agent_id: str) -> Agent
    def update_agent(self, agent_id: str, agent_data: AgentUpdate) -> Agent
    def delete_agent(self, agent_id: str) -> bool
    def list_agents(self, user_id: str, filters: AgentFilters) -> List[Agent]
    def clone_agent(self, agent_id: str, user_id: str) -> Agent
    def export_agent(self, agent_id: str) -> dict
    def import_agent(self, user_id: str, agent_data: dict) -> Agent
```

**BlockService**
```python
class BlockService:
    """Service for managing blocks"""
    
    def create_block(self, user_id: str, block_data: BlockCreate) -> Block
    def get_block(self, block_id: str) -> Block
    def update_block(self, block_id: str, block_data: BlockUpdate) -> Block
    def delete_block(self, block_id: str) -> bool
    def list_blocks(self, filters: BlockFilters) -> List[Block]
    def test_block(self, block_id: str, test_input: dict) -> BlockTestResult
    def create_composite_block(self, user_id: str, workflow: dict) -> Block
```

**WorkflowService**
```python
class WorkflowService:
    """Service for managing workflows"""
    
    def create_workflow(self, user_id: str, workflow_data: WorkflowCreate) -> Workflow
    def get_workflow(self, workflow_id: str) -> Workflow
    def update_workflow(self, workflow_id: str, workflow_data: WorkflowUpdate) -> Workflow
    def delete_workflow(self, workflow_id: str) -> bool
    def compile_workflow(self, workflow_id: str) -> StateGraph
    def validate_workflow(self, workflow_data: dict) -> ValidationResult
```

**KnowledgebaseService**
```python
class KnowledgebaseService:
    """Service for managing knowledgebases"""
    
    def create_knowledgebase(self, user_id: str, kb_data: KnowledgebaseCreate) -> Knowledgebase
    def add_documents(self, kb_id: str, documents: List[UploadFile]) -> List[Document]
    def search_knowledgebase(self, kb_id: str, query: str, top_k: int) -> List[SearchResult]
    def create_version(self, kb_id: str) -> KnowledgebaseVersion
    def rollback_version(self, kb_id: str, version_id: str) -> bool
```

**VariableService**
```python
class VariableService:
    """Service for managing variables and secrets"""
    
    def create_variable(self, user_id: str, var_data: VariableCreate) -> Variable
    def get_variable(self, var_name: str, scope: VariableScope, context: dict) -> Any
    def update_variable(self, var_id: str, var_data: VariableUpdate) -> Variable
    def delete_variable(self, var_id: str) -> bool
    def resolve_variables(self, template: str, context: dict) -> str
```

**ExecutionService**
```python
class ExecutionService:
    """Service for executing agents and workflows"""
    
    async def execute_agent(
        self, 
        agent_id: str, 
        input_data: dict, 
        context: ExecutionContext
    ) -> AsyncGenerator[AgentStep, None]
    
    async def execute_workflow(
        self, 
        workflow_id: str, 
        input_data: dict, 
        context: ExecutionContext
    ) -> AsyncGenerator[AgentStep, None]
    
    def get_execution(self, execution_id: str) -> Execution
    def list_executions(self, filters: ExecutionFilters) -> List[Execution]
    def cancel_execution(self, execution_id: str) -> bool
    def replay_execution(self, execution_id: str) -> str
```



#### 3. Data Models (SQLAlchemy ORM)

**Core Agent Models**
```python
class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    agent_type = Column(String, nullable=False)  # custom, template_based
    template_id = Column(String, ForeignKey("agent_templates.id"))
    llm_provider = Column(String, nullable=False)
    llm_model = Column(String, nullable=False)
    prompt_template_id = Column(String, ForeignKey("prompt_templates.id"))
    configuration = Column(JSON)  # Agent-specific config
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    versions = relationship("AgentVersion", back_populates="agent")
    tools = relationship("AgentTool", back_populates="agent")
    knowledgebases = relationship("AgentKnowledgebase", back_populates="agent")
    executions = relationship("AgentExecution", back_populates="agent")

class AgentVersion(Base):
    __tablename__ = "agent_versions"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    version_number = Column(String, nullable=False)  # Semantic versioning
    configuration = Column(JSON)  # Snapshot of agent config
    change_description = Column(Text)
    created_by = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="versions")

class AgentTool(Base):
    __tablename__ = "agent_tools"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    configuration = Column(JSON)  # Tool-specific config
    order = Column(Integer)  # Execution order
    
    agent = relationship("Agent", back_populates="tools")
    tool = relationship("Tool")

class Tool(Base):
    __tablename__ = "tools"
    
    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(Text)
    category = Column(String)  # vector_search, web_search, database, etc.
    input_schema = Column(JSON)  # JSON Schema for inputs
    output_schema = Column(JSON)  # JSON Schema for outputs
    implementation_type = Column(String)  # langchain, custom, builtin
    implementation_ref = Column(String)  # Reference to implementation
    requires_auth = Column(Boolean, default=False)
    is_builtin = Column(Boolean, default=False)
```

**Block Models**
```python
class Block(Base):
    __tablename__ = "blocks"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    block_type = Column(String, nullable=False)  # llm, tool, logic, composite
    input_schema = Column(JSON)
    output_schema = Column(JSON)
    configuration = Column(JSON)
    implementation = Column(Text)  # Code or config
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    versions = relationship("BlockVersion", back_populates="block")
    test_cases = relationship("BlockTestCase", back_populates="block")

class BlockVersion(Base):
    __tablename__ = "block_versions"
    
    id = Column(String, primary_key=True)
    block_id = Column(String, ForeignKey("blocks.id"), nullable=False)
    version_number = Column(String, nullable=False)
    configuration = Column(JSON)
    implementation = Column(Text)
    is_breaking_change = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    block = relationship("Block", back_populates="versions")

class BlockDependency(Base):
    __tablename__ = "block_dependencies"
    
    id = Column(String, primary_key=True)
    parent_block_id = Column(String, ForeignKey("blocks.id"), nullable=False)
    child_block_id = Column(String, ForeignKey("blocks.id"), nullable=False)
    version_constraint = Column(String)  # Semantic version constraint
```

**Workflow Models**
```python
class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    graph_definition = Column(JSON)  # LangGraph StateGraph definition
    compiled_graph = Column(LargeBinary)  # Pickled compiled graph (cached)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    executions = relationship("WorkflowExecution", back_populates="workflow")

class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    node_type = Column(String, nullable=False)  # agent, block, control
    node_ref_id = Column(String)  # Reference to agent_id or block_id
    position_x = Column(Float)
    position_y = Column(Float)
    configuration = Column(JSON)

class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"
    
    id = Column(String, primary_key=True)
    workflow_id = Column(String, ForeignKey("workflows.id"), nullable=False)
    source_node_id = Column(String, ForeignKey("workflow_nodes.id"), nullable=False)
    target_node_id = Column(String, ForeignKey("workflow_nodes.id"), nullable=False)
    edge_type = Column(String)  # normal, conditional
    condition = Column(Text)  # Python expression for conditional edges
```

**Knowledgebase Models**
```python
class Knowledgebase(Base):
    __tablename__ = "knowledgebases"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    milvus_collection_name = Column(String, unique=True, nullable=False)
    embedding_model = Column(String, nullable=False)
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    documents = relationship("KnowledgebaseDocument", back_populates="knowledgebase")
    versions = relationship("KnowledgebaseVersion", back_populates="knowledgebase")

class KnowledgebaseDocument(Base):
    __tablename__ = "knowledgebase_documents"
    
    id = Column(String, primary_key=True)
    knowledgebase_id = Column(String, ForeignKey("knowledgebases.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    removed_at = Column(DateTime, nullable=True)
    
    knowledgebase = relationship("Knowledgebase", back_populates="documents")
    document = relationship("Document")

class KnowledgebaseVersion(Base):
    __tablename__ = "knowledgebase_versions"
    
    id = Column(String, primary_key=True)
    knowledgebase_id = Column(String, ForeignKey("knowledgebases.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    document_snapshot = Column(JSON)  # List of document IDs
    created_at = Column(DateTime, default=datetime.utcnow)
    
    knowledgebase = relationship("Knowledgebase", back_populates="versions")

class AgentKnowledgebase(Base):
    __tablename__ = "agent_knowledgebases"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    knowledgebase_id = Column(String, ForeignKey("knowledgebases.id"), nullable=False)
    priority = Column(Integer, default=0)  # For ranking multiple KBs
    
    agent = relationship("Agent", back_populates="knowledgebases")
    knowledgebase = relationship("Knowledgebase")
```



**Variable Models**
```python
class Variable(Base):
    __tablename__ = "variables"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    scope = Column(String, nullable=False)  # global, workspace, user, agent
    scope_id = Column(String)  # ID of workspace, user, or agent
    value_type = Column(String, nullable=False)  # string, number, boolean, json
    value = Column(Text)  # Stored as string, parsed based on type
    is_secret = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        UniqueConstraint('name', 'scope', 'scope_id', name='uq_variable_scope'),
    )

class Secret(Base):
    __tablename__ = "secrets"
    
    id = Column(String, primary_key=True)
    variable_id = Column(String, ForeignKey("variables.id"), nullable=False)
    encrypted_value = Column(Text, nullable=False)  # AES-256 encrypted
    encryption_key_id = Column(String)  # Key rotation support
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Execution Models**
```python
class AgentExecution(Base):
    __tablename__ = "agent_executions"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_id = Column(String)
    input_data = Column(JSON)
    output_data = Column(JSON)
    execution_context = Column(JSON)
    status = Column(String, nullable=False)  # running, completed, failed, timeout
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Integer)
    
    agent = relationship("Agent", back_populates="executions")
    steps = relationship("ExecutionStep", back_populates="execution")
    metrics = relationship("ExecutionMetrics", back_populates="execution")

class ExecutionStep(Base):
    __tablename__ = "execution_steps"
    
    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("agent_executions.id"), nullable=False)
    step_number = Column(Integer, nullable=False)
    step_type = Column(String, nullable=False)  # thought, action, observation, etc.
    content = Column(Text)
    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    execution = relationship("AgentExecution", back_populates="steps")

class ExecutionMetrics(Base):
    __tablename__ = "execution_metrics"
    
    id = Column(String, primary_key=True)
    execution_id = Column(String, ForeignKey("agent_executions.id"), nullable=False)
    llm_call_count = Column(Integer, default=0)
    llm_total_tokens = Column(Integer, default=0)
    llm_prompt_tokens = Column(Integer, default=0)
    llm_completion_tokens = Column(Integer, default=0)
    tool_call_count = Column(Integer, default=0)
    tool_total_duration_ms = Column(Integer, default=0)
    cache_hit_count = Column(Integer, default=0)
    cache_miss_count = Column(Integer, default=0)
    
    execution = relationship("AgentExecution", back_populates="metrics")

class ExecutionSchedule(Base):
    __tablename__ = "execution_schedules"
    
    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    cron_expression = Column(String, nullable=False)
    timezone = Column(String, default="UTC")
    input_data = Column(JSON)
    is_active = Column(Boolean, default=True)
    last_execution_at = Column(DateTime)
    next_execution_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Permission Models**
```python
class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    resource_type = Column(String, nullable=False)  # agent, block, workflow, knowledgebase
    resource_id = Column(String, nullable=False)
    action = Column(String, nullable=False)  # read, write, execute, delete, share, admin
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(String, ForeignKey("users.id"))
    
    __table_args__ = (
        UniqueConstraint('user_id', 'resource_type', 'resource_id', 'action', 
                        name='uq_permission'),
    )

class ResourceShare(Base):
    __tablename__ = "resource_shares"
    
    id = Column(String, primary_key=True)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    share_token = Column(String, unique=True, nullable=False)
    permissions = Column(JSON)  # List of allowed actions
    expires_at = Column(DateTime)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    resource_type = Column(String)
    resource_id = Column(String)
    details = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
```



## Components and Interfaces

### 1. LangGraph Workflow Execution Engine

The execution engine compiles and executes agent workflows using LangGraph.

**WorkflowExecutor Class**
```python
class WorkflowExecutor:
    """Executes agent workflows using LangGraph"""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        memory_manager: MemoryManager,
        tool_registry: ToolRegistry,
        cache: Redis
    ):
        self.llm_manager = llm_manager
        self.memory_manager = memory_manager
        self.tool_registry = tool_registry
        self.cache = cache
        self.compiled_graphs: LRUCache = LRUCache(maxsize=100)
    
    async def compile_workflow(self, workflow: Workflow) -> StateGraph:
        """Compile workflow definition to LangGraph StateGraph"""
        # Check cache first
        cache_key = f"compiled_graph:{workflow.id}:{workflow.updated_at}"
        if cache_key in self.compiled_graphs:
            return self.compiled_graphs[cache_key]
        
        # Create StateGraph
        graph = StateGraph(dict)
        
        # Add nodes from workflow definition
        for node in workflow.graph_definition["nodes"]:
            if node["type"] == "agent":
                graph.add_node(node["id"], self._create_agent_node(node))
            elif node["type"] == "block":
                graph.add_node(node["id"], self._create_block_node(node))
            elif node["type"] == "control":
                graph.add_node(node["id"], self._create_control_node(node))
        
        # Add edges
        for edge in workflow.graph_definition["edges"]:
            if edge["type"] == "normal":
                graph.add_edge(edge["source"], edge["target"])
            elif edge["type"] == "conditional":
                graph.add_conditional_edges(
                    edge["source"],
                    self._create_condition_function(edge["condition"]),
                    edge["branches"]
                )
        
        # Set entry and exit points
        graph.set_entry_point(workflow.graph_definition["entry_point"])
        
        # Compile
        compiled = graph.compile()
        
        # Cache compiled graph
        self.compiled_graphs[cache_key] = compiled
        
        return compiled
    
    async def execute_workflow(
        self,
        workflow: Workflow,
        input_data: dict,
        context: ExecutionContext
    ) -> AsyncGenerator[AgentStep, None]:
        """Execute workflow and stream results"""
        # Compile workflow
        graph = await self.compile_workflow(workflow)
        
        # Initialize state
        initial_state = {
            "input": input_data,
            "context": context.to_dict(),
            "variables": await self._resolve_variables(context),
            "knowledgebases": await self._load_knowledgebases(workflow),
            "steps": [],
            "output": None
        }
        
        # Execute graph with streaming
        async for state in graph.astream(initial_state):
            # Extract new steps
            new_steps = state.get("steps", [])[len(initial_state.get("steps", [])):]
            
            # Yield steps
            for step in new_steps:
                yield AgentStep(**step)
            
            # Update initial state
            initial_state = state
        
        # Yield final output
        if state.get("output"):
            yield AgentStep(
                step_id=f"output_{uuid.uuid4().hex[:8]}",
                type="response",
                content=state["output"],
                timestamp=datetime.now(),
                metadata={"final": True}
            )
    
    def _create_agent_node(self, node_config: dict):
        """Create agent execution node"""
        async def agent_node(state: dict) -> dict:
            agent_id = node_config["agent_id"]
            agent = await self._load_agent(agent_id)
            
            # Execute agent
            result = await self._execute_agent(agent, state)
            
            # Update state
            state["steps"].append({
                "step_id": f"agent_{uuid.uuid4().hex[:8]}",
                "type": "agent_execution",
                "content": f"Executed agent: {agent.name}",
                "timestamp": datetime.now(),
                "metadata": {"agent_id": agent_id, "result": result}
            })
            
            # Store result in state
            state[f"agent_{agent_id}_output"] = result
            
            return state
        
        return agent_node
    
    def _create_block_node(self, node_config: dict):
        """Create block execution node"""
        async def block_node(state: dict) -> dict:
            block_id = node_config["block_id"]
            block = await self._load_block(block_id)
            
            # Prepare input from state
            block_input = self._map_block_input(block, state, node_config)
            
            # Execute block
            result = await self._execute_block(block, block_input)
            
            # Update state
            state["steps"].append({
                "step_id": f"block_{uuid.uuid4().hex[:8]}",
                "type": "block_execution",
                "content": f"Executed block: {block.name}",
                "timestamp": datetime.now(),
                "metadata": {"block_id": block_id, "result": result}
            })
            
            # Store result in state
            state[f"block_{block_id}_output"] = result
            
            return state
        
        return block_node
    
    def _create_condition_function(self, condition: str):
        """Create condition evaluation function"""
        def condition_fn(state: dict) -> str:
            # Safely evaluate condition
            try:
                # Create safe evaluation context
                eval_context = {
                    "state": state,
                    "output": state.get("output"),
                    **state.get("variables", {})
                }
                
                # Evaluate condition
                result = eval(condition, {"__builtins__": {}}, eval_context)
                
                return str(result)
            except Exception as e:
                logger.error(f"Condition evaluation failed: {e}")
                return "error"
        
        return condition_fn
```

### 2. Block Execution System

**BlockExecutor Class**
```python
class BlockExecutor:
    """Executes individual blocks"""
    
    def __init__(
        self,
        llm_manager: LLMManager,
        tool_registry: ToolRegistry
    ):
        self.llm_manager = llm_manager
        self.tool_registry = tool_registry
    
    async def execute_block(
        self,
        block: Block,
        input_data: dict,
        context: dict
    ) -> dict:
        """Execute a block based on its type"""
        if block.block_type == "llm":
            return await self._execute_llm_block(block, input_data, context)
        elif block.block_type == "tool":
            return await self._execute_tool_block(block, input_data, context)
        elif block.block_type == "logic":
            return await self._execute_logic_block(block, input_data, context)
        elif block.block_type == "composite":
            return await self._execute_composite_block(block, input_data, context)
        else:
            raise ValueError(f"Unknown block type: {block.block_type}")
    
    async def _execute_llm_block(
        self,
        block: Block,
        input_data: dict,
        context: dict
    ) -> dict:
        """Execute LLM block"""
        # Load prompt template
        prompt_template = block.configuration.get("prompt_template")
        
        # Substitute variables
        prompt = self._substitute_variables(prompt_template, input_data, context)
        
        # Call LLM
        response = await self.llm_manager.generate([
            {"role": "user", "content": prompt}
        ])
        
        return {"output": response}
    
    async def _execute_tool_block(
        self,
        block: Block,
        input_data: dict,
        context: dict
    ) -> dict:
        """Execute tool block"""
        # Get tool
        tool_id = block.configuration.get("tool_id")
        tool = self.tool_registry.get_tool(tool_id)
        
        # Prepare tool input
        tool_input = self._map_tool_input(tool, input_data, block.configuration)
        
        # Execute tool
        result = await tool.arun(tool_input)
        
        return {"output": result}
    
    async def _execute_logic_block(
        self,
        block: Block,
        input_data: dict,
        context: dict
    ) -> dict:
        """Execute logic block (custom Python code)"""
        # Get implementation
        code = block.implementation
        
        # Create safe execution environment
        exec_globals = {
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
            }
        }
        
        exec_locals = {
            "input": input_data,
            "context": context,
            "output": None
        }
        
        # Execute code
        exec(code, exec_globals, exec_locals)
        
        return {"output": exec_locals.get("output")}
```



### 3. Tool Registry System

**ToolRegistry Class**
```python
class ToolRegistry:
    """Registry for managing available tools"""
    
    def __init__(self, db: Session):
        self.db = db
        self._tool_cache: Dict[str, BaseTool] = {}
        self._initialize_builtin_tools()
    
    def _initialize_builtin_tools(self):
        """Initialize built-in tools from existing agents"""
        # Vector Search Tool
        self.register_tool(
            tool_id="vector_search",
            name="Vector Search",
            description="Search documents using semantic similarity",
            category="search",
            tool_class=VectorSearchTool,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 10},
                    "knowledgebase_ids": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["query"]
            }
        )
        
        # Web Search Tool
        self.register_tool(
            tool_id="web_search",
            name="Web Search",
            description="Search the web using DuckDuckGo",
            category="search",
            tool_class=WebSearchTool,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        )
        
        # Database Query Tool
        self.register_tool(
            tool_id="database_query",
            name="Database Query",
            description="Execute SQL queries on connected databases",
            category="database",
            tool_class=DatabaseQueryTool,
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "database": {"type": "string", "default": "default"}
                },
                "required": ["query"]
            }
        )
        
        # File Operation Tool
        self.register_tool(
            tool_id="file_operation",
            name="File Operation",
            description="Read, write, and manipulate files",
            category="file",
            tool_class=FileOperationTool,
            input_schema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["read", "write", "list"]},
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["operation", "path"]
            }
        )
        
        # HTTP API Call Tool
        self.register_tool(
            tool_id="http_api_call",
            name="HTTP API Call",
            description="Make HTTP requests to external APIs",
            category="api",
            tool_class=HTTPAPICallTool,
            input_schema={
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "url": {"type": "string"},
                    "headers": {"type": "object"},
                    "body": {"type": "object"}
                },
                "required": ["method", "url"]
            }
        )
    
    def register_tool(
        self,
        tool_id: str,
        name: str,
        description: str,
        category: str,
        tool_class: Type[BaseTool],
        input_schema: dict,
        output_schema: dict = None,
        requires_auth: bool = False
    ):
        """Register a new tool"""
        # Create or update tool in database
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            tool = Tool(
                id=tool_id,
                name=name,
                description=description,
                category=category,
                input_schema=input_schema,
                output_schema=output_schema,
                implementation_type="langchain",
                implementation_ref=f"{tool_class.__module__}.{tool_class.__name__}",
                requires_auth=requires_auth,
                is_builtin=True
            )
            self.db.add(tool)
            self.db.commit()
        
        # Cache tool instance
        self._tool_cache[tool_id] = tool_class()
    
    def get_tool(self, tool_id: str) -> BaseTool:
        """Get tool instance"""
        if tool_id in self._tool_cache:
            return self._tool_cache[tool_id]
        
        # Load from database
        tool = self.db.query(Tool).filter(Tool.id == tool_id).first()
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        
        # Instantiate tool
        if tool.implementation_type == "langchain":
            module_name, class_name = tool.implementation_ref.rsplit(".", 1)
            module = importlib.import_module(module_name)
            tool_class = getattr(module, class_name)
            tool_instance = tool_class()
            self._tool_cache[tool_id] = tool_instance
            return tool_instance
        
        raise ValueError(f"Unsupported tool implementation type: {tool.implementation_type}")
    
    def list_tools(self, category: str = None) -> List[Tool]:
        """List available tools"""
        query = self.db.query(Tool)
        if category:
            query = query.filter(Tool.category == category)
        return query.all()
```

### 4. Knowledgebase Management

**KnowledgebaseManager Class**
```python
class KnowledgebaseManager:
    """Manages knowledgebases and document processing"""
    
    def __init__(
        self,
        db: Session,
        milvus_client: MilvusClient,
        embedding_service: EmbeddingService,
        document_processor: DocumentProcessor
    ):
        self.db = db
        self.milvus = milvus_client
        self.embedding = embedding_service
        self.document_processor = document_processor
    
    async def create_knowledgebase(
        self,
        user_id: str,
        name: str,
        description: str,
        embedding_model: str = None
    ) -> Knowledgebase:
        """Create a new knowledgebase"""
        # Generate unique collection name
        collection_name = f"kb_{uuid.uuid4().hex[:16]}"
        
        # Create Milvus collection
        await self.milvus.create_collection(
            collection_name=collection_name,
            dimension=768,  # Default embedding dimension
            index_type="IVF_FLAT",
            metric_type="COSINE"
        )
        
        # Create knowledgebase record
        kb = Knowledgebase(
            id=str(uuid.uuid4()),
            user_id=user_id,
            name=name,
            description=description,
            milvus_collection_name=collection_name,
            embedding_model=embedding_model or settings.EMBEDDING_MODEL
        )
        self.db.add(kb)
        self.db.commit()
        
        return kb
    
    async def add_documents(
        self,
        knowledgebase_id: str,
        files: List[UploadFile]
    ) -> List[Document]:
        """Add documents to knowledgebase"""
        kb = self.db.query(Knowledgebase).filter(
            Knowledgebase.id == knowledgebase_id
        ).first()
        
        if not kb:
            raise ValueError(f"Knowledgebase not found: {knowledgebase_id}")
        
        documents = []
        
        for file in files:
            # Process document
            doc = await self.document_processor.process_document(file)
            
            # Chunk document
            chunks = await self.document_processor.chunk_document(
                doc,
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap
            )
            
            # Generate embeddings
            embeddings = await self.embedding.embed_documents(
                [chunk.text for chunk in chunks]
            )
            
            # Insert into Milvus
            await self.milvus.insert(
                collection_name=kb.milvus_collection_name,
                data=[
                    {
                        "id": chunk.id,
                        "vector": embedding,
                        "document_id": doc.id,
                        "text": chunk.text,
                        "metadata": chunk.metadata
                    }
                    for chunk, embedding in zip(chunks, embeddings)
                ]
            )
            
            # Create knowledgebase document link
            kb_doc = KnowledgebaseDocument(
                id=str(uuid.uuid4()),
                knowledgebase_id=knowledgebase_id,
                document_id=doc.id
            )
            self.db.add(kb_doc)
            
            documents.append(doc)
        
        self.db.commit()
        
        return documents
    
    async def search_knowledgebase(
        self,
        knowledgebase_id: str,
        query: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """Search knowledgebase"""
        kb = self.db.query(Knowledgebase).filter(
            Knowledgebase.id == knowledgebase_id
        ).first()
        
        if not kb:
            raise ValueError(f"Knowledgebase not found: {knowledgebase_id}")
        
        # Generate query embedding
        query_embedding = await self.embedding.embed_query(query)
        
        # Search Milvus
        results = await self.milvus.search(
            collection_name=kb.milvus_collection_name,
            query_vectors=[query_embedding],
            limit=top_k
        )
        
        return [
            SearchResult(
                chunk_id=result["id"],
                document_id=result["document_id"],
                text=result["text"],
                score=result["score"],
                metadata=result["metadata"]
            )
            for result in results[0]
        ]
```



### 5. Variable Resolution System

**VariableResolver Class**
```python
class VariableResolver:
    """Resolves variables with scope precedence"""
    
    def __init__(self, db: Session, cache: Redis):
        self.db = db
        self.cache = cache
    
    async def resolve_variable(
        self,
        name: str,
        context: ExecutionContext
    ) -> Any:
        """Resolve variable value with scope precedence"""
        # Check cache first
        cache_key = f"var:{name}:{context.agent_id}:{context.user_id}"
        cached_value = await self.cache.get(cache_key)
        if cached_value:
            return json.loads(cached_value)
        
        # Scope precedence: agent > user > workspace > global
        scopes = [
            ("agent", context.agent_id),
            ("user", context.user_id),
            ("workspace", context.workspace_id),
            ("global", None)
        ]
        
        for scope, scope_id in scopes:
            var = self.db.query(Variable).filter(
                Variable.name == name,
                Variable.scope == scope,
                Variable.scope_id == scope_id,
                Variable.deleted_at.is_(None)
            ).first()
            
            if var:
                # Parse value based on type
                value = self._parse_value(var.value, var.value_type)
                
                # Cache for 5 minutes
                await self.cache.setex(
                    cache_key,
                    300,
                    json.dumps(value)
                )
                
                return value
        
        # Variable not found
        raise ValueError(f"Variable not found: {name}")
    
    async def resolve_variables(
        self,
        template: str,
        context: ExecutionContext
    ) -> str:
        """Resolve all variables in a template"""
        # Find all variable references: ${variable_name}
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, template)
        
        # Resolve each variable
        resolved = template
        for var_name in matches:
            try:
                value = await self.resolve_variable(var_name, context)
                resolved = resolved.replace(f"${{{var_name}}}", str(value))
            except ValueError:
                # Variable not found, leave as is or use default
                logger.warning(f"Variable not found: {var_name}")
        
        return resolved
    
    def _parse_value(self, value: str, value_type: str) -> Any:
        """Parse value based on type"""
        if value_type == "string":
            return value
        elif value_type == "number":
            return float(value) if "." in value else int(value)
        elif value_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        elif value_type == "json":
            return json.loads(value)
        else:
            return value

class SecretManager:
    """Manages encrypted secrets"""
    
    def __init__(self, db: Session, encryption_key: str):
        self.db = db
        self.cipher = Fernet(encryption_key.encode())
    
    def encrypt_secret(self, value: str) -> str:
        """Encrypt a secret value"""
        return self.cipher.encrypt(value.encode()).decode()
    
    def decrypt_secret(self, encrypted_value: str) -> str:
        """Decrypt a secret value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    async def get_secret(self, variable_id: str) -> str:
        """Get decrypted secret value"""
        secret = self.db.query(Secret).filter(
            Secret.variable_id == variable_id
        ).first()
        
        if not secret:
            raise ValueError(f"Secret not found for variable: {variable_id}")
        
        return self.decrypt_secret(secret.encrypted_value)
```

## Data Models

### State Management

**ExecutionContext**
```python
@dataclass
class ExecutionContext:
    """Context for agent/workflow execution"""
    execution_id: str
    user_id: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    workspace_id: Optional[str] = None
    session_id: Optional[str] = None
    input_data: dict = field(default_factory=dict)
    variables: dict = field(default_factory=dict)
    knowledgebases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)
```

**AgentStep** (Existing model, extended)
```python
@dataclass
class AgentStep:
    """Represents a step in agent execution"""
    step_id: str
    type: str  # thought, action, observation, response, error, etc.
    content: str
    timestamp: datetime
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "type": self.type,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
```

## Error Handling

### Error Recovery Strategy

1. **Retry Logic**: Use existing RetryHandler with exponential backoff
2. **Fallback Behavior**: Define fallback values or actions for blocks
3. **Error Propagation**: Control whether errors stop execution or continue
4. **Circuit Breaker**: Prevent cascading failures in workflows

**Error Handling Example**
```python
class ErrorHandler:
    """Handles errors in agent/workflow execution"""
    
    def __init__(self, retry_handler: RetryHandler):
        self.retry_handler = retry_handler
    
    async def handle_block_error(
        self,
        block: Block,
        error: Exception,
        context: dict
    ) -> dict:
        """Handle block execution error"""
        # Get error handling config
        error_config = block.configuration.get("error_handling", {})
        
        # Retry if configured
        if error_config.get("retry_enabled", False):
            retry_count = error_config.get("retry_count", 3)
            for attempt in range(retry_count):
                try:
                    # Retry block execution
                    result = await self._execute_block_with_retry(block, context)
                    return result
                except Exception as e:
                    if attempt == retry_count - 1:
                        # All retries exhausted
                        break
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Use fallback if configured
        if error_config.get("fallback_enabled", False):
            fallback_value = error_config.get("fallback_value")
            return {"output": fallback_value}
        
        # Propagate error if configured
        if error_config.get("propagate_error", True):
            raise error
        
        # Skip block
        return {"output": None, "skipped": True}
```

## Testing Strategy

### Unit Tests

1. **Service Layer Tests**: Test each service independently with mocked dependencies
2. **Model Tests**: Test SQLAlchemy models and relationships
3. **Utility Tests**: Test variable resolution, encryption, validation

### Integration Tests

1. **Workflow Execution Tests**: Test end-to-end workflow execution
2. **API Tests**: Test FastAPI endpoints with test database
3. **Database Tests**: Test SQLAlchemy queries and transactions

### E2E Tests

1. **Agent Creation Flow**: Create agent, add tools, test execution
2. **Workflow Designer Flow**: Create workflow, add nodes, execute
3. **Knowledgebase Flow**: Create KB, upload documents, search

**Test Example**
```python
@pytest.mark.asyncio
async def test_agent_execution():
    """Test agent execution with tools"""
    # Create test agent
    agent = await agent_service.create_agent(
        user_id="test_user",
        agent_data=AgentCreate(
            name="Test Agent",
            agent_type="custom",
            llm_provider="ollama",
            llm_model="llama3.1",
            tools=["vector_search"]
        )
    )
    
    # Execute agent
    steps = []
    async for step in execution_service.execute_agent(
        agent_id=agent.id,
        input_data={"query": "What is RAG?"},
        context=ExecutionContext(
            execution_id="test_exec",
            user_id="test_user",
            agent_id=agent.id
        )
    ):
        steps.append(step)
    
    # Verify execution
    assert len(steps) > 0
    assert any(step.type == "response" for step in steps)
```

