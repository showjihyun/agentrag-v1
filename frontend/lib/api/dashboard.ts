/**
 * Dashboard API Client
 * 
 * Provides methods for managing dashboard layouts:
 * - Get/save layouts
 * - Widget management
 * - Reset to default
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface DashboardWidget {
  id: string;
  type: string;
  title: string;
  x: number;
  y: number;
  width: number;
  height: number;
  config?: Record<string, unknown>;
}

export interface DashboardLayout {
  user_id: string;
  widgets: DashboardWidget[];
  theme: string;
  columns: number;
  row_height: number;
  created_at: string;
  updated_at: string;
}

export interface AddWidgetRequest {
  type: string;
  title: string;
  config?: Record<string, unknown>;
}

export interface UpdateWidgetRequest {
  title?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  config?: Record<string, unknown>;
}

// Widget types
export const WIDGET_TYPES = {
  WORKFLOW_STATS: 'workflow_stats',
  RECENT_EXECUTIONS: 'recent_executions',
  SYSTEM_HEALTH: 'system_health',
  QUICK_ACTIONS: 'quick_actions',
  NOTIFICATIONS: 'notifications',
  AGENT_PERFORMANCE: 'agent_performance',
  ERROR_RATE: 'error_rate',
  RESOURCE_USAGE: 'resource_usage',
} as const;

// ============================================================================
// API Client
// ============================================================================

class DashboardAPI {
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

  // Get dashboard layout
  async getLayout(): Promise<DashboardLayout> {
    return this.request('/api/dashboard/layout');
  }

  // Save dashboard layout
  async saveLayout(layout: Partial<DashboardLayout>): Promise<{ success: boolean }> {
    return this.request('/api/dashboard/layout', {
      method: 'PUT',
      body: JSON.stringify(layout),
    });
  }

  // Reset to default layout
  async resetLayout(): Promise<DashboardLayout> {
    return this.request('/api/dashboard/layout/reset', { method: 'POST' });
  }

  // Add widget
  async addWidget(request: AddWidgetRequest): Promise<DashboardWidget> {
    return this.request('/api/dashboard/widgets', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Update widget
  async updateWidget(widgetId: string, updates: UpdateWidgetRequest): Promise<DashboardWidget> {
    return this.request(`/api/dashboard/widgets/${widgetId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Remove widget
  async removeWidget(widgetId: string): Promise<{ success: boolean }> {
    return this.request(`/api/dashboard/widgets/${widgetId}`, { method: 'DELETE' });
  }
}

export const dashboardAPI = new DashboardAPI();
