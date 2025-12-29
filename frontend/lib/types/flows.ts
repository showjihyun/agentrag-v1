// Flow Types for Agentflow and Chatflow

export type FlowType = 'agentflow' | 'chatflow';

// Base Flow interface
export interface BaseFlow {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  flow_type: FlowType;
  graph_definition: FlowGraphDefinition;
  is_public: boolean;
  is_active: boolean;
  version: string;
  tags?: string[];
  category?: string;
  created_at: string;
  updated_at?: string;
  execution_count?: number;
  last_execution_status?: 'success' | 'failed' | 'running' | 'completed';
  last_execution_at?: string;
}

// Agentflow - Multi-Agent Systems
export interface Agentflow extends BaseFlow {
  flow_type: 'agentflow';
  orchestration_type: 
    // Core patterns (existing)
    | 'sequential' 
    | 'parallel' 
    | 'hierarchical' 
    | 'adaptive'
    // 2025 Trends - Advanced patterns
    | 'consensus_building'
    | 'dynamic_routing'
    | 'swarm_intelligence'
    | 'event_driven'
    | 'reflection'
    // 2026 Trends - Next-generation patterns
    | 'neuromorphic'
    | 'quantum_enhanced'
    | 'bio_inspired'
    | 'self_evolving'
    | 'federated'
    | 'emotional_ai'
    | 'predictive';
  supervisor_config?: SupervisorConfig;
  agents: AgentflowAgent[];
  communication_protocol?: 'direct' | 'broadcast' | 'pubsub';
}

export interface SupervisorConfig {
  enabled: boolean;
  llm_provider: string;
  llm_model: string;
  max_iterations: number;
  decision_strategy: 'round_robin' | 'priority' | 'llm_based' | 'rule_based';
  fallback_agent_id?: string;
}

export interface AgentflowAgent {
  id: string;
  agent_id: string;
  name: string;
  role: string;
  description?: string;
  capabilities: string[];
  priority: number;
  max_retries: number;
  timeout_seconds: number;
  dependencies?: string[];
}

// Chatflow - Single-Agent Chat Assistants
export interface Chatflow extends BaseFlow {
  flow_type: 'chatflow';
  chat_config: ChatConfig;
  memory_config: MemoryConfig;
  rag_config?: RAGConfig;
  tools: ChatflowTool[];
}

export interface ChatConfig {
  llm_provider: string;
  llm_model: string;
  system_prompt: string;
  temperature: number;
  max_tokens: number;
  streaming: boolean;
  welcome_message?: string;
  suggested_questions?: string[];
}

export interface MemoryConfig {
  type: 'buffer' | 'summary' | 'vector' | 'hybrid';
  max_messages: number;
  summary_threshold?: number;
  vector_store_id?: string;
}

export interface RAGConfig {
  enabled: boolean;
  knowledgebase_ids: string[];
  retrieval_strategy: 'similarity' | 'mmr' | 'hybrid';
  top_k: number;
  score_threshold: number;
  reranking_enabled: boolean;
  reranking_model?: string;
}

export interface ChatflowTool {
  id: string;
  tool_id: string;
  name: string;
  description?: string;
  enabled: boolean;
  configuration?: Record<string, any>;
}

// Flow Graph Definition
export interface FlowGraphDefinition {
  nodes: FlowNode[];
  edges: FlowEdge[];
  viewport?: { x: number; y: number; zoom: number };
}

export interface FlowNode {
  id: string;
  type: FlowNodeType;
  position: { x: number; y: number };
  data: FlowNodeData;
  width?: number;
  height?: number;
}

export type FlowNodeType =
  // Common
  | 'start'
  | 'end'
  | 'condition'
  | 'loop'
  | 'delay'
  // Agentflow specific
  | 'supervisor'
  | 'worker_agent'
  | 'router'
  | 'parallel'
  | 'sequential'
  | 'aggregator'
  | 'human_in_loop'
  // Chatflow specific
  | 'chat_input'
  | 'chat_output'
  | 'llm'
  | 'memory'
  | 'retriever'
  | 'tool_executor'
  | 'prompt_template'
  // Shared
  | 'agent'
  | 'block'
  | 'tool'
  | 'trigger'
  | 'transform'
  | 'http_request'
  | 'code'
  | 'webhook';

export interface FlowNodeData {
  label: string;
  description?: string;
  configuration?: Record<string, any>;
  inputs?: FlowNodePort[];
  outputs?: FlowNodePort[];
  status?: 'idle' | 'running' | 'success' | 'error';
  error?: string;
  metrics?: NodeMetrics;
}

export interface FlowNodePort {
  id: string;
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array' | 'any';
  required?: boolean;
  default?: any;
}

export interface FlowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: 'default' | 'conditional' | 'error';
  label?: string;
  condition?: string;
  animated?: boolean;
}

export interface NodeMetrics {
  execution_count: number;
  avg_duration_ms: number;
  success_rate: number;
  last_execution_at?: string;
}

// Flow Execution
export interface FlowExecution {
  id: string;
  flow_id: string;
  flow_type: FlowType;
  flow_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  node_executions: NodeExecution[];
  metrics: ExecutionMetrics;
}

export interface NodeExecution {
  id: string;
  node_id: string;
  node_type: FlowNodeType;
  node_label: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  input_data?: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  retry_count?: number;
  logs?: ExecutionLog[];
}

export interface ExecutionLog {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  metadata?: Record<string, any>;
}

export interface ExecutionMetrics {
  total_nodes: number;
  completed_nodes: number;
  failed_nodes: number;
  skipped_nodes: number;
  total_duration_ms: number;
  llm_calls: number;
  llm_tokens: number;
  tool_calls: number;
  estimated_cost: number;
}

// Flow Templates
export interface FlowTemplate {
  id: string;
  name: string;
  description: string;
  flow_type: FlowType;
  category: string;
  tags: string[];
  icon: string;
  preview_image?: string;
  graph_definition: FlowGraphDefinition;
  default_config: Record<string, any>;
  popularity: number;
  author?: string;
  created_at: string;
}

// API Request/Response Types
export interface CreateAgentflowRequest {
  name: string;
  description?: string;
  orchestration_type: Agentflow['orchestration_type'];
  supervisor_config?: SupervisorConfig;
  graph_definition?: FlowGraphDefinition;
  tags?: string[];
}

export interface CreateChatflowRequest {
  name: string;
  description?: string;
  chat_config: ChatConfig;
  memory_config?: MemoryConfig;
  rag_config?: RAGConfig;
  graph_definition?: FlowGraphDefinition;
  tags?: string[];
}

export interface UpdateFlowRequest {
  name?: string;
  description?: string;
  graph_definition?: FlowGraphDefinition;
  is_active?: boolean;
  tags?: string[];
  configuration?: Record<string, any>;
}

export interface FlowListResponse {
  flows: (Agentflow | Chatflow)[];
  total: number;
  page: number;
  page_size: number;
}

export interface FlowFilters {
  flow_type?: FlowType;
  search?: string;
  category?: string;
  tags?: string[];
  is_active?: boolean;
  page?: number;
  page_size?: number;
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'execution_count';
  sort_order?: 'asc' | 'desc';
}
