// Event Store API Client

import { apiClient } from '../api-client';

export interface DomainEvent {
  aggregate_id: string;
  aggregate_type: string;
  event_type: string;
  event_data: Record<string, any>;
  user_id?: number;
  metadata?: Record<string, any>;
  timestamp: string;
  version: number;
}

export interface AuditLogFilters {
  userId?: number;
  aggregateType?: string;
  eventType?: string;
  fromDate?: Date;
  toDate?: Date;
  limit?: number;
}

export interface AuditLogResponse {
  events: DomainEvent[];
  total_count: number;
}

export class EventStoreAPI {
  /**
   * Get all events for an aggregate
   */
  async getAggregateEvents(
    aggregateId: string,
    aggregateType?: string,
    fromVersion: number = 0
  ): Promise<DomainEvent[]> {
    const params = new URLSearchParams({
      from_version: fromVersion.toString(),
    });
    
    if (aggregateType) {
      params.append('aggregate_type', aggregateType);
    }

    return apiClient['request'](
      `/api/events/aggregate/${aggregateId}?${params.toString()}`
    );
  }

  /**
   * Replay events up to a specific version (time-travel debugging)
   */
  async replayEvents(
    aggregateId: string,
    aggregateType: string,
    toVersion?: number
  ): Promise<DomainEvent[]> {
    const params = new URLSearchParams({
      aggregate_type: aggregateType,
    });
    
    if (toVersion !== undefined) {
      params.append('to_version', toVersion.toString());
    }

    return apiClient['request'](
      `/api/events/replay/${aggregateId}?${params.toString()}`
    );
  }

  /**
   * Get audit log with filters
   */
  async getAuditLog(filters: AuditLogFilters): Promise<AuditLogResponse> {
    const params = new URLSearchParams();
    
    if (filters.userId) params.append('user_id', filters.userId.toString());
    if (filters.aggregateType) params.append('aggregate_type', filters.aggregateType);
    if (filters.eventType) params.append('event_type', filters.eventType);
    if (filters.fromDate) params.append('from_date', filters.fromDate.toISOString());
    if (filters.toDate) params.append('to_date', filters.toDate.toISOString());
    if (filters.limit) params.append('limit', filters.limit.toString());

    return apiClient['request'](`/api/events/audit?${params.toString()}`);
  }
}

export const eventStoreAPI = new EventStoreAPI();
