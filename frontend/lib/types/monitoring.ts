// Enhanced type definitions for monitoring components

// Define missing types
export interface WorkflowMetrics {
  duration: number;
  nodeCount: number;
  executionTime: number;
  memoryUsage?: number;
  cpuUsage?: number;
  totalNodes: number;
  totalEdges: number;
  complexity: string;
  successRate?: number;
}

export interface AgentStatus {
  id: string;
  status: 'idle' | 'running' | 'error' | 'completed';
  lastUpdate: string;
}

export interface SystemMetrics {
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

export interface ExecutionPrediction {
  estimatedDuration: number;
  confidence: number;
  factors: string[];
}

export interface OptimizationInsight {
  type: 'performance' | 'cost' | 'reliability';
  description: string;
  impact: number;
  recommendation: string;
}

export interface SSEEventData<T = unknown> {
  type: string;
  payload: T;
}

export interface ExecutionCompletePayload {
  duration_ms: number;
  final_metrics?: WorkflowMetrics;
  [key: string]: unknown;
}

export interface ExecutionFailedPayload {
  error: string;
  [key: string]: unknown;
}

export interface MonitoringConfig {
  autoRefresh: boolean;
  refreshInterval: number;
  maxLogEntries: number;
  enablePredictions: boolean;
  enableOptimizations: boolean;
}

export interface FilterOptions {
  level: 'all' | 'info' | 'warning' | 'error' | 'success';
  agentId?: string;
  timeRange?: string;
}

// Types are defined above, no need to re-export from agent-builder