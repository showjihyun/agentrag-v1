"""Pydantic schemas for Agent Builder feature."""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


# ============================================================================
# Agent Schemas
# ============================================================================

class ToolConfiguration(BaseModel):
    """Schema for tool configuration."""
    
    tool_id: str = Field(..., description="Tool ID")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Tool-specific configuration"
    )
    order: int = Field(default=0, description="Execution order")


class ContextItem(BaseModel):
    """Schema for context item."""
    
    id: str = Field(..., description="Context item ID")
    type: Literal["file", "folder", "url", "text"] = Field(..., description="Context type")
    name: str = Field(..., description="Context item name")
    value: str = Field(..., description="Context value (path, URL, or text)")
    enabled: bool = Field(default=True, description="Whether context is enabled")


class MCPServerConfig(BaseModel):
    """Schema for MCP server configuration."""
    
    id: str = Field(..., description="MCP server ID")
    name: str = Field(..., description="MCP server name")
    command: str = Field(..., description="Command to run MCP server")
    args: List[str] = Field(default_factory=list, description="Command arguments")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    enabled: bool = Field(default=True, description="Whether MCP server is enabled")


class AgentCreate(BaseModel):
    """Schema for creating a new agent."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    agent_type: Literal["custom", "template_based"] = Field(
        ..., description="Type of agent"
    )
    template_id: Optional[str] = Field(None, description="Template ID if template-based")
    llm_provider: str = Field(..., description="LLM provider (ollama, openai, claude)")
    llm_model: str = Field(..., description="LLM model name")
    prompt_template_id: Optional[str] = Field(None, description="Prompt template ID")
    prompt_template: Optional[str] = Field(None, description="Custom prompt template")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Agent-specific configuration"
    )
    tool_ids: List[str] = Field(
        default_factory=list, description="List of tool IDs to attach (deprecated, use tools)"
    )
    tools: List[ToolConfiguration] = Field(
        default_factory=list, description="List of tools with configurations"
    )
    knowledgebase_ids: List[str] = Field(
        default_factory=list, description="List of knowledgebase IDs to attach"
    )
    context_items: List[ContextItem] = Field(
        default_factory=list, description="List of context items"
    )
    mcp_servers: List[MCPServerConfig] = Field(
        default_factory=list, description="List of MCP server configurations"
    )
    is_public: bool = Field(default=False, description="Whether agent is public")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Research Assistant",
                "description": "An agent that helps with research tasks",
                "agent_type": "custom",
                "llm_provider": "ollama",
                "llm_model": "llama3.1",
                "prompt_template": "You are a helpful research assistant...",
                "tool_ids": ["vector_search", "web_search"],
                "knowledgebase_ids": [],
                "is_public": False
            }
        }
    )


class AgentUpdate(BaseModel):
    """Schema for updating an agent."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    prompt_template_id: Optional[str] = None
    prompt_template: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    tool_ids: Optional[List[str]] = None
    tools: Optional[List[ToolConfiguration]] = None
    knowledgebase_ids: Optional[List[str]] = None
    context_items: Optional[List[ContextItem]] = None
    mcp_servers: Optional[List[MCPServerConfig]] = None
    is_public: Optional[bool] = None


class AgentResponse(BaseModel):
    """Schema for agent response."""
    
    id: str
    user_id: str
    name: str
    description: Optional[str]
    agent_type: str
    template_id: Optional[str]
    llm_provider: str
    llm_model: str
    prompt_template_id: Optional[str]
    configuration: Dict[str, Any]
    context_items: List[Dict[str, Any]] = Field(default_factory=list)
    mcp_servers: List[Dict[str, Any]] = Field(default_factory=list)
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    # Related data
    tools: List[Dict[str, Any]] = Field(default_factory=list)
    knowledgebases: List[Dict[str, Any]] = Field(default_factory=list)
    version_count: int = Field(default=0)
    
    model_config = ConfigDict(from_attributes=True)


class AgentListResponse(BaseModel):
    """Schema for agent list response."""
    
    agents: List[AgentResponse]
    total: int
    limit: int
    offset: int
    
    model_config = ConfigDict(from_attributes=True)


class AgentExportResponse(BaseModel):
    """Schema for agent export response."""
    
    agent: AgentResponse
    export_format: str
    export_data: Dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Block Schemas
# ============================================================================

class BlockCreate(BaseModel):
    """Schema for creating a new block."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Block name")
    description: Optional[str] = Field(None, description="Block description")
    block_type: Literal["llm", "tool", "logic", "composite"] = Field(
        ..., description="Type of block"
    )
    input_schema: Dict[str, Any] = Field(
        ..., description="JSON Schema for block inputs"
    )
    output_schema: Dict[str, Any] = Field(
        ..., description="JSON Schema for block outputs"
    )
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Block configuration"
    )
    implementation: Optional[str] = Field(
        None, description="Block implementation code or config"
    )
    is_public: bool = Field(default=False, description="Whether block is public")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Text Summarizer",
                "description": "Summarizes text using LLM",
                "block_type": "llm",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"}
                    }
                },
                "configuration": {
                    "prompt_template": "Summarize the following text: {text}"
                }
            }
        }
    )


class BlockUpdate(BaseModel):
    """Schema for updating a block."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    configuration: Optional[Dict[str, Any]] = None
    implementation: Optional[str] = None
    is_public: Optional[bool] = None


class BlockResponse(BaseModel):
    """Schema for block response."""
    
    id: str
    user_id: str
    name: str
    description: Optional[str]
    block_type: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    configuration: Dict[str, Any]
    implementation: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    version_count: int = Field(default=0)
    
    model_config = ConfigDict(from_attributes=True)


class BlockListResponse(BaseModel):
    """Schema for block list response."""
    
    blocks: List[BlockResponse]
    total: int
    limit: int
    offset: int
    
    model_config = ConfigDict(from_attributes=True)


class BlockTestInput(BaseModel):
    """Schema for testing a block."""
    
    input_data: Dict[str, Any] = Field(..., description="Input data for block")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Execution context"
    )


class BlockTestRequest(BaseModel):
    """Schema for block test request."""
    
    input_data: Dict[str, Any] = Field(..., description="Input data for block")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Execution context"
    )


class BlockTestResult(BaseModel):
    """Schema for block test result."""
    
    success: bool
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BlockVersionResponse(BaseModel):
    """Schema for block version response."""
    
    id: str
    block_id: str
    version_number: int
    configuration: Dict[str, Any]
    created_at: datetime
    created_by: str
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Workflow Schemas
# ============================================================================

class WorkflowNodeCreate(BaseModel):
    """Schema for workflow node."""
    
    id: str = Field(..., description="Unique node ID")
    node_type: str = Field(
        ..., description="Type of node (start, end, agent, block, tool, ai_agent, condition, etc.)"
    )
    node_ref_id: Optional[str] = Field(
        None, description="Reference to agent_id or block_id"
    )
    position_x: float = Field(..., description="X position on canvas")
    position_y: float = Field(..., description="Y position on canvas")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Node configuration"
    )


class WorkflowEdgeCreate(BaseModel):
    """Schema for workflow edge."""
    
    id: str = Field(..., description="Unique edge ID")
    source_node_id: str = Field(..., description="Source node ID")
    target_node_id: str = Field(..., description="Target node ID")
    edge_type: str = Field(
        default="normal", description="Type of edge (normal, conditional, true, false, custom, etc.)"
    )
    condition: Optional[str] = Field(
        None, description="Python expression for conditional edges"
    )
    source_handle: Optional[str] = Field(
        None, description="Source handle ID"
    )
    target_handle: Optional[str] = Field(
        None, description="Target handle ID"
    )


class WorkflowCreate(BaseModel):
    """Schema for creating a workflow."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    nodes: List[WorkflowNodeCreate] = Field(
        default_factory=list, description="Workflow nodes"
    )
    edges: List[WorkflowEdgeCreate] = Field(
        default_factory=list, description="Workflow edges"
    )
    entry_point: Optional[str] = Field(None, description="Entry node ID (optional for empty workflows)")
    is_public: bool = Field(default=False, description="Whether workflow is public")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Research Workflow",
                "description": "Multi-step research workflow",
                "nodes": [
                    {
                        "id": "node_1",
                        "node_type": "agent",
                        "node_ref_id": "agent_123",
                        "position_x": 100,
                        "position_y": 100,
                        "configuration": {}
                    }
                ],
                "edges": [],
                "entry_point": "node_1"
            }
        }
    )


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: Optional[List[WorkflowNodeCreate]] = None
    edges: Optional[List[WorkflowEdgeCreate]] = None
    entry_point: Optional[str] = None
    is_public: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """Schema for workflow response."""
    
    id: str
    user_id: str
    name: str
    description: Optional[str]
    graph_definition: Dict[str, Any]
    is_public: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowListResponse(BaseModel):
    """Schema for workflow list response."""
    
    workflows: List[WorkflowResponse]
    total: int
    limit: int
    offset: int
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowValidationResult(BaseModel):
    """Schema for workflow validation result."""
    
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class WorkflowCompileResult(BaseModel):
    """Schema for workflow compile result."""
    
    success: bool
    compiled_graph: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ============================================================================
# Knowledgebase Schemas
# ============================================================================

class KnowledgebaseCreate(BaseModel):
    """Schema for creating a knowledgebase."""
    
    name: str = Field(..., min_length=1, max_length=255, description="KB name")
    description: Optional[str] = Field(None, description="KB description")
    embedding_model: Optional[str] = Field(
        None, description="Embedding model to use"
    )
    chunk_size: int = Field(default=500, ge=100, le=2000, description="Chunk size")
    chunk_overlap: int = Field(
        default=50, ge=0, le=500, description="Chunk overlap"
    )
    kg_enabled: Optional[bool] = Field(
        default=False, description="Enable Knowledge Graph features"
    )


class KnowledgebaseUpdate(BaseModel):
    """Schema for updating a knowledgebase."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=500)
    kg_enabled: Optional[bool] = Field(None, description="Enable Knowledge Graph features")


class KnowledgebaseResponse(BaseModel):
    """Schema for knowledgebase response."""
    
    id: str
    user_id: str
    name: str
    description: Optional[str]
    milvus_collection_name: str
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    kg_enabled: Optional[bool] = Field(default=False)
    created_at: datetime
    updated_at: Optional[datetime]
    
    document_count: int = Field(default=0)
    total_size: int = Field(default=0)
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgebaseSearchRequest(BaseModel):
    """Schema for knowledgebase search request."""
    
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(default=10, ge=1, le=100, description="Number of results")


class KnowledgebaseListResponse(BaseModel):
    """Schema for knowledgebase list response."""
    
    knowledgebases: List[KnowledgebaseResponse]
    total: int
    limit: int
    offset: int
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgebaseDocumentResponse(BaseModel):
    """Schema for knowledgebase document response."""
    
    id: str
    knowledgebase_id: str
    filename: str
    file_size: int
    chunk_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgebaseSearchResult(BaseModel):
    """Schema for knowledgebase search result."""
    
    chunk_id: str
    document_id: str
    text: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgebaseSearchResponse(BaseModel):
    """Schema for knowledgebase search response."""
    
    results: List[KnowledgebaseSearchResult]
    total: int
    query: str
    
    model_config = ConfigDict(from_attributes=True)


class KnowledgebaseVersionResponse(BaseModel):
    """Schema for knowledgebase version response."""
    
    id: str
    knowledgebase_id: str
    version_number: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Variable Schemas
# ============================================================================

class VariableCreate(BaseModel):
    """Schema for creating a variable."""
    
    name: str = Field(..., min_length=1, max_length=255, description="Variable name")
    scope: Literal["global", "workspace", "user", "agent"] = Field(
        ..., description="Variable scope"
    )
    scope_id: Optional[str] = Field(None, description="Scope ID (user_id, agent_id)")
    value_type: Literal["string", "number", "boolean", "json"] = Field(
        ..., description="Value type"
    )
    value: str = Field(..., description="Variable value (as string)")
    is_secret: bool = Field(default=False, description="Whether value is secret")


class VariableUpdate(BaseModel):
    """Schema for updating a variable."""
    
    value: Optional[str] = None
    value_type: Optional[Literal["string", "number", "boolean", "json"]] = None


class VariableResponse(BaseModel):
    """Schema for variable response."""
    
    id: str
    name: str
    scope: str
    scope_id: Optional[str]
    value_type: str
    value: str  # Masked if secret
    is_secret: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class VariableListResponse(BaseModel):
    """Schema for variable list response."""
    
    variables: List[VariableResponse]
    total: int
    limit: int
    offset: int
    
    model_config = ConfigDict(from_attributes=True)


class VariableResolveRequest(BaseModel):
    """Schema for variable resolve request."""
    
    template: str = Field(..., description="Template string with variables")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class VariableResolveResponse(BaseModel):
    """Schema for variable resolve response."""
    
    resolved: str
    variables_used: List[str] = Field(default_factory=list)


# ============================================================================
# Execution Schemas
# ============================================================================

class ExecutionContext(BaseModel):
    """Context for agent/workflow execution."""
    
    execution_id: str
    user_id: str
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    workspace_id: Optional[str] = None
    session_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    variables: Dict[str, Any] = Field(default_factory=dict)
    knowledgebases: List[str] = Field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class ExecutionRequest(BaseModel):
    """Schema for execution request."""
    
    input_data: Dict[str, Any] = Field(..., description="Input data for execution")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Execution variables"
    )


class ExecutionResponse(BaseModel):
    """Schema for execution response."""
    
    id: str
    agent_id: Optional[str]
    workflow_id: Optional[str]
    user_id: str
    session_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    execution_context: Dict[str, Any]
    status: str
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    
    model_config = ConfigDict(from_attributes=True)


class ExecutionFilters(BaseModel):
    """Schema for execution filters."""
    
    status: Optional[Literal["running", "completed", "failed", "timeout"]] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


# ============================================================================
# Permission Schemas
# ============================================================================

class PermissionCreate(BaseModel):
    """Schema for creating a permission."""
    
    user_id: str = Field(..., description="User ID to grant permission to")
    resource_type: Literal["agent", "block", "workflow", "knowledgebase"] = Field(
        ..., description="Resource type"
    )
    resource_id: str = Field(..., description="Resource ID")
    action: Literal["read", "write", "execute", "delete", "share", "admin"] = Field(
        ..., description="Action to permit"
    )


class PermissionResponse(BaseModel):
    """Schema for permission response."""
    
    id: str
    user_id: str
    resource_type: str
    resource_id: str
    action: str
    granted_at: datetime
    granted_by: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class ResourceShareCreate(BaseModel):
    """Schema for creating a resource share."""
    
    resource_type: Literal["agent", "block", "workflow", "knowledgebase"] = Field(
        ..., description="Resource type"
    )
    resource_id: str = Field(..., description="Resource ID")
    permissions: List[str] = Field(..., description="List of allowed actions")
    expires_at: Optional[datetime] = Field(None, description="Expiration time")


class ResourceShareResponse(BaseModel):
    """Schema for resource share response."""
    
    id: str
    resource_type: str
    resource_id: str
    share_token: str
    permissions: List[str]
    expires_at: Optional[datetime]
    created_by: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Block System Schemas (Sim Integration)
# ============================================================================

class SubBlockConfig(BaseModel):
    """Schema for SubBlock configuration (UI components within blocks)."""
    
    id: str = Field(..., description="SubBlock ID")
    type: Literal[
        "short-input", "long-input", "dropdown", "code", 
        "oauth-input", "checkbox", "number-input", "file-upload"
    ] = Field(..., description="SubBlock type")
    title: str = Field(..., description="SubBlock title/label")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    default_value: Optional[Any] = Field(None, description="Default value")
    required: bool = Field(default=False, description="Whether field is required")
    options: Optional[List[str]] = Field(None, description="Options for dropdown")
    language: Optional[str] = Field(None, description="Language for code editor")
    condition: Optional[Dict[str, Any]] = Field(
        None, description="Conditional rendering logic"
    )
    validation: Optional[Dict[str, Any]] = Field(
        None, description="Validation rules"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "model",
                "type": "dropdown",
                "title": "Model",
                "required": True,
                "options": ["gpt-4", "gpt-3.5-turbo", "claude-3"],
                "default_value": "gpt-4"
            }
        }
    )


class BlockConfig(BaseModel):
    """Schema for Block configuration (registry definition)."""
    
    type: str = Field(..., description="Block type identifier")
    name: str = Field(..., description="Block display name")
    description: str = Field(..., description="Block description")
    category: Literal["blocks", "tools", "triggers"] = Field(
        ..., description="Block category"
    )
    sub_blocks: List[SubBlockConfig] = Field(
        default_factory=list, description="SubBlock configurations"
    )
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Input schema"
    )
    outputs: Dict[str, Any] = Field(
        default_factory=dict, description="Output schema"
    )
    bg_color: str = Field(default="#3B82F6", description="Background color")
    icon: str = Field(default="cube", description="Icon name")
    auth_mode: Optional[Literal["oauth", "api_key", "none"]] = Field(
        None, description="Authentication mode"
    )
    docs_link: Optional[str] = Field(None, description="Documentation link")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "openai",
                "name": "OpenAI",
                "description": "Call OpenAI API",
                "category": "tools",
                "sub_blocks": [
                    {
                        "id": "model",
                        "type": "dropdown",
                        "title": "Model",
                        "required": True,
                        "options": ["gpt-4", "gpt-3.5-turbo"]
                    }
                ],
                "inputs": {"prompt": {"type": "string"}},
                "outputs": {"response": {"type": "string"}},
                "bg_color": "#10A37F",
                "icon": "openai"
            }
        }
    )


class AgentBlockCreate(BaseModel):
    """Schema for creating an agent block."""
    
    type: str = Field(..., description="Block type")
    name: str = Field(..., min_length=1, max_length=255, description="Block name")
    position_x: float = Field(..., description="X position on canvas")
    position_y: float = Field(..., description="Y position on canvas")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Block configuration"
    )
    sub_blocks: Dict[str, Any] = Field(
        default_factory=dict, description="SubBlock values"
    )
    inputs: Dict[str, Any] = Field(
        default_factory=dict, description="Input schema"
    )
    outputs: Dict[str, Any] = Field(
        default_factory=dict, description="Output schema"
    )
    enabled: bool = Field(default=True, description="Whether block is enabled")


class AgentBlockUpdate(BaseModel):
    """Schema for updating an agent block."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    sub_blocks: Optional[Dict[str, Any]] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class AgentBlockResponse(BaseModel):
    """Schema for agent block response."""
    
    id: str
    workflow_id: str
    type: str
    name: str
    position_x: float
    position_y: float
    config: Dict[str, Any]
    sub_blocks: Dict[str, Any]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    enabled: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AgentEdgeCreate(BaseModel):
    """Schema for creating an agent edge."""
    
    source_block_id: str = Field(..., description="Source block ID")
    target_block_id: str = Field(..., description="Target block ID")
    source_handle: Optional[str] = Field(None, description="Source handle")
    target_handle: Optional[str] = Field(None, description="Target handle")


class AgentEdgeResponse(BaseModel):
    """Schema for agent edge response."""
    
    id: str
    workflow_id: str
    source_block_id: str
    target_block_id: str
    source_handle: Optional[str]
    target_handle: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowScheduleCreate(BaseModel):
    """Schema for creating a workflow schedule."""
    
    cron_expression: str = Field(..., description="Cron expression")
    timezone: str = Field(default="UTC", description="Timezone")
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Default input data"
    )
    is_active: bool = Field(default=True, description="Whether schedule is active")


class WorkflowScheduleUpdate(BaseModel):
    """Schema for updating a workflow schedule."""
    
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WorkflowScheduleResponse(BaseModel):
    """Schema for workflow schedule response."""
    
    id: str
    workflow_id: str
    cron_expression: str
    timezone: str
    input_data: Dict[str, Any]
    is_active: bool
    last_execution_at: Optional[datetime]
    next_execution_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowWebhookCreate(BaseModel):
    """Schema for creating a workflow webhook."""
    
    webhook_path: Optional[str] = Field(
        None, description="Custom webhook path (auto-generated if not provided)"
    )
    webhook_secret: Optional[str] = Field(None, description="Webhook secret")
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(
        default="POST", description="HTTP method"
    )
    is_active: bool = Field(default=True, description="Whether webhook is active")


class WorkflowWebhookUpdate(BaseModel):
    """Schema for updating a workflow webhook."""
    
    webhook_secret: Optional[str] = None
    http_method: Optional[Literal["GET", "POST", "PUT", "PATCH", "DELETE"]] = None
    is_active: Optional[bool] = None


class WorkflowWebhookResponse(BaseModel):
    """Schema for workflow webhook response."""
    
    id: str
    workflow_id: str
    webhook_path: str
    webhook_secret: Optional[str]
    http_method: str
    is_active: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowSubflowCreate(BaseModel):
    """Schema for creating a workflow subflow."""
    
    parent_block_id: str = Field(..., description="Parent block ID")
    subflow_type: Literal["loop", "parallel"] = Field(..., description="Subflow type")
    configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Subflow configuration"
    )


class WorkflowSubflowUpdate(BaseModel):
    """Schema for updating a workflow subflow."""
    
    configuration: Optional[Dict[str, Any]] = None


class WorkflowSubflowResponse(BaseModel):
    """Schema for workflow subflow response."""
    
    id: str
    workflow_id: str
    parent_block_id: str
    subflow_type: str
    configuration: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WorkflowExecutionLogResponse(BaseModel):
    """Schema for workflow execution log response."""
    
    id: str
    workflow_id: str
    execution_id: str
    trigger: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_ms: Optional[int]
    execution_data: Dict[str, Any]
    cost: Optional[Dict[str, Any]]
    files: Optional[Dict[str, Any]]
    status: str
    error_message: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BlockExecutionRequest(BaseModel):
    """Schema for block execution request."""
    
    inputs: Dict[str, Any] = Field(..., description="Block inputs")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Execution context"
    )


class BlockExecutionResponse(BaseModel):
    """Schema for block execution response."""
    
    success: bool
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowValidationError(BaseModel):
    """Schema for workflow validation error."""
    
    block_id: Optional[str] = None
    edge_id: Optional[str] = None
    error_type: str
    message: str
    severity: Literal["error", "warning"]


class WorkflowValidationResponse(BaseModel):
    """Schema for workflow validation response."""
    
    is_valid: bool
    errors: List[WorkflowValidationError] = Field(default_factory=list)
    warnings: List[WorkflowValidationError] = Field(default_factory=list)



class WorkflowCompileResult(BaseModel):
    """Schema for workflow compile result."""
    
    success: bool
    compiled_graph: Optional[Dict[str, Any]] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    compilation_time_ms: int = 0
    
    model_config = ConfigDict(from_attributes=True)



# ============================================================================
# API Key Management Schemas
# ============================================================================

class APIKeyCreate(BaseModel):
    """Schema for creating a new API key."""
    
    service_name: str = Field(..., description="Service identifier (e.g., 'youtube', 'openai')")
    service_display_name: str = Field(..., description="Service display name")
    api_key: str = Field(..., description="API key value (will be encrypted)")
    description: Optional[str] = Field(None, description="Optional description")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "service_name": "youtube",
                "service_display_name": "YouTube Data API",
                "api_key": "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "description": "API key for YouTube video search"
            }
        }
    )


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""
    
    api_key: Optional[str] = Field(None, description="New API key value")
    description: Optional[str] = Field(None, description="Updated description")
    is_active: Optional[bool] = Field(None, description="Active status")


class APIKeyResponse(BaseModel):
    """Schema for API key response (without exposing the actual key)."""
    
    id: str
    service_name: str
    service_display_name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    usage_count: int
    # Note: encrypted_api_key is NOT included for security
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyListResponse(BaseModel):
    """Schema for API key list response."""
    
    api_keys: List[APIKeyResponse]
    total: int


class APIKeyTestResponse(BaseModel):
    """Schema for API key test response."""
    
    success: bool
    message: str
    service_name: str
    details: Optional[Dict[str, Any]] = None


# ============================================================================
# Knowledge Graph Schemas
# ============================================================================

class KnowledgeGraphCreateRequest(BaseModel):
    """Schema for creating a knowledge graph."""
    
    knowledgebase_id: str = Field(..., description="Knowledgebase ID")
    name: str = Field(..., min_length=1, max_length=255, description="Knowledge graph name")
    description: Optional[str] = Field(None, description="Knowledge graph description")
    auto_extraction_enabled: bool = Field(default=True, description="Enable automatic entity/relationship extraction")
    entity_extraction_model: str = Field(default="spacy_en_core_web_sm", description="Entity extraction model")
    relation_extraction_model: str = Field(default="rebel_large", description="Relationship extraction model")


class KnowledgeGraphResponse(BaseModel):
    """Schema for knowledge graph response."""
    
    id: str
    knowledgebase_id: str
    name: str
    description: Optional[str]
    auto_extraction_enabled: bool
    entity_extraction_model: str
    relation_extraction_model: str
    entity_count: int
    relationship_count: int
    processing_status: str
    processing_error: Optional[str]
    last_processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class KGEntitySearchRequest(BaseModel):
    """Schema for entity search request."""
    
    query: Optional[str] = Field(None, description="Search query")
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")


class KGEntityResponse(BaseModel):
    """Schema for knowledge graph entity response."""
    
    id: str
    name: str
    canonical_name: str
    entity_type: str
    description: Optional[str]
    confidence_score: float
    mention_count: int
    relationship_count: int
    properties: Dict[str, Any]
    aliases: List[str]


class KGEntitySearchResponse(BaseModel):
    """Schema for entity search response."""
    
    entities: List[KGEntityResponse]
    total_count: int
    query: Optional[str]
    entity_types: Optional[List[str]]


class KGRelationshipSearchRequest(BaseModel):
    """Schema for relationship search request."""
    
    entity_id: Optional[str] = Field(None, description="Filter by entity ID")
    relation_types: Optional[List[str]] = Field(None, description="Filter by relationship types")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")


class KGRelationshipResponse(BaseModel):
    """Schema for knowledge graph relationship response."""
    
    id: str
    relation_type: str
    relation_label: Optional[str]
    description: Optional[str]
    confidence_score: float
    mention_count: int
    is_bidirectional: bool
    properties: Dict[str, Any]
    source_entity: Dict[str, Any]
    target_entity: Dict[str, Any]
    temporal_start: Optional[str]
    temporal_end: Optional[str]


class KGRelationshipSearchResponse(BaseModel):
    """Schema for relationship search response."""
    
    relationships: List[KGRelationshipResponse]
    total_count: int
    entity_id: Optional[str]
    relation_types: Optional[List[str]]


class KGPathFindingRequest(BaseModel):
    """Schema for path finding request."""
    
    source_entity_id: str = Field(..., description="Source entity ID")
    target_entity_id: str = Field(..., description="Target entity ID")
    max_depth: int = Field(default=3, ge=1, le=5, description="Maximum path depth")


class KGPathFindingResponse(BaseModel):
    """Schema for path finding response."""
    
    paths: List[List[Dict[str, Any]]]
    source_entity_id: str
    target_entity_id: str
    max_depth: int


class KGSubgraphRequest(BaseModel):
    """Schema for subgraph request."""
    
    entity_ids: List[str] = Field(..., min_items=1, description="Entity IDs to include in subgraph")
    depth: int = Field(default=1, ge=1, le=3, description="Expansion depth")


class KGSubgraphResponse(BaseModel):
    """Schema for subgraph response."""
    
    entities: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]
    entity_ids: List[str]
    depth: int


class KGExtractionJobResponse(BaseModel):
    """Schema for extraction job response."""
    
    id: str
    knowledge_graph_id: str
    job_type: str
    status: str
    documents_processed: int
    documents_total: int
    entities_extracted: int
    relationships_extracted: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    estimated_completion: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class KGStatsResponse(BaseModel):
    """Schema for knowledge graph statistics response."""
    
    entity_count: int
    relationship_count: int
    entity_types: List[Dict[str, Any]]
    relationship_types: List[Dict[str, Any]]
    last_processed_at: Optional[datetime]
    processing_status: str


class EntityTypeResponse(BaseModel):
    """Schema for entity type response."""
    
    value: str
    label: str


class RelationTypeResponse(BaseModel):
    """Schema for relation type response."""
    
    value: str
    label: str