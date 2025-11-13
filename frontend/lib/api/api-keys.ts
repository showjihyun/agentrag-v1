/**
 * API client for managing user API keys
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface APIKey {
  id: string;
  service_name: string;
  service_display_name: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_used_at?: string;
  usage_count: number;
}

export interface APIKeyCreate {
  service_name: string;
  service_display_name: string;
  api_key: string;
  description?: string;
}

export interface APIKeyUpdate {
  api_key?: string;
  description?: string;
  is_active?: boolean;
}

export interface APIKeyTestResult {
  success: boolean;
  message: string;
  service_name: string;
  details?: {
    masked_key?: string;
    last_used?: string;
    usage_count?: number;
  };
}

class APIKeysAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
      ...options.headers,
    };

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async listAPIKeys(includeInactive = false): Promise<{ api_keys: APIKey[]; total: number }> {
    const params = new URLSearchParams();
    if (includeInactive) params.append('include_inactive', 'true');
    
    const query = params.toString();
    return this.request(`/api/agent-builder/api-keys${query ? `?${query}` : ''}`);
  }

  async getAPIKey(apiKeyId: string): Promise<APIKey> {
    return this.request(`/api/agent-builder/api-keys/${apiKeyId}`);
  }

  async createAPIKey(data: APIKeyCreate): Promise<APIKey> {
    return this.request('/api/agent-builder/api-keys', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAPIKey(apiKeyId: string, data: APIKeyUpdate): Promise<APIKey> {
    return this.request(`/api/agent-builder/api-keys/${apiKeyId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAPIKey(apiKeyId: string): Promise<void> {
    await this.request(`/api/agent-builder/api-keys/${apiKeyId}`, {
      method: 'DELETE',
    });
  }

  async testAPIKey(serviceName: string): Promise<APIKeyTestResult> {
    return this.request(`/api/agent-builder/api-keys/test/${serviceName}`, {
      method: 'POST',
    });
  }
}

export const apiKeysAPI = new APIKeysAPI();

// Service definitions with icons and descriptions
export const SUPPORTED_SERVICES = [
  {
    name: 'youtube',
    displayName: 'YouTube Data API',
    icon: '📺',
    color: '#FF0000',
    description: 'Search YouTube videos and channels',
    docsUrl: 'https://developers.google.com/youtube/v3/getting-started',
    getKeyUrl: 'https://console.cloud.google.com/apis/credentials',
  },
  {
    name: 'google',
    displayName: 'Google Search API',
    icon: '🔍',
    color: '#4285F4',
    description: 'Search the web using Google Custom Search',
    docsUrl: 'https://developers.google.com/custom-search/v1/overview',
    getKeyUrl: 'https://console.cloud.google.com/apis/credentials',
  },
  {
    name: 'openai',
    displayName: 'OpenAI API',
    icon: '🤖',
    color: '#10A37F',
    description: 'Access GPT models and other OpenAI services',
    docsUrl: 'https://platform.openai.com/docs/api-reference',
    getKeyUrl: 'https://platform.openai.com/api-keys',
  },
  {
    name: 'anthropic',
    displayName: 'Anthropic Claude API',
    icon: '🧠',
    color: '#D97757',
    description: 'Access Claude AI models',
    docsUrl: 'https://docs.anthropic.com/claude/reference/getting-started-with-the-api',
    getKeyUrl: 'https://console.anthropic.com/settings/keys',
  },
  {
    name: 'newsapi',
    displayName: 'NewsAPI',
    icon: '📰',
    color: '#FF6B6B',
    description: 'Search news articles from various sources',
    docsUrl: 'https://newsapi.org/docs',
    getKeyUrl: 'https://newsapi.org/register',
  },
  {
    name: 'openweathermap',
    displayName: 'OpenWeatherMap',
    icon: '🌤️',
    color: '#EB6E4B',
    description: 'Get weather data and forecasts',
    docsUrl: 'https://openweathermap.org/api',
    getKeyUrl: 'https://home.openweathermap.org/api_keys',
  },
] as const;

export function getServiceInfo(serviceName: string) {
  return SUPPORTED_SERVICES.find(s => s.name === serviceName);
}
