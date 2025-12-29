// API client for RAG backend - Fixed version

import { 
  StreamChunk, 
  TokenResponse, 
  UserResponse, 
  UserCreate,
  SessionListResponse,
  SessionResponse,
  MessageListResponse,
  DocumentResponse,
  DocumentListResponse,
  BatchUploadResponse,
  BatchProgressResponse
} from './types';
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth';
import { APIError, NetworkError } from './errors';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class RAGApiClient {
  private baseUrl: string;
  private isRefreshing: boolean = false;
  private refreshPromise: Promise<void> | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Get authorization headers if token exists.
   */
  private getAuthHeaders(): Record<string, string> {
    const token = getAccessToken();
    if (token) {
      return {
        'Authorization': `Bearer ${token}`,
      };
    }
    return {};
  }

  /**
   * Common request method with error handling.
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
      ...this.getAuthHeaders(),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle 401 with token refresh
      if (response.status === 401) {
        await this.handleTokenRefresh();
        // Retry with new token
        return this.request<T>(endpoint, options);
      }

      // Handle errors
      if (!response.ok) {
        throw await APIError.fromResponse(response);
      }

      // Handle 204 No Content (no response body)
      if (response.status === 204) {
        return undefined as T;
      }

      // Check if response has content
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return response.json();
      }

      // For non-JSON responses, return empty object
      return {} as T;
    } catch (error) {
      // Network errors
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('Network connection failed');
      }
      throw error;
    }
  }

  /**
   * Request method for file uploads (FormData).
   */
  private async requestFile<T>(
    endpoint: string,
    formData: FormData
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      ...this.getAuthHeaders(),
      // Don't set Content-Type for FormData - browser will set it with boundary
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: formData,
      });

      // Handle 401 with token refresh
      if (response.status === 401) {
        await this.handleTokenRefresh();
        return this.requestFile<T>(endpoint, formData);
      }

      if (!response.ok) {
        throw await APIError.fromResponse(response);
      }

      // Handle 204 No Content (no response body)
      if (response.status === 204) {
        return undefined as T;
      }

      // Check if response has content
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return response.json();
      }

      // For non-JSON responses, return empty object
      return {} as T;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new NetworkError('Network connection failed');
      }
      throw error;
    }
  }

  /**
   * Handle token refresh with deduplication.
   */
  private async handleTokenRefresh(): Promise<void> {
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;
    this.refreshPromise = this.performTokenRefresh();

    try {
      await this.refreshPromise;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  /**
   * Perform actual token refresh.
   */
  private async performTokenRefresh(): Promise<void> {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      throw new APIError('No refresh token available', 401, 'AuthenticationException');
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        clearTokens();
        throw await APIError.fromResponse(response);
      }

      const tokenData: TokenResponse = await response.json();
      setTokens(tokenData.access_token, tokenData.refresh_token);
    } catch (error) {
      clearTokens();
      throw error;
    }
  }

  // Auth endpoints

  async login(email: string, password: string): Promise<TokenResponse> {
    return this.request<TokenResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(userData: UserCreate): Promise<TokenResponse> {
    return this.request<TokenResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async me(): Promise<UserResponse> {
    return this.request<UserResponse>('/api/auth/me');
  }

  async updateUser(updates: {
    username?: string;
    full_name?: string;
    email?: string;
    current_password?: string;
    new_password?: string;
  }): Promise<UserResponse> {
    return this.request<UserResponse>('/api/auth/me', {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async refresh(refreshToken: string): Promise<TokenResponse> {
    return this.request<TokenResponse>('/api/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  // Conversation endpoints

  async getSessions(limit: number = 20, offset: number = 0): Promise<SessionListResponse> {
    return this.request<SessionListResponse>(
      `/api/conversations/sessions?limit=${limit}&offset=${offset}`
    );
  }

  async createSession(title?: string): Promise<SessionResponse> {
    return this.request<SessionResponse>('/api/conversations/sessions', {
      method: 'POST',
      body: JSON.stringify({ title }),
    });
  }

  async updateSession(id: string, title: string): Promise<SessionResponse> {
    return this.request<SessionResponse>(`/api/conversations/sessions/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    });
  }

  async deleteSession(id: string): Promise<void> {
    return this.request<void>(`/api/conversations/sessions/${id}`, {
      method: 'DELETE',
    });
  }

  async getSession(id: string): Promise<SessionResponse> {
    return this.request<SessionResponse>(`/api/conversations/sessions/${id}`);
  }

  async getSessionMessages(id: string, limit: number = 50, offset: number = 0): Promise<MessageListResponse> {
    return this.request<MessageListResponse>(
      `/api/conversations/sessions/${id}/messages?limit=${limit}&offset=${offset}`
    );
  }

  async searchMessages(query: string, limit: number = 20, offset: number = 0): Promise<MessageListResponse> {
    return this.request<MessageListResponse>('/api/conversations/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit, offset }),
    });
  }

  async getMessages(sessionId: string, limit: number = 50, offset: number = 0): Promise<MessageListResponse> {
    return this.getSessionMessages(sessionId, limit, offset);
  }

  // Document endpoints

  async uploadDocument(file: File): Promise<DocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.requestFile<DocumentResponse>('/api/documents/upload', formData);
  }

  async *queryStream(
    query: string,
    options?: { mode?: string; session_id?: string; top_k?: number }
  ): AsyncGenerator<StreamChunk> {
    // Convert mode to lowercase for backend compatibility
    const mode = options?.mode ? options.mode.toLowerCase() : 'auto';
    
    const requestBody: any = {
      query,
      mode,
      top_k: options?.top_k || 10,
    };
    
    if (options?.session_id) {
      requestBody.session_id = options.session_id;
    }
    
    const url = `${this.baseUrl}/api/query`;
    const headers = {
      'Content-Type': 'application/json',
      ...this.getAuthHeaders(),
    };

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody),
    });
    
    if (!response.ok) {
      throw await APIError.fromResponse(response);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('No response body');
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (!line || !line.trim()) continue; // Skip empty lines
        
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }
          try {
            yield JSON.parse(data) as StreamChunk;
          } catch {
            // Skip malformed JSON chunks - this can happen with partial data
            console.warn('Failed to parse stream chunk, skipping:', data.substring(0, 100));
          }
        }
      }
    }
  }

  async getDocuments(status?: string, limit: number = 50, offset: number = 0): Promise<DocumentListResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (status) {
      params.append('status', status);
    }

    return this.request<DocumentListResponse>(`/api/documents?${params.toString()}`);
  }

  async getDocument(documentId: string): Promise<DocumentResponse> {
    return this.request<DocumentResponse>(`/api/documents/${documentId}`);
  }

  async deleteDocument(documentId: string): Promise<void> {
    return this.request<void>(`/api/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async uploadBatch(files: File[]): Promise<BatchUploadResponse> {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    return this.requestFile<BatchUploadResponse>('/api/documents/batch', formData);
  }

  async getBatchStatus(batchId: string): Promise<BatchProgressResponse> {
    return this.request<BatchProgressResponse>(`/api/documents/batch/${batchId}`);
  }

  streamBatchProgress(batchId: string): EventSource {
    const token = getAccessToken();
    
    if (!token) {
      throw new Error('Authentication required for batch progress streaming');
    }
    
    const url = new URL(`${this.baseUrl}/api/documents/batch/${batchId}/progress`);
    url.searchParams.append('token', token);

    return new EventSource(url.toString());
  }

  // Query endpoints

  async analyzeQueryComplexity(query: string): Promise<any> {
    return this.request<any>('/api/query/analyze-complexity', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  async query(
    query: string,
    options?: { mode?: string; session_id?: string; top_k?: number }
  ): Promise<any> {
    return this.request<any>('/api/query/sync', {
      method: 'POST',
      body: JSON.stringify({ query, ...options }),
    });
  }

  async getQueryStatus(queryId: string): Promise<any> {
    return this.request<any>(`/api/query/${queryId}`);
  }

  // Health check endpoint

  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    if (!response.ok) {
      throw new Error('Health check failed');
    }
    return response.json();
  }

  // Model management endpoints

  async getOllamaModels(): Promise<any> {
    return this.request<any>('/api/models/ollama/list');
  }

  async getCurrentModel(): Promise<any> {
    return this.request<any>('/api/models/current');
  }

  // Confidence prediction endpoints

  async calculateConfidence(request: {
    query: string;
    sources: any[];
    response: string;
    mode: string;
    reasoning_steps?: number;
    has_memory?: boolean;
    cache_hit?: boolean;
    user_history?: any;
  }): Promise<{
    confidence: number;
    method: 'ml' | 'blended' | 'heuristic';
    uncertainty?: number;
    features: any;
  }> {
    return this.request('/api/confidence/calculate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async recordConfidenceFeedback(request: {
    query: string;
    sources: any[];
    response: string;
    mode: string;
    actual_feedback: number;
    reasoning_steps?: number;
    has_memory?: boolean;
    cache_hit?: boolean;
    user_history?: any;
  }): Promise<{ status: string; message: string }> {
    return this.request('/api/confidence/feedback', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async trainConfidenceModel(learning_rate: number = 0.01, epochs: number = 100): Promise<{
    status: string;
    message: string;
    samples: number;
  }> {
    return this.request(
      `/api/confidence/train?learning_rate=${learning_rate}&epochs=${epochs}`,
      { method: 'POST' }
    );
  }

  async getConfidenceStats(): Promise<{
    model_exists: boolean;
    model_path: string;
    training_samples_pending: number;
    metadata: any;
  }> {
    return this.request('/api/confidence/stats');
  }

  // Feedback endpoints

  async submitFeedback(request: {
    message_id?: string;
    session_id?: string;
    rating: number;
    comment?: string;
  }): Promise<any> {
    return this.request('/api/feedback/submit', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getQualityStats(days: number = 7): Promise<{
    total_answers: number;
    average_score: number;
    quality_distribution: Record<string, number>;
    user_satisfaction: Record<string, number>;
    recent_trend: string;
  }> {
    return this.request(`/api/feedback/stats?days=${days}`);
  }

  async getFeedbackHistory(
    limit: number = 20,
    offset: number = 0,
    qualityLevel?: string
  ): Promise<any[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (qualityLevel) {
      params.append('quality_level', qualityLevel);
    }

    return this.request(`/api/feedback/history?${params.toString()}`);
  }

  // Additional methods for compatibility
  async getUserSessions(limit: number = 20, offset: number = 0): Promise<SessionListResponse> {
    return this.getSessions(limit, offset);
  }

  async sendQuery(query: string, sessionId: string, mode?: string): Promise<MessageResponse> {
    return this.request<MessageResponse>('/api/conversations/query', {
      method: 'POST',
      body: JSON.stringify({ 
        query, 
        session_id: sessionId, 
        mode: mode || 'balanced' 
      }),
    });
  }

  async sendMessage(sessionId: string, content: string): Promise<MessageResponse> {
    return this.request<MessageResponse>('/api/conversations/messages', {
      method: 'POST',
      body: JSON.stringify({ 
        session_id: sessionId, 
        content 
      }),
    });
  }

  async getCurrentUser(): Promise<any> {
    return this.request<any>('/api/auth/me');
  }
}

export const apiClient = new RAGApiClient();