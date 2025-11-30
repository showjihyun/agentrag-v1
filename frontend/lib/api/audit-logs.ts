/**
 * Audit Logs API Client
 * 
 * Provides methods for viewing and managing audit logs.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export interface AuditLogEntry {
  id: string;
  event_type: string;
  severity: string;
  action: string;
  user_id?: string;
  user_email?: string;
  ip_address?: string;
  resource_type?: string;
  resource_id?: string;
  details: Record<string, any>;
  success: boolean;
  error_message?: string;
  timestamp: string;
}

export interface AuditLogListResponse {
  logs: AuditLogEntry[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface AuditLogStats {
  total_events: number;
  events_by_type: Record<string, number>;
  events_by_severity: Record<string, number>;
  events_by_user: Record<string, number>;
  success_rate: number;
  time_range: {
    start: string;
    end: string;
    days: number;
  };
}

export interface AuditLogFilters {
  page?: number;
  page_size?: number;
  event_type?: string;
  severity?: string;
  user_id?: string;
  resource_type?: string;
  resource_id?: string;
  success?: boolean;
  start_date?: string;
  end_date?: string;
}

export interface EventType {
  value: string;
  name: string;
}

export interface Severity {
  value: string;
  name: string;
}

// ============================================================================
// API Client
// ============================================================================

class AuditLogsAPI {
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

  // List audit logs with filters
  async listLogs(filters: AuditLogFilters = {}): Promise<AuditLogListResponse> {
    const params = new URLSearchParams();
    
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.event_type) params.append('event_type', filters.event_type);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.user_id) params.append('user_id', filters.user_id);
    if (filters.resource_type) params.append('resource_type', filters.resource_type);
    if (filters.resource_id) params.append('resource_id', filters.resource_id);
    if (filters.success !== undefined) params.append('success', filters.success.toString());
    if (filters.start_date) params.append('start_date', filters.start_date);
    if (filters.end_date) params.append('end_date', filters.end_date);
    
    const query = params.toString();
    return this.request(`/api/agent-builder/audit-logs${query ? `?${query}` : ''}`);
  }

  // Get single log entry
  async getLog(logId: string): Promise<AuditLogEntry> {
    return this.request(`/api/agent-builder/audit-logs/${logId}`);
  }

  // Get statistics
  async getStats(days: number = 7): Promise<AuditLogStats> {
    return this.request(`/api/agent-builder/audit-logs/stats?days=${days}`);
  }

  // Get available event types
  async getEventTypes(): Promise<{ event_types: EventType[] }> {
    return this.request('/api/agent-builder/audit-logs/event-types');
  }

  // Get available severities
  async getSeverities(): Promise<{ severities: Severity[] }> {
    return this.request('/api/agent-builder/audit-logs/severities');
  }

  // Cleanup old logs (admin only)
  async cleanupLogs(days: number = 90): Promise<{ message: string; deleted_count: number; remaining_count: number }> {
    return this.request(`/api/agent-builder/audit-logs/cleanup?days=${days}`, {
      method: 'DELETE',
    });
  }

  // Export logs (admin only)
  async exportLogs(options: {
    start_date?: string;
    end_date?: string;
    format?: 'json' | 'csv';
  } = {}): Promise<{ format: string; count: number; data: any }> {
    const params = new URLSearchParams();
    if (options.start_date) params.append('start_date', options.start_date);
    if (options.end_date) params.append('end_date', options.end_date);
    if (options.format) params.append('format', options.format);
    
    const query = params.toString();
    return this.request(`/api/agent-builder/audit-logs/export${query ? `?${query}` : ''}`, {
      method: 'POST',
    });
  }
}

export const auditLogsAPI = new AuditLogsAPI();

// ============================================================================
// Helpers
// ============================================================================

export function formatEventType(eventType: string): string {
  // Convert "auth.login.success" to "Auth Login Success"
  return eventType
    .split('.')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'debug':
      return 'text-gray-500';
    case 'info':
      return 'text-blue-500';
    case 'warning':
      return 'text-yellow-500';
    case 'error':
      return 'text-red-500';
    case 'critical':
      return 'text-red-700';
    default:
      return 'text-gray-500';
  }
}

export function getSeverityBadgeVariant(severity: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (severity) {
    case 'error':
    case 'critical':
      return 'destructive';
    case 'warning':
      return 'secondary';
    default:
      return 'outline';
  }
}

export function getEventTypeIcon(eventType: string): string {
  if (eventType.startsWith('auth.')) return '🔐';
  if (eventType.startsWith('user.')) return '👤';
  if (eventType.startsWith('workflow.')) return '⚡';
  if (eventType.startsWith('resource.')) return '📁';
  if (eventType.startsWith('api_key.')) return '🔑';
  if (eventType.startsWith('config.')) return '⚙️';
  if (eventType.startsWith('security.')) return '🛡️';
  return '📋';
}
