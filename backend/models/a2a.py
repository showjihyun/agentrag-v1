"""
Google A2A (Agent-to-Agent) Protocol Models.

A2A 프로토콜은 서로 다른 프레임워크, 언어, 벤더로 구축된 AI 에이전트 간의
통신과 상호운용성을 위한 개방형 표준입니다.

Reference: https://a2a-protocol.org/latest/specification/
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class TaskState(str, Enum):
    """Task lifecycle states."""
    UNSPECIFIED = "unspecified"
    SUBMITTED = "submitted"
    WORKING = "working"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INPUT_REQUIRED = "input_required"
    REJECTED = "rejected"
    AUTH_REQUIRED = "auth_required"


class Role(str, Enum):
    """Message sender role."""
    UNSPECIFIED = "unspecified"
    USER = "user"
    AGENT = "agent"


class ProtocolBinding(str, Enum):
    """Supported protocol bindings."""
    JSONRPC = "JSONRPC"
    GRPC = "GRPC"
    HTTP_JSON = "HTTP+JSON"


# ============================================================================
# Part Types (Content Units)
# ============================================================================

class FilePart(BaseModel):
    """File content representation."""
    file_with_uri: Optional[str] = Field(None, alias="fileWithUri", description="URL pointing to file content")
    file_with_bytes: Optional[str] = Field(None, alias="fileWithBytes", description="Base64-encoded file content")
    media_type: Optional[str] = Field(None, alias="mediaType", description="MIME type (e.g., 'application/pdf')")
    name: Optional[str] = Field(None, description="File name")
    
    model_config = ConfigDict(populate_by_name=True)


class DataPart(BaseModel):
    """Structured data content."""
    data: Dict[str, Any] = Field(..., description="JSON object containing arbitrary data")


class Part(BaseModel):
    """Content unit within a Message or Artifact."""
    text: Optional[str] = Field(None, description="Text content")
    file: Optional[FilePart] = Field(None, description="File content")
    data: Optional[DataPart] = Field(None, description="Structured data content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


# ============================================================================
# Message
# ============================================================================

class Message(BaseModel):
    """Communication unit between client and server."""
    message_id: str = Field(..., alias="messageId", description="Unique message identifier")
    context_id: Optional[str] = Field(None, alias="contextId", description="Context identifier")
    task_id: Optional[str] = Field(None, alias="taskId", description="Associated task ID")
    role: Role = Field(..., description="Sender role (user/agent)")
    parts: List[Part] = Field(..., description="Message content parts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    extensions: Optional[List[str]] = Field(None, description="Extension URIs")
    reference_task_ids: Optional[List[str]] = Field(None, alias="referenceTaskIds", description="Referenced task IDs")
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Task
# ============================================================================

class TaskStatus(BaseModel):
    """Task status container."""
    state: TaskState = Field(..., description="Current task state")
    message: Optional[Message] = Field(None, description="Status message")
    timestamp: Optional[datetime] = Field(None, description="Status timestamp")


class Artifact(BaseModel):
    """Task output artifact."""
    artifact_id: str = Field(..., alias="artifactId", description="Unique artifact identifier")
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Artifact description")
    parts: List[Part] = Field(..., description="Artifact content parts")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    extensions: Optional[List[str]] = Field(None, description="Extension URIs")
    
    model_config = ConfigDict(populate_by_name=True)


class Task(BaseModel):
    """Core unit of action for A2A."""
    id: str = Field(..., description="Unique task identifier")
    context_id: str = Field(..., alias="contextId", description="Context identifier")
    status: TaskStatus = Field(..., description="Current task status")
    artifacts: Optional[List[Artifact]] = Field(None, description="Output artifacts")
    history: Optional[List[Message]] = Field(None, description="Interaction history")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Task metadata")
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Streaming Events
# ============================================================================

class TaskStatusUpdateEvent(BaseModel):
    """Task status change notification."""
    task_id: str = Field(..., alias="taskId", description="Task ID")
    context_id: str = Field(..., alias="contextId", description="Context ID")
    status: TaskStatus = Field(..., description="New task status")
    final: bool = Field(..., description="Whether this is the final event")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    
    model_config = ConfigDict(populate_by_name=True)


class TaskArtifactUpdateEvent(BaseModel):
    """Task artifact generation notification."""
    task_id: str = Field(..., alias="taskId", description="Task ID")
    context_id: str = Field(..., alias="contextId", description="Context ID")
    artifact: Artifact = Field(..., description="Generated artifact")
    append: Optional[bool] = Field(None, description="Whether to append to existing artifact")
    last_chunk: Optional[bool] = Field(None, alias="lastChunk", description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    
    model_config = ConfigDict(populate_by_name=True)


class StreamResponse(BaseModel):
    """Wrapper for streaming response data."""
    task: Optional[Task] = Field(None, description="Task object")
    message: Optional[Message] = Field(None, description="Message object")
    status_update: Optional[TaskStatusUpdateEvent] = Field(None, alias="statusUpdate", description="Status update event")
    artifact_update: Optional[TaskArtifactUpdateEvent] = Field(None, alias="artifactUpdate", description="Artifact update event")
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Push Notifications
# ============================================================================

class AuthenticationInfo(BaseModel):
    """Authentication details for push notifications."""
    schemes: List[str] = Field(..., description="Supported authentication schemes")
    credentials: Optional[str] = Field(None, description="Optional credentials")


class PushNotificationConfig(BaseModel):
    """Push notification configuration."""
    id: Optional[str] = Field(None, description="Unique identifier")
    url: str = Field(..., description="Webhook URL")
    token: Optional[str] = Field(None, description="Session/task token")
    authentication: Optional[AuthenticationInfo] = Field(None, description="Authentication info")


class TaskPushNotificationConfig(BaseModel):
    """Task-specific push notification configuration."""
    name: str = Field(..., description="Resource name: tasks/{task_id}/pushNotificationConfigs/{config_id}")
    push_notification_config: PushNotificationConfig = Field(..., alias="pushNotificationConfig")
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Agent Card (Discovery)
# ============================================================================

class AgentProvider(BaseModel):
    """Agent service provider information."""
    url: str = Field(..., description="Provider website URL")
    organization: str = Field(..., description="Organization name")


class AgentExtension(BaseModel):
    """Protocol extension declaration."""
    uri: Optional[str] = Field(None, description="Extension URI")
    description: Optional[str] = Field(None, description="Extension description")
    required: Optional[bool] = Field(None, description="Whether client must support this extension")
    params: Optional[Dict[str, Any]] = Field(None, description="Extension parameters")


class AgentCapabilities(BaseModel):
    """Agent capability declarations."""
    streaming: Optional[bool] = Field(None, description="Supports streaming responses")
    push_notifications: Optional[bool] = Field(None, alias="pushNotifications", description="Supports push notifications")
    extensions: Optional[List[AgentExtension]] = Field(None, description="Supported extensions")
    state_transition_history: Optional[bool] = Field(None, alias="stateTransitionHistory", description="Provides state history")
    
    model_config = ConfigDict(populate_by_name=True)


class AgentSkill(BaseModel):
    """Agent capability/function declaration."""
    id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Skill description")
    tags: List[str] = Field(..., description="Capability keywords")
    examples: Optional[List[str]] = Field(None, description="Example prompts")
    input_modes: Optional[List[str]] = Field(None, alias="inputModes", description="Supported input media types")
    output_modes: Optional[List[str]] = Field(None, alias="outputModes", description="Supported output media types")
    security: Optional[List[Dict[str, List[str]]]] = Field(None, description="Security requirements")
    
    model_config = ConfigDict(populate_by_name=True)


class AgentInterface(BaseModel):
    """Protocol binding and URL combination."""
    url: str = Field(..., description="Interface URL")
    protocol_binding: ProtocolBinding = Field(..., alias="protocolBinding", description="Protocol binding type")
    tenant: Optional[str] = Field(None, description="Tenant identifier")
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Security Schemes
# ============================================================================

class APIKeySecurityScheme(BaseModel):
    """API key authentication scheme."""
    description: Optional[str] = Field(None)
    location: str = Field(..., description="Location: query, header, or cookie")
    name: str = Field(..., description="Parameter name")


class HTTPAuthSecurityScheme(BaseModel):
    """HTTP authentication scheme."""
    description: Optional[str] = Field(None)
    scheme: str = Field(..., description="Auth scheme (e.g., 'Bearer')")
    bearer_format: Optional[str] = Field(None, alias="bearerFormat", description="Token format hint")
    
    model_config = ConfigDict(populate_by_name=True)


class OAuthFlow(BaseModel):
    """OAuth flow configuration."""
    authorization_url: Optional[str] = Field(None, alias="authorizationUrl")
    token_url: Optional[str] = Field(None, alias="tokenUrl")
    refresh_url: Optional[str] = Field(None, alias="refreshUrl")
    scopes: Dict[str, str] = Field(default_factory=dict)
    
    model_config = ConfigDict(populate_by_name=True)


class OAuthFlows(BaseModel):
    """OAuth flows configuration."""
    authorization_code: Optional[OAuthFlow] = Field(None, alias="authorizationCode")
    client_credentials: Optional[OAuthFlow] = Field(None, alias="clientCredentials")
    implicit: Optional[OAuthFlow] = Field(None)
    password: Optional[OAuthFlow] = Field(None)
    
    model_config = ConfigDict(populate_by_name=True)


class OAuth2SecurityScheme(BaseModel):
    """OAuth 2.0 authentication scheme."""
    description: Optional[str] = Field(None)
    flows: OAuthFlows = Field(...)
    oauth2_metadata_url: Optional[str] = Field(None, alias="oauth2MetadataUrl")
    
    model_config = ConfigDict(populate_by_name=True)


class OpenIdConnectSecurityScheme(BaseModel):
    """OpenID Connect authentication scheme."""
    description: Optional[str] = Field(None)
    open_id_connect_url: str = Field(..., alias="openIdConnectUrl")
    
    model_config = ConfigDict(populate_by_name=True)


class SecurityScheme(BaseModel):
    """Security scheme definition (discriminated union)."""
    api_key: Optional[APIKeySecurityScheme] = Field(None, alias="apiKeySecurityScheme")
    http_auth: Optional[HTTPAuthSecurityScheme] = Field(None, alias="httpAuthSecurityScheme")
    oauth2: Optional[OAuth2SecurityScheme] = Field(None, alias="oauth2SecurityScheme")
    openid_connect: Optional[OpenIdConnectSecurityScheme] = Field(None, alias="openIdConnectSecurityScheme")
    
    model_config = ConfigDict(populate_by_name=True)


class AgentCardSignature(BaseModel):
    """JWS signature for Agent Card."""
    protected: str = Field(..., description="Base64url-encoded protected header")
    signature: str = Field(..., description="Base64url-encoded signature")
    header: Optional[Dict[str, Any]] = Field(None, description="Unprotected header")


class AgentCard(BaseModel):
    """Agent self-describing manifest."""
    protocol_version: Optional[str] = Field("1.0", alias="protocolVersion", description="A2A protocol version")
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    supported_interfaces: Optional[List[AgentInterface]] = Field(None, alias="supportedInterfaces", description="Supported interfaces")
    url: Optional[str] = Field(None, description="DEPRECATED: Use supportedInterfaces")
    provider: Optional[AgentProvider] = Field(None, description="Service provider")
    version: str = Field(..., description="Agent version")
    documentation_url: Optional[str] = Field(None, alias="documentationUrl", description="Documentation URL")
    capabilities: AgentCapabilities = Field(..., description="Agent capabilities")
    security_schemes: Optional[Dict[str, SecurityScheme]] = Field(None, alias="securitySchemes", description="Security schemes")
    security: Optional[List[Dict[str, List[str]]]] = Field(None, description="Security requirements")
    default_input_modes: List[str] = Field(..., alias="defaultInputModes", description="Default input media types")
    default_output_modes: List[str] = Field(..., alias="defaultOutputModes", description="Default output media types")
    skills: List[AgentSkill] = Field(..., description="Agent skills")
    supports_extended_agent_card: Optional[bool] = Field(None, alias="supportsExtendedAgentCard")
    signatures: Optional[List[AgentCardSignature]] = Field(None, description="JWS signatures")
    icon_url: Optional[str] = Field(None, alias="iconUrl", description="Agent icon URL")
    
    model_config = ConfigDict(populate_by_name=True)


# ============================================================================
# Request/Response Models
# ============================================================================

class SendMessageConfiguration(BaseModel):
    """Send message request configuration."""
    accepted_output_modes: Optional[List[str]] = Field(None, alias="acceptedOutputModes")
    push_notification_config: Optional[PushNotificationConfig] = Field(None, alias="pushNotificationConfig")
    history_length: Optional[int] = Field(None, alias="historyLength")
    blocking: Optional[bool] = Field(None, description="Wait for task completion")
    
    model_config = ConfigDict(populate_by_name=True)


class SendMessageRequest(BaseModel):
    """Request for message/send operation."""
    tenant: Optional[str] = Field(None, description="Optional tenant")
    message: Message = Field(..., description="Message to send")
    configuration: Optional[SendMessageConfiguration] = Field(None, description="Request configuration")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class SendMessageResponse(BaseModel):
    """Response for message/send operation."""
    task: Optional[Task] = Field(None, description="Created task")
    message: Optional[Message] = Field(None, description="Direct response message")


class GetTaskRequest(BaseModel):
    """Request for tasks/get operation."""
    tenant: Optional[str] = Field(None)
    name: str = Field(..., description="Resource name: tasks/{task_id}")
    history_length: Optional[int] = Field(None, alias="historyLength")
    
    model_config = ConfigDict(populate_by_name=True)


class ListTasksRequest(BaseModel):
    """Request for tasks/list operation."""
    tenant: Optional[str] = Field(None)
    context_id: Optional[str] = Field(None, alias="contextId")
    status: Optional[TaskState] = Field(None)
    page_size: Optional[int] = Field(50, alias="pageSize", ge=1, le=100)
    page_token: Optional[str] = Field(None, alias="pageToken")
    history_length: Optional[int] = Field(None, alias="historyLength")
    last_updated_after: Optional[int] = Field(None, alias="lastUpdatedAfter")
    include_artifacts: Optional[bool] = Field(False, alias="includeArtifacts")
    
    model_config = ConfigDict(populate_by_name=True)


class ListTasksResponse(BaseModel):
    """Response for tasks/list operation."""
    tasks: List[Task] = Field(...)
    next_page_token: str = Field(..., alias="nextPageToken")
    page_size: int = Field(..., alias="pageSize")
    total_size: int = Field(..., alias="totalSize")
    
    model_config = ConfigDict(populate_by_name=True)


class CancelTaskRequest(BaseModel):
    """Request for tasks/cancel operation."""
    tenant: Optional[str] = Field(None)
    name: str = Field(..., description="Resource name: tasks/{task_id}")


# ============================================================================
# A2A Agent Configuration (Internal)
# ============================================================================

class A2AAgentConfig(BaseModel):
    """Configuration for connecting to an external A2A agent."""
    id: str = Field(..., description="Unique configuration ID")
    name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Description")
    agent_card_url: str = Field(..., alias="agentCardUrl", description="URL to fetch Agent Card")
    base_url: Optional[str] = Field(None, alias="baseUrl", description="Override base URL")
    protocol_binding: ProtocolBinding = Field(
        default=ProtocolBinding.HTTP_JSON, 
        alias="protocolBinding",
        description="Protocol binding to use"
    )
    auth_type: Optional[Literal["none", "api_key", "bearer", "oauth2"]] = Field(
        "none", alias="authType", description="Authentication type"
    )
    auth_config: Optional[Dict[str, Any]] = Field(None, alias="authConfig", description="Auth configuration")
    headers: Optional[Dict[str, str]] = Field(None, description="Custom headers")
    timeout_seconds: int = Field(30, alias="timeoutSeconds", description="Request timeout")
    retry_count: int = Field(3, alias="retryCount", description="Retry count")
    enabled: bool = Field(True, description="Whether this agent is enabled")
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    # Cached agent card
    cached_agent_card: Optional[AgentCard] = Field(None, alias="cachedAgentCard")
    
    model_config = ConfigDict(populate_by_name=True)


class A2AAgentConfigCreate(BaseModel):
    """Schema for creating A2A agent configuration."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    agent_card_url: str = Field(..., alias="agentCardUrl")
    base_url: Optional[str] = Field(None, alias="baseUrl")
    protocol_binding: ProtocolBinding = Field(default=ProtocolBinding.HTTP_JSON, alias="protocolBinding")
    auth_type: Optional[Literal["none", "api_key", "bearer", "oauth2"]] = Field("none", alias="authType")
    auth_config: Optional[Dict[str, Any]] = Field(None, alias="authConfig")
    headers: Optional[Dict[str, str]] = Field(None)
    timeout_seconds: int = Field(30, alias="timeoutSeconds")
    retry_count: int = Field(3, alias="retryCount")
    enabled: bool = Field(True)
    
    model_config = ConfigDict(populate_by_name=True)


class A2AAgentConfigUpdate(BaseModel):
    """Schema for updating A2A agent configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    agent_card_url: Optional[str] = Field(None, alias="agentCardUrl")
    base_url: Optional[str] = Field(None, alias="baseUrl")
    protocol_binding: Optional[ProtocolBinding] = Field(None, alias="protocolBinding")
    auth_type: Optional[Literal["none", "api_key", "bearer", "oauth2"]] = Field(None, alias="authType")
    auth_config: Optional[Dict[str, Any]] = Field(None, alias="authConfig")
    headers: Optional[Dict[str, str]] = Field(None)
    timeout_seconds: Optional[int] = Field(None, alias="timeoutSeconds")
    retry_count: Optional[int] = Field(None, alias="retryCount")
    enabled: Optional[bool] = Field(None)
    
    model_config = ConfigDict(populate_by_name=True)


class A2AAgentConfigResponse(BaseModel):
    """Response for A2A agent configuration."""
    config: A2AAgentConfig
    agent_card: Optional[AgentCard] = Field(None, alias="agentCard")
    status: Literal["connected", "disconnected", "error"] = Field("disconnected")
    last_error: Optional[str] = Field(None, alias="lastError")
    
    model_config = ConfigDict(populate_by_name=True)


class A2AAgentListResponse(BaseModel):
    """Response for listing A2A agent configurations."""
    agents: List[A2AAgentConfigResponse]
    total: int


# ============================================================================
# A2A Server Configuration (Expose local agents)
# ============================================================================

class A2AServerConfig(BaseModel):
    """Configuration for exposing local agent as A2A server."""
    id: str = Field(..., description="Configuration ID")
    agent_id: str = Field(..., alias="agentId", description="Local agent ID to expose")
    workflow_id: Optional[str] = Field(None, alias="workflowId", description="Or workflow ID")
    
    # Agent Card configuration
    name: str = Field(..., description="A2A agent name")
    description: str = Field(..., description="A2A agent description")
    version: str = Field("1.0.0", description="Agent version")
    
    # Skills mapping
    skills: List[AgentSkill] = Field(default_factory=list, description="Exposed skills")
    
    # Capabilities
    streaming_enabled: bool = Field(True, alias="streamingEnabled")
    push_notifications_enabled: bool = Field(False, alias="pushNotificationsEnabled")
    
    # Security
    require_auth: bool = Field(True, alias="requireAuth")
    allowed_auth_schemes: List[str] = Field(
        default_factory=lambda: ["bearer"], 
        alias="allowedAuthSchemes"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(60, alias="rateLimitPerMinute")
    
    enabled: bool = Field(True)
    created_at: Optional[datetime] = Field(None, alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    
    model_config = ConfigDict(populate_by_name=True)


class A2AServerConfigCreate(BaseModel):
    """Schema for creating A2A server configuration."""
    agent_id: Optional[str] = Field(None, alias="agentId")
    workflow_id: Optional[str] = Field(None, alias="workflowId")
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(...)
    version: str = Field("1.0.0")
    skills: List[AgentSkill] = Field(default_factory=list)
    streaming_enabled: bool = Field(True, alias="streamingEnabled")
    push_notifications_enabled: bool = Field(False, alias="pushNotificationsEnabled")
    require_auth: bool = Field(True, alias="requireAuth")
    allowed_auth_schemes: List[str] = Field(default_factory=lambda: ["bearer"], alias="allowedAuthSchemes")
    rate_limit_per_minute: int = Field(60, alias="rateLimitPerMinute")
    enabled: bool = Field(True)
    
    model_config = ConfigDict(populate_by_name=True)


class A2AServerConfigUpdate(BaseModel):
    """Schema for updating A2A server configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    version: Optional[str] = Field(None)
    skills: Optional[List[AgentSkill]] = Field(None)
    streaming_enabled: Optional[bool] = Field(None, alias="streamingEnabled")
    push_notifications_enabled: Optional[bool] = Field(None, alias="pushNotificationsEnabled")
    require_auth: Optional[bool] = Field(None, alias="requireAuth")
    allowed_auth_schemes: Optional[List[str]] = Field(None, alias="allowedAuthSchemes")
    rate_limit_per_minute: Optional[int] = Field(None, alias="rateLimitPerMinute")
    enabled: Optional[bool] = Field(None)
    
    model_config = ConfigDict(populate_by_name=True)


class A2AServerConfigResponse(BaseModel):
    """Response for A2A server configuration."""
    config: A2AServerConfig
    agent_card_url: str = Field(..., alias="agentCardUrl")
    endpoint_url: str = Field(..., alias="endpointUrl")
    
    model_config = ConfigDict(populate_by_name=True)


class A2AServerListResponse(BaseModel):
    """Response for listing A2A server configurations."""
    servers: List[A2AServerConfigResponse]
    total: int
