/**
 * Chatflow memory management types
 */

export interface ChatSession {
  id: string;
  title: string;
  memory_type: MemoryType;
  memory_config: MemoryConfig;
  message_count: number;
  total_tokens_used: number;
  created_at: string;
  last_activity_at?: string;
  status: SessionStatus;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  metadata?: MessageMetadata;
  isStreaming?: boolean;
}

export interface MessageMetadata {
  tokens_used?: {
    input: number;
    output: number;
  };
  response_time?: number;
  model_used?: string;
  temperature?: number;
  sources?: any[];
  tool_calls?: any[];
  importance_score?: number;
  topics?: string[];
  sentiment?: string;
  intent?: string;
  references?: string[];
}

export type MemoryType = 'buffer' | 'summary' | 'vector' | 'hybrid';

export type SessionStatus = 'active' | 'archived' | 'deleted';

export interface MemoryConfig {
  buffer_size?: number;
  summary_threshold?: number;
  summary_interval?: number;
  vector_top_k?: number;
  hybrid_weights?: {
    buffer: number;
    summary: number;
    vector: number;
  };
}

export interface MemoryStrategy {
  name: string;
  description: string;
  config_options: Record<string, MemoryConfigOption>;
  status?: 'available' | 'coming_soon';
}

export interface MemoryConfigOption {
  type: 'integer' | 'float' | 'object';
  default: any;
  description: string;
  min?: number;
  max?: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  workflow_id?: string;
  config?: {
    provider?: string;
    model?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
    memory_type?: MemoryType;
    memory_config?: MemoryConfig;
  };
}

export interface ChatResponse {
  success: boolean;
  response?: string;
  error?: string;
  session_id: string;
  message_count: number;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  response_time?: number;
}

export interface SessionListResponse {
  success: boolean;
  sessions: ChatSession[];
  total: number;
}

export interface SessionDetailResponse {
  success: boolean;
  session: ChatSession;
  messages: ChatMessage[];
}

export interface MemoryStrategiesResponse {
  success: boolean;
  strategies: Record<string, MemoryStrategy>;
}