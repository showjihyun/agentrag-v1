/**
 * A2A Protocol Types
 * 
 * Google A2A 프로토콜 관련 TypeScript 타입 정의
 */

// Enums
export type TaskState = 
  | 'unspecified'
  | 'submitted'
  | 'working'
  | 'completed'
  | 'failed'
  | 'cancelled'
  | 'input_required'
  | 'rejected'
  | 'auth_required';

export type Role = 'unspecified' | 'user' | 'agent';

export type ProtocolBinding = 'JSONRPC' | 'GRPC' | 'HTTP+JSON';

export type AuthType = 'none' | 'api_key' | 'bearer' | 'oauth2';

// Part Types
export interface FilePart {
  fileWithUri?: string;
  fileWithBytes?: string;
  mediaType?: string;
  name?: string;
}

export interface DataPart {
  data: Record<string, unknown>;
}

export interface Part {
  text?: string;
  file?: FilePart;
  data?: DataPart;
  metadata?: Record<string, unknown>;
}

// Message
export interface Message {
  messageId: string;
  contextId?: string;
  taskId?: string;
  role: Role;
  parts: Part[];
  metadata?: Record<string, unknown>;
  extensions?: string[];
  referenceTaskIds?: string[];
}

// Task
export interface TaskStatus {
  state: TaskState;
  message?: Message;
  timestamp?: string;
}

export interface Artifact {
  artifactId: string;
  name?: string;
  description?: string;
  parts: Part[];
  metadata?: Record<string, unknown>;
  extensions?: string[];
}

export interface Task {
  id: string;
  contextId: string;
  status: TaskStatus;
  artifacts?: Artifact[];
  history?: Message[];
  metadata?: Record<string, unknown>;
}

// Streaming Events
export interface TaskStatusUpdateEvent {
  taskId: string;
  contextId: string;
  status: TaskStatus;
  final: boolean;
  metadata?: Record<string, unknown>;
}

export interface TaskArtifactUpdateEvent {
  taskId: string;
  contextId: string;
  artifact: Artifact;
  append?: boolean;
  lastChunk?: boolean;
  metadata?: Record<string, unknown>;
}

export interface StreamResponse {
  task?: Task;
  message?: Message;
  statusUpdate?: TaskStatusUpdateEvent;
  artifactUpdate?: TaskArtifactUpdateEvent;
}

// Agent Card
export interface AgentProvider {
  url: string;
  organization: string;
}

export interface AgentCapabilities {
  streaming?: boolean;
  pushNotifications?: boolean;
  stateTransitionHistory?: boolean;
}

export interface AgentSkill {
  id: string;
  name: string;
  description: string;
  tags: string[];
  examples?: string[];
  inputModes?: string[];
  outputModes?: string[];
}

export interface AgentInterface {
  url: string;
  protocolBinding: ProtocolBinding;
  tenant?: string;
}

export interface AgentCard {
  protocolVersion?: string;
  name: string;
  description: string;
  supportedInterfaces?: AgentInterface[];
  url?: string;
  provider?: AgentProvider;
  version: string;
  documentationUrl?: string;
  capabilities: AgentCapabilities;
  defaultInputModes: string[];
  defaultOutputModes: string[];
  skills: AgentSkill[];
  supportsExtendedAgentCard?: boolean;
  iconUrl?: string;
}

// Configuration Types
export interface A2AAgentConfig {
  id: string;
  name: string;
  description?: string;
  agentCardUrl: string;
  baseUrl?: string;
  protocolBinding: ProtocolBinding;
  authType: AuthType;
  authConfig?: Record<string, unknown>;
  headers?: Record<string, string>;
  timeoutSeconds: number;
  retryCount: number;
  enabled: boolean;
  createdAt?: string;
  updatedAt?: string;
  cachedAgentCard?: AgentCard;
}

export interface A2AAgentConfigCreate {
  name: string;
  description?: string;
  agentCardUrl: string;
  baseUrl?: string;
  protocolBinding?: ProtocolBinding;
  authType?: AuthType;
  authConfig?: Record<string, unknown>;
  headers?: Record<string, string>;
  timeoutSeconds?: number;
  retryCount?: number;
  enabled?: boolean;
}

export interface A2AAgentConfigUpdate {
  name?: string;
  description?: string;
  agentCardUrl?: string;
  baseUrl?: string;
  protocolBinding?: ProtocolBinding;
  authType?: AuthType;
  authConfig?: Record<string, unknown>;
  headers?: Record<string, string>;
  timeoutSeconds?: number;
  retryCount?: number;
  enabled?: boolean;
}

export interface A2AAgentConfigResponse {
  config: A2AAgentConfig;
  agentCard?: AgentCard;
  status: 'connected' | 'disconnected' | 'error';
  lastError?: string;
}

export interface A2AAgentListResponse {
  agents: A2AAgentConfigResponse[];
  total: number;
}

// Server Configuration
export interface A2AServerConfig {
  id: string;
  agentId?: string;
  workflowId?: string;
  name: string;
  description: string;
  version: string;
  skills: AgentSkill[];
  streamingEnabled: boolean;
  pushNotificationsEnabled: boolean;
  requireAuth: boolean;
  allowedAuthSchemes: string[];
  rateLimitPerMinute: number;
  enabled: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface A2AServerConfigCreate {
  agentId?: string;
  workflowId?: string;
  name: string;
  description: string;
  version?: string;
  skills?: AgentSkill[];
  streamingEnabled?: boolean;
  pushNotificationsEnabled?: boolean;
  requireAuth?: boolean;
  allowedAuthSchemes?: string[];
  rateLimitPerMinute?: number;
  enabled?: boolean;
}

export interface A2AServerConfigUpdate {
  name?: string;
  description?: string;
  version?: string;
  skills?: AgentSkill[];
  streamingEnabled?: boolean;
  pushNotificationsEnabled?: boolean;
  requireAuth?: boolean;
  allowedAuthSchemes?: string[];
  rateLimitPerMinute?: number;
  enabled?: boolean;
}

export interface A2AServerConfigResponse {
  config: A2AServerConfig;
  agentCardUrl: string;
  endpointUrl: string;
}

export interface A2AServerListResponse {
  servers: A2AServerConfigResponse[];
  total: number;
}

// Request/Response Types
export interface SendMessageRequest {
  text?: string;
  data?: Record<string, unknown>;
  contextId?: string;
  blocking?: boolean;
}

export interface SendMessageResponse {
  task?: Task;
  message?: Message;
}
