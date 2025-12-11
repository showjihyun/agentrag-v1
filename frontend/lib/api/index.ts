/**
 * Unified API Layer
 * 
 * This module provides a centralized API client for all backend interactions.
 * Import from this file for consistent API access across the application.
 */

// Re-export all API modules
export * from './agent-builder';
export * from './flows';
export * from './workflow-api';
export * from './tools';
export * from './api-keys';
export * from './triggers';
export * from './dashboard';
export * from './chat-history';
export * from './notifications';
export * from './user-settings';
export * from './audit-logs';
export * from './exports';
export * from './workflow-debug';
export * from './workflow-monitoring';
export * from './code-execution';

// Re-export the main RAG API client from parent
export { RAGApiClient, apiClient } from '../api-client';

// Export types
export type {
  Agent,
  Tool,
  Block,
  Knowledgebase,
  Execution,
  Variable,
  AgentCreate,
  AgentUpdate,
  BlockCreate,
  BlockUpdate,
  KnowledgebaseCreate,
  KnowledgebaseUpdate,
  VariableCreate,
  VariableUpdate,
} from './agent-builder';
