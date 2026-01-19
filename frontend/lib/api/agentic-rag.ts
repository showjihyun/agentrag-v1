/**
 * Agentic RAG API Client
 * 
 * Provides type-safe API calls for Agentic RAG functionality.
 */

import { apiClient } from './api-client';

export interface AgenticRAGQueryRequest {
  query: string;
  conversation_id?: string;
  knowledge_base_id?: string;
  strategy?: 'adaptive' | 'hybrid' | 'vector_only' | 'web_only';
  top_k?: number;
  context?: Record<string, any>;
}

export interface Source {
  content: string;
  metadata: Record<string, any>;
  source_type: string;
  relevance_score: number;
  url?: string;
}

export interface SubQuery {
  id: string;
  query: string;
  num_results: number;
}

export interface AgenticRAGQueryResponse {
  answer: string;
  sources: Source[];
  metadata: {
    query_complexity: 'simple' | 'moderate' | 'complex';
    retrieval_strategy: string;
    sub_queries: SubQuery[];
    retrieval_iterations: number;
    confidence_score: number;
    reflection_applied: boolean;
    execution_time: number;
    total_sources: number;
  };
}

export interface QueryComplexityResponse {
  query: string;
  complexity: 'simple' | 'moderate' | 'complex';
  recommended_strategy: string;
  estimated_execution_time: number;
}

export interface QueryDecompositionResponse {
  original_query: string;
  sub_queries: Array<{
    id: string;
    query: string;
    dependencies: string[];
  }>;
  total_sub_queries: number;
}

export interface AgenticRAGStatistics {
  total_queries: number;
  average_execution_time: number;
  average_confidence: number;
}

export class AgenticRAGAPI {
  /**
   * Execute Agentic RAG query
   */
  async query(request: AgenticRAGQueryRequest): Promise<AgenticRAGQueryResponse> {
    return apiClient.request('/api/agentic-rag/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Analyze query complexity
   */
  async analyzeComplexity(
    query: string,
    context?: Record<string, any>
  ): Promise<QueryComplexityResponse> {
    const params = new URLSearchParams({ query });
    if (context) {
      params.append('context', JSON.stringify(context));
    }

    return apiClient.request(`/api/agentic-rag/analyze-complexity?${params}`, {
      method: 'POST',
    });
  }

  /**
   * Decompose complex query into sub-queries
   */
  async decomposeQuery(
    query: string,
    context?: Record<string, any>
  ): Promise<QueryDecompositionResponse> {
    const params = new URLSearchParams({ query });
    if (context) {
      params.append('context', JSON.stringify(context));
    }

    return apiClient.request(`/api/agentic-rag/decompose-query?${params}`, {
      method: 'POST',
    });
  }

  /**
   * Get usage statistics
   */
  async getStatistics(): Promise<AgenticRAGStatistics> {
    return apiClient.request('/api/agentic-rag/statistics', {
      method: 'GET',
    });
  }
}

// Export singleton instance
export const agenticRAGAPI = new AgenticRAGAPI();
