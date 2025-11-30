/**
 * TypeScript interfaces for the Agentic RAG system frontend.
 * These mirror the backend Pydantic models.
 */

/**
 * Represents a chunk of text from a document.
 */
export interface TextChunk {
  chunk_id: string;
  document_id: string;
  text: string;
  chunk_index: number;
  start_char: number;
  end_char: number;
  metadata: Record<string, any>;
  embedding?: number[];
}

/**
 * Represents a document in the system.
 */
export interface Document {
  document_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  created_at: string;
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count?: number;
  metadata?: Record<string, any>;
  error_message?: string;
}

/**
 * Represents a search result from vector database.
 */
export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  text: string;
  score: number;
  metadata: Record<string, any>;
}

/**
 * Query mode for hybrid system.
 */
export type QueryMode = 'FAST' | 'BALANCED' | 'DEEP' | 'WEB_SEARCH';

/**
 * Request model for query processing.
 */
export interface QueryRequest {
  query: string;
  session_id?: string;
  top_k?: number;
  filters?: Record<string, any>;
  stream?: boolean;
  mode?: QueryMode;
}

/**
 * Response model for query processing.
 */
export interface QueryResponse {
  query_id: string;
  query: string;
  response: string;
  sources: SearchResult[];
  reasoning_steps: Record<string, any>[];
  session_id?: string;
  processing_time?: number;
  metadata: Record<string, any>;
}

/**
 * Agent step types for reasoning process.
 */
export type AgentStepType = 
  | 'thought' 
  | 'action' 
  | 'observation' 
  | 'planning' 
  | 'reflection' 
  | 'response' 
  | 'memory' 
  | 'error';

/**
 * Represents a single step in the agent's reasoning process.
 */
export interface AgentStep {
  step_id: string;
  type: AgentStepType;
  content: string;
  timestamp: string;
  metadata: Record<string, any>;
}

/**
 * Response chunk types for streaming.
 */
export type StreamChunkType = 
  | 'chunk' 
  | 'preliminary' 
  | 'refinement' 
  | 'final' 
  | 'step' 
  | 'response'  // Streaming token-by-token response
  | 'error' 
  | 'done';

/**
 * Response type indicators.
 */
export type ResponseType = 'preliminary' | 'refinement' | 'final';

/**
 * Path source indicators.
 */
export type PathSource = 'speculative' | 'agentic' | 'hybrid';

/**
 * Response chunk data structure.
 */
export interface ResponseChunk {
  content: string;
  sources?: SearchResult[];
  reasoning_steps?: AgentStep[];
  response_type?: ResponseType;
  path_source?: PathSource;
  confidence_score?: number;
}

/**
 * Stream chunk data structure.
 */
export interface StreamChunk {
  type: StreamChunkType;
  data: ResponseChunk | AgentStep | { error: string } | Record<string, any>;
  timestamp?: string;
}

/**
 * Represents the complete state of the agent during query processing.
 */
export interface AgentState {
  query: string;
  session_id?: string;
  planning_steps: string[];
  action_history: Record<string, any>[];
  retrieved_docs: Record<string, any>[];
  reasoning_steps: AgentStep[];
  final_response?: string;
  memory_context: Record<string, any>;
  current_action?: Record<string, any>;
  reflection_decision?: string;
  error?: string;
}

/**
 * Document response from API.
 */
export interface DocumentResponse {
  document_id: string;
  user_id: string;
  filename: string;
  file_size: number;
  file_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count: number;
  created_at: string;
  processing_completed_at?: string;
  error_message?: string;
}

/**
 * Document list response from API.
 */
export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Upload response from document upload endpoint.
 */
export interface UploadResponse {
  document_id: string;
  filename: string;
  status: 'processing' | 'completed' | 'failed';
  chunk_count?: number;
}

// Note: ResponseType, PathSource, ResponseChunk, and StreamChunk are defined above
// Removed duplicate definitions

/**
 * Error response from API.
 */
export interface ErrorResponse {
  detail: string;
  status_code: number;
}

/**
 * User information response.
 */
export interface UserResponse {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  query_count: number;
  storage_used_bytes: number;
}

/**
 * Token response from authentication endpoints.
 */
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

/**
 * User registration data.
 */
export interface UserCreate {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

/**
 * User login data.
 */
export interface UserLogin {
  email: string;
  password: string;
}

/**
 * Session (conversation) information.
 */
export interface SessionResponse {
  id: string;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

/**
 * List of sessions with pagination.
 */
export interface SessionListResponse {
  sessions: SessionResponse[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Message in a conversation.
 */
export interface MessageResponse {
  id: string;
  session_id: string;
  user_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  metadata?: Record<string, any>;
  sources?: SearchResult[];
  // Progressive response properties
  reasoning_steps?: AgentStep[];
  response_type?: 'preliminary' | 'refinement' | 'final';
  path_source?: 'speculative' | 'agentic' | 'hybrid';
  confidence_score?: number;
}

/**
 * List of messages with pagination.
 */
export interface MessageListResponse {
  messages: MessageResponse[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Document response with user information.
 */
export interface DocumentResponse {
  id: string;
  user_id: string;
  filename: string;
  file_path: string;
  file_size: number;
  file_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  chunk_count: number;
  created_at: string;
  updated_at: string;
  error_message?: string;
}

/**
 * List of documents with pagination.
 */
export interface DocumentListResponse {
  documents: DocumentResponse[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Batch upload response.
 */
export interface BatchUploadResponse {
  id: string;
  user_id: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
}

/**
 * Batch upload progress with file details.
 */
export interface BatchProgressResponse {
  id: string;
  user_id: string;
  total_files: number;
  completed_files: number;
  failed_files: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  files: Array<{
    filename: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    error_message?: string;
  }>;
}
