/**
 * Chat History API Client
 * 
 * Provides methods for managing chat sessions and messages:
 * - Create/list/delete sessions
 * - Add/get messages
 * - Search history
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  agent_id?: string;
  title: string;
  metadata?: Record<string, unknown>;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateSessionRequest {
  agent_id?: string;
  title?: string;
  metadata?: Record<string, unknown>;
}

export interface AddMessageRequest {
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: Record<string, unknown>;
}

export interface SearchResult {
  message: ChatMessage;
  session: ChatSession;
}

// ============================================================================
// API Client
// ============================================================================

class ChatHistoryAPI {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Session management
  async createSession(request: CreateSessionRequest = {}): Promise<{ session_id: string }> {
    return this.request('/api/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async listSessions(limit = 50, offset = 0): Promise<{ sessions: ChatSession[]; total: number }> {
    return this.request(`/api/chat/sessions?limit=${limit}&offset=${offset}`);
  }

  async getSession(sessionId: string): Promise<ChatSession> {
    return this.request(`/api/chat/sessions/${sessionId}`);
  }

  async deleteSession(sessionId: string): Promise<{ success: boolean }> {
    return this.request(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
  }

  async updateSessionTitle(sessionId: string, title: string): Promise<{ success: boolean }> {
    return this.request(`/api/chat/sessions/${sessionId}/title`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    });
  }

  async clearSession(sessionId: string): Promise<{ success: boolean }> {
    return this.request(`/api/chat/sessions/${sessionId}/clear`, { method: 'POST' });
  }

  // Message management
  async addMessage(sessionId: string, request: AddMessageRequest): Promise<ChatMessage> {
    return this.request(`/api/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getMessages(sessionId: string, limit?: number): Promise<{ messages: ChatMessage[] }> {
    const params = limit ? `?limit=${limit}` : '';
    return this.request(`/api/chat/sessions/${sessionId}/messages${params}`);
  }

  // Search
  async searchMessages(query: string, limit = 20): Promise<{ results: SearchResult[] }> {
    return this.request(`/api/chat/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  }
}

export const chatHistoryAPI = new ChatHistoryAPI();
