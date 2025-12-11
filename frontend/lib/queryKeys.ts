// Query Keys Factory for React Query
// Provides consistent cache key management

import { FlowFilters, AuditLogFilters } from './types/flows';

export const queryKeys = {
  // Workflows/Flows
  workflows: {
    all: ['workflows'] as const,
    lists: () => [...queryKeys.workflows.all, 'list'] as const,
    list: (filters: FlowFilters) => [...queryKeys.workflows.lists(), filters] as const,
    details: () => [...queryKeys.workflows.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.workflows.details(), id] as const,
  },

  // Agentflows
  agentflows: {
    all: ['agentflows'] as const,
    lists: () => [...queryKeys.agentflows.all, 'list'] as const,
    list: (filters: FlowFilters) => [...queryKeys.agentflows.lists(), filters] as const,
    details: () => [...queryKeys.agentflows.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.agentflows.details(), id] as const,
  },

  // Chatflows
  chatflows: {
    all: ['chatflows'] as const,
    lists: () => [...queryKeys.chatflows.all, 'list'] as const,
    list: (filters: FlowFilters) => [...queryKeys.chatflows.lists(), filters] as const,
    details: () => [...queryKeys.chatflows.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.chatflows.details(), id] as const,
  },

  // Executions
  executions: {
    all: ['executions'] as const,
    lists: () => [...queryKeys.executions.all, 'list'] as const,
    list: (flowId: string) => [...queryKeys.executions.lists(), flowId] as const,
    details: () => [...queryKeys.executions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.executions.details(), id] as const,
  },

  // Documents
  documents: {
    all: ['documents'] as const,
    lists: () => [...queryKeys.documents.all, 'list'] as const,
    list: (filters: { status?: string; limit?: number; offset?: number }) => 
      [...queryKeys.documents.lists(), filters] as const,
    details: () => [...queryKeys.documents.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.documents.details(), id] as const,
  },

  // Sessions (Conversations)
  sessions: {
    all: ['sessions'] as const,
    lists: () => [...queryKeys.sessions.all, 'list'] as const,
    list: (filters: { limit?: number; offset?: number }) => 
      [...queryKeys.sessions.lists(), filters] as const,
    details: () => [...queryKeys.sessions.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.sessions.details(), id] as const,
    messages: (id: string) => [...queryKeys.sessions.detail(id), 'messages'] as const,
  },

  // Events (Event Store)
  events: {
    all: ['events'] as const,
    aggregate: (aggregateId: string, aggregateType?: string, fromVersion?: number) =>
      [...queryKeys.events.all, 'aggregate', aggregateId, aggregateType, fromVersion] as const,
    audit: (filters: AuditLogFilters) => 
      [...queryKeys.events.all, 'audit', filters] as const,
  },

  // User
  user: {
    me: ['user', 'me'] as const,
  },

  // Models
  models: {
    all: ['models'] as const,
    ollama: () => [...queryKeys.models.all, 'ollama'] as const,
    current: () => [...queryKeys.models.all, 'current'] as const,
  },

  // Feedback
  feedback: {
    all: ['feedback'] as const,
    stats: (days: number) => [...queryKeys.feedback.all, 'stats', days] as const,
    history: (filters: { limit?: number; offset?: number; qualityLevel?: string }) =>
      [...queryKeys.feedback.all, 'history', filters] as const,
  },

  // Confidence
  confidence: {
    all: ['confidence'] as const,
    stats: () => [...queryKeys.confidence.all, 'stats'] as const,
  },
};
