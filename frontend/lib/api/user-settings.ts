/**
 * User Settings API Client
 * 
 * Provides methods for managing user preferences:
 * - Notifications
 * - Security
 * - Appearance
 * - LLM configuration
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export type EmailDigestFrequency = 'realtime' | 'hourly' | 'daily' | 'weekly' | 'never';
export type TwoFactorMethod = 'app' | 'sms' | 'email';
export type ThemeMode = 'light' | 'dark' | 'system';

export interface NotificationSettings {
  email_enabled: boolean;
  email_address?: string;
  email_on_workflow_complete: boolean;
  email_on_workflow_error: boolean;
  email_on_agent_alert: boolean;
  email_digest_frequency: EmailDigestFrequency;
  
  in_app_enabled: boolean;
  in_app_on_workflow_complete: boolean;
  in_app_on_workflow_error: boolean;
  in_app_on_agent_alert: boolean;
  in_app_on_system_update: boolean;
  
  slack_enabled: boolean;
  slack_webhook_url?: string;
  slack_on_workflow_complete: boolean;
  slack_on_workflow_error: boolean;
  
  browser_enabled: boolean;
  browser_on_workflow_complete: boolean;
  browser_on_workflow_error: boolean;
}

export interface SecuritySettings {
  require_strong_password: boolean;
  password_min_length: number;
  
  session_timeout: number;
  single_session: boolean;
  
  two_factor_enabled: boolean;
  two_factor_method: TwoFactorMethod;
  
  api_rate_limit_enabled: boolean;
  api_rate_limit_requests: number;
  api_rate_limit_window: number;
  
  audit_logging_enabled: boolean;
  log_api_calls: boolean;
  log_workflow_executions: boolean;
  log_login_attempts: boolean;
}

export interface AppearanceSettings {
  theme: ThemeMode;
  accent_color: string;
  
  font_size: number;
  font_family: string;
  
  sidebar_collapsed: boolean;
  compact_mode: boolean;
  show_breadcrumbs: boolean;
  
  editor_font_size: number;
  editor_line_numbers: boolean;
  editor_word_wrap: boolean;
  editor_minimap: boolean;
  
  reduce_motion: boolean;
  high_contrast: boolean;
}

export interface LLMSettings {
  default_provider: string;
  default_model: string;
  
  ollama_enabled: boolean;
  ollama_base_url: string;
  ollama_default_model: string;
}

export interface AllUserSettings {
  notifications: NotificationSettings;
  security: SecuritySettings;
  appearance: AppearanceSettings;
  llm: LLMSettings;
  updated_at?: string;
}

// ============================================================================
// API Client
// ============================================================================

class UserSettingsAPI {
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

  // Get all settings
  async getAllSettings(): Promise<AllUserSettings> {
    return this.request('/api/agent-builder/user-settings');
  }

  // Update all settings
  async updateAllSettings(settings: AllUserSettings): Promise<AllUserSettings> {
    return this.request('/api/agent-builder/user-settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Notification settings
  async getNotificationSettings(): Promise<NotificationSettings> {
    return this.request('/api/agent-builder/user-settings/notifications');
  }

  async updateNotificationSettings(settings: NotificationSettings): Promise<NotificationSettings> {
    return this.request('/api/agent-builder/user-settings/notifications', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Security settings
  async getSecuritySettings(): Promise<SecuritySettings> {
    return this.request('/api/agent-builder/user-settings/security');
  }

  async updateSecuritySettings(settings: SecuritySettings): Promise<SecuritySettings> {
    return this.request('/api/agent-builder/user-settings/security', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Appearance settings
  async getAppearanceSettings(): Promise<AppearanceSettings> {
    return this.request('/api/agent-builder/user-settings/appearance');
  }

  async updateAppearanceSettings(settings: AppearanceSettings): Promise<AppearanceSettings> {
    return this.request('/api/agent-builder/user-settings/appearance', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // LLM settings
  async getLLMSettings(): Promise<LLMSettings> {
    return this.request('/api/agent-builder/user-settings/llm');
  }

  async updateLLMSettings(settings: LLMSettings): Promise<LLMSettings> {
    return this.request('/api/agent-builder/user-settings/llm', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }

  // Reset settings
  async resetSettings(category?: string): Promise<{ message: string }> {
    const params = category ? `?category=${category}` : '';
    return this.request(`/api/agent-builder/user-settings/reset${params}`, {
      method: 'POST',
    });
  }

  // Export settings
  async exportSettings(): Promise<{ user_id: string; exported_at: string; settings: any }> {
    return this.request('/api/agent-builder/user-settings/export', {
      method: 'POST',
    });
  }

  // Import settings
  async importSettings(settings: Record<string, any>): Promise<{ message: string }> {
    return this.request('/api/agent-builder/user-settings/import', {
      method: 'POST',
      body: JSON.stringify(settings),
    });
  }
}

export const userSettingsAPI = new UserSettingsAPI();

// ============================================================================
// Default Settings
// ============================================================================

export const defaultNotificationSettings: NotificationSettings = {
  email_enabled: true,
  email_address: '',
  email_on_workflow_complete: false,
  email_on_workflow_error: true,
  email_on_agent_alert: true,
  email_digest_frequency: 'daily',
  
  in_app_enabled: true,
  in_app_on_workflow_complete: true,
  in_app_on_workflow_error: true,
  in_app_on_agent_alert: true,
  in_app_on_system_update: true,
  
  slack_enabled: false,
  slack_webhook_url: '',
  slack_on_workflow_complete: false,
  slack_on_workflow_error: true,
  
  browser_enabled: false,
  browser_on_workflow_complete: false,
  browser_on_workflow_error: true,
};

export const defaultSecuritySettings: SecuritySettings = {
  require_strong_password: true,
  password_min_length: 8,
  
  session_timeout: 30,
  single_session: false,
  
  two_factor_enabled: false,
  two_factor_method: 'app',
  
  api_rate_limit_enabled: true,
  api_rate_limit_requests: 100,
  api_rate_limit_window: 60,
  
  audit_logging_enabled: true,
  log_api_calls: true,
  log_workflow_executions: true,
  log_login_attempts: true,
};

export const defaultAppearanceSettings: AppearanceSettings = {
  theme: 'system',
  accent_color: '#3b82f6',
  
  font_size: 14,
  font_family: 'system',
  
  sidebar_collapsed: false,
  compact_mode: false,
  show_breadcrumbs: true,
  
  editor_font_size: 14,
  editor_line_numbers: true,
  editor_word_wrap: true,
  editor_minimap: true,
  
  reduce_motion: false,
  high_contrast: false,
};

export const defaultLLMSettings: LLMSettings = {
  default_provider: 'openai',
  default_model: 'gpt-4o-mini',
  
  ollama_enabled: false,
  ollama_base_url: 'http://localhost:11434',
  ollama_default_model: 'llama3.1',
};
