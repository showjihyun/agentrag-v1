/**
 * Workflow Monitoring API Client
 * 
 * API client for workflow monitoring, alerts, and DLQ management.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function for API requests
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }
  
  return response.json();
}

// Types
export interface MetricsSummary {
  total_executions: number;
  active_executions: number;
  total_errors: number;
  cache_hit_rate: number;
}

export interface Alert {
  id: string;
  alert_type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  workflow_id?: string;
  node_id?: string;
  metric_value?: number;
  threshold?: number;
  created_at: string;
  acknowledged: boolean;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved: boolean;
  resolved_at?: string;
}

export interface AlertStats {
  total_alerts: number;
  active_alerts: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}

export interface DLQEntry {
  id: string;
  execution_id: string;
  workflow_id: string;
  error_message: string;
  error_type: string;
  input_data: Record<string, any>;
  execution_context: Record<string, any>;
  metadata: Record<string, any>;
  status: 'pending' | 'retrying' | 'resolved' | 'discarded';
  retry_count: number;
  max_retries: number;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  resolution_notes?: string;
}

export interface DLQStats {
  total: number;
  by_status: Record<string, number>;
  by_error_type: Record<string, number>;
  by_workflow: Record<string, number>;
  oldest_pending?: string;
}

export interface WorkflowStats {
  workflow_id: string;
  sample_count: number;
  avg_duration: number;
  median_duration: number;
  min_duration: number;
  max_duration: number;
  std_deviation: number;
  p95_duration: number;
  p99_duration: number;
}

export interface NodeStats {
  [nodeId: string]: {
    sample_count: number;
    avg_duration: number;
    median_duration: number;
    max_duration: number;
    p95_duration: number;
  };
}

export interface Bottleneck {
  node_id: string;
  avg_duration: number;
  percentage_of_total: number;
  recommendation: string;
}

export interface Checkpoint {
  id: string;
  execution_id: string;
  workflow_id: string;
  checkpoint_type: string;
  name: string;
  current_node_id?: string;
  completed_nodes: string[];
  node_results: Record<string, any>;
  execution_data: Record<string, any>;
  created_at: string;
  metadata: Record<string, any>;
}

// API Functions

/**
 * Get monitoring dashboard data
 */
export async function getDashboard(workflowId?: string) {
  const params = new URLSearchParams();
  if (workflowId) params.append('workflow_id', workflowId);
  const query = params.toString() ? `?${params.toString()}` : '';
  
  return apiRequest<{
    metrics_summary: MetricsSummary;
    active_alerts: Alert[];
    alert_stats: AlertStats;
    workflow_stats?: WorkflowStats;
    node_stats?: NodeStats;
    bottlenecks?: Bottleneck[];
    regression?: { detected: boolean; previous_avg?: number; recent_avg?: number; increase_percentage?: number };
  }>(`/api/agent-builder/monitoring/v2/dashboard${query}`);
}

/**
 * Get metrics
 */
export async function getMetrics(format: 'json' | 'prometheus' = 'json') {
  return apiRequest<{
    summary: MetricsSummary;
    metrics: any[];
  }>(`/api/agent-builder/monitoring/v2/metrics?format=${format}`);
}

/**
 * Get metrics summary
 */
export async function getMetricsSummary() {
  return apiRequest<MetricsSummary>('/api/agent-builder/monitoring/metrics/summary');
}

// Performance APIs

/**
 * Get workflow performance analysis
 */
export async function getWorkflowPerformance(workflowId: string) {
  return apiRequest<{
    workflow_stats: WorkflowStats;
    node_stats: NodeStats;
    bottlenecks: Bottleneck[];
    regression: { detected: boolean; previous_avg?: number; recent_avg?: number; increase_percentage?: number } | null;
  }>(`/api/agent-builder/monitoring/v2/performance/${workflowId}`);
}

/**
 * Get node-level performance stats
 */
export async function getNodePerformance(workflowId: string) {
  return apiRequest<NodeStats>(`/api/agent-builder/monitoring/v2/performance/${workflowId}/nodes`);
}

/**
 * Get performance bottlenecks
 */
export async function getBottlenecks(workflowId: string) {
  return apiRequest<Bottleneck[]>(`/api/agent-builder/monitoring/v2/performance/${workflowId}/bottlenecks`);
}

// Alert APIs

/**
 * Get alerts
 */
export async function getAlerts(params?: {
  severity?: string;
  workflow_id?: string;
  include_resolved?: boolean;
  limit?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.severity) searchParams.append('severity', params.severity);
  if (params?.workflow_id) searchParams.append('workflow_id', params.workflow_id);
  if (params?.include_resolved) searchParams.append('include_resolved', String(params.include_resolved));
  if (params?.limit) searchParams.append('limit', String(params.limit));
  const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
  
  return apiRequest<{ alerts: Alert[]; total: number }>(`/api/agent-builder/monitoring/v2/alerts${query}`);
}

/**
 * Get alert statistics
 */
export async function getAlertStats() {
  return apiRequest<AlertStats>('/api/agent-builder/monitoring/alerts/stats');
}

/**
 * Acknowledge an alert
 */
export async function acknowledgeAlert(alertId: string, acknowledgedBy: string) {
  return apiRequest<Alert>(`/api/agent-builder/monitoring/alerts/${alertId}/acknowledge`, {
    method: 'POST',
    body: JSON.stringify({ acknowledged_by: acknowledgedBy }),
  });
}

/**
 * Resolve an alert
 */
export async function resolveAlert(alertId: string) {
  return apiRequest<Alert>(`/api/agent-builder/monitoring/v2/alerts/${alertId}/resolve`, {
    method: 'POST',
  });
}

/**
 * Update alert threshold
 */
export async function updateAlertThreshold(
  alertType: string,
  thresholds: {
    warning_threshold: number;
    error_threshold: number;
    critical_threshold: number;
    window_minutes?: number;
  }
) {
  return apiRequest<{ status: string; alert_type: string }>(
    `/api/agent-builder/monitoring/alerts/thresholds/${alertType}`,
    { method: 'PUT', body: JSON.stringify(thresholds) }
  );
}

// DLQ APIs

/**
 * Get DLQ entries
 */
export async function getDLQEntries(params?: {
  status?: string;
  workflow_id?: string;
  limit?: number;
  offset?: number;
}) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.append('status', params.status);
  if (params?.workflow_id) searchParams.append('workflow_id', params.workflow_id);
  if (params?.limit) searchParams.append('limit', String(params.limit));
  if (params?.offset) searchParams.append('offset', String(params.offset));
  const query = searchParams.toString() ? `?${searchParams.toString()}` : '';
  
  return apiRequest<{ entries: DLQEntry[]; total: number }>(`/api/agent-builder/monitoring/v2/dlq${query}`);
}

/**
 * Get DLQ statistics
 */
export async function getDLQStats() {
  return apiRequest<DLQStats>('/api/agent-builder/monitoring/v2/dlq/stats');
}

/**
 * Get a specific DLQ entry
 */
export async function getDLQEntry(entryId: string) {
  return apiRequest<DLQEntry>(`/api/agent-builder/monitoring/v2/dlq/${entryId}`);
}

/**
 * Retry a DLQ entry
 */
export async function retryDLQEntry(entryId: string, force: boolean = false) {
  return apiRequest<{
    entry_id: string;
    decision: string;
    success: boolean;
    message: string;
    retry_scheduled_at?: string;
  }>(`/api/agent-builder/monitoring/v2/dlq/${entryId}/retry`, {
    method: 'POST',
    body: JSON.stringify({ force }),
  });
}

/**
 * Resolve a DLQ entry
 */
export async function resolveDLQEntry(entryId: string, notes?: string, discard: boolean = false) {
  return apiRequest<DLQEntry>(`/api/agent-builder/monitoring/v2/dlq/${entryId}/resolve`, {
    method: 'POST',
    body: JSON.stringify({ notes, discard }),
  });
}

/**
 * Process pending DLQ entries
 */
export async function processPendingDLQ(limit: number = 10, workflowId?: string) {
  const searchParams = new URLSearchParams();
  searchParams.append('limit', String(limit));
  if (workflowId) searchParams.append('workflow_id', workflowId);
  
  return apiRequest<{
    processed: number;
    results: Array<{
      entry_id: string;
      decision: string;
      success: boolean;
      message: string;
    }>;
  }>(`/api/agent-builder/monitoring/v2/dlq/process-pending?${searchParams.toString()}`, {
    method: 'POST',
  });
}

/**
 * Get DLQ processor stats
 */
export async function getDLQProcessorStats() {
  return apiRequest<{
    processed_count: number;
    retry_count: number;
    discard_count: number;
    manual_count: number;
    pending_retries: number;
    is_processing: boolean;
  }>('/api/agent-builder/monitoring/dlq/processor/stats');
}

/**
 * Get retry schedule
 */
export async function getRetrySchedule() {
  return apiRequest<Array<{
    entry_id: string;
    scheduled_at: string;
    delay_seconds: number;
  }>>('/api/agent-builder/monitoring/dlq/processor/schedule');
}

// Checkpoint APIs

/**
 * Get checkpoints for an execution
 */
export async function getCheckpoints(executionId: string) {
  return apiRequest<{
    execution_id: string;
    checkpoints: Checkpoint[];
    total: number;
  }>(`/api/agent-builder/monitoring/v2/checkpoints/${executionId}`);
}

/**
 * Get latest checkpoint
 */
export async function getLatestCheckpoint(executionId: string, checkpointType?: string) {
  const query = checkpointType ? `?checkpoint_type=${checkpointType}` : '';
  return apiRequest<Checkpoint>(`/api/agent-builder/monitoring/v2/checkpoints/${executionId}/latest${query}`);
}

/**
 * Delete a checkpoint
 */
export async function deleteCheckpoint(checkpointId: string) {
  return apiRequest<{ deleted: boolean }>(`/api/agent-builder/monitoring/v2/checkpoints/${checkpointId}`, {
    method: 'DELETE',
  });
}

// Health check

/**
 * Check monitoring system health
 */
export async function checkMonitoringHealth() {
  return apiRequest<{
    status: string;
    components: Record<string, string>;
    summary: {
      active_alerts: number;
      dlq_pending: number;
      total_executions: number;
    };
  }>('/api/agent-builder/monitoring/v2/health');
}

// React Query hooks (optional, for use with TanStack Query)

export const monitoringQueryKeys = {
  dashboard: (workflowId?: string) => ['monitoring', 'dashboard', workflowId] as const,
  metrics: ['monitoring', 'metrics'] as const,
  metricsSummary: ['monitoring', 'metrics', 'summary'] as const,
  performance: (workflowId: string) => ['monitoring', 'performance', workflowId] as const,
  alerts: (params?: any) => ['monitoring', 'alerts', params] as const,
  alertStats: ['monitoring', 'alerts', 'stats'] as const,
  dlq: (params?: any) => ['monitoring', 'dlq', params] as const,
  dlqStats: ['monitoring', 'dlq', 'stats'] as const,
  dlqEntry: (entryId: string) => ['monitoring', 'dlq', entryId] as const,
  checkpoints: (executionId: string) => ['monitoring', 'checkpoints', executionId] as const,
  health: ['monitoring', 'health'] as const,
};
