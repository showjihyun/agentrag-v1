/**
 * Notifications API Client
 * 
 * Provides methods for managing notifications:
 * - In-app notifications
 * - Mark as read
 * - Notification preferences
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================================================
// Types
// ============================================================================

export type NotificationChannel = 'email' | 'slack' | 'in_app' | 'browser' | 'webhook' | 'pagerduty';
export type NotificationType = 'workflow_complete' | 'workflow_error' | 'agent_alert' | 'system_update' | 'security_alert' | 'quota_warning';
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent';

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  priority: NotificationPriority;
  data?: Record<string, unknown>;
  created_at: string;
  read: boolean;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
}

export interface SendNotificationRequest {
  type: NotificationType;
  title: string;
  message: string;
  channels: NotificationChannel[];
  priority?: NotificationPriority;
  data?: Record<string, unknown>;
}

// ============================================================================
// API Client
// ============================================================================

class NotificationsAPI {
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

  // Get all notifications
  async getNotifications(unreadOnly = false, limit = 50): Promise<NotificationListResponse> {
    const params = new URLSearchParams();
    if (unreadOnly) params.append('unread_only', 'true');
    params.append('limit', limit.toString());
    return this.request(`/api/notifications?${params}`);
  }

  // Get unread count
  async getUnreadCount(): Promise<{ count: number }> {
    return this.request('/api/notifications/unread-count');
  }

  // Mark notification as read
  async markAsRead(notificationId: string): Promise<{ success: boolean }> {
    return this.request(`/api/notifications/${notificationId}/read`, { method: 'POST' });
  }

  // Mark all as read
  async markAllAsRead(): Promise<{ count: number }> {
    return this.request('/api/notifications/read-all', { method: 'POST' });
  }

  // Delete notification
  async deleteNotification(notificationId: string): Promise<{ success: boolean }> {
    return this.request(`/api/notifications/${notificationId}`, { method: 'DELETE' });
  }

  // Send test notification
  async sendTestNotification(channel: NotificationChannel): Promise<{ success: boolean; message: string }> {
    return this.request('/api/notifications/test', {
      method: 'POST',
      body: JSON.stringify({ channel }),
    });
  }
}

export const notificationsAPI = new NotificationsAPI();
