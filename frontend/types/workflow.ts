import { Node, Edge } from 'reactflow';

// Tab types
export type WorkflowTabValue = 'canvas' | 'debug' | 'performance' | 'ai';

// Node status types
export type NodeStatus = 'idle' | 'running' | 'success' | 'error' | 'paused';

// Execution state
export interface ExecutionState {
  nodeId: string;
  timestamp: Date;
  status: NodeStatus;
  input?: any;
  output?: any;
  error?: string;
  duration?: number;
  memory?: number;
  cpu?: number;
}

// Breakpoint configuration
export interface BreakpointConfig {
  nodeId: string;
  enabled: boolean;
  condition?: string;
  hitCount?: number;
}

// Performance metrics
export interface NodeMetrics {
  nodeId: string;
  nodeName: string;
  executions: number;
  avgDuration: number;
  totalDuration: number;
  successRate: number;
  errorRate: number;
  avgMemory?: number;
  avgCpu?: number;
  isBottleneck?: boolean;
}

export interface PerformanceMetrics {
  totalDuration: number;
  avgDuration: number;
  successRate: number;
  errorRate: number;
  nodeMetrics: Record<string, NodeMetrics>;
}

// AI Assistant types
export interface ErrorDiagnosis {
  error_type: string;
  root_cause: string;
  explanation: string;
  suggested_fixes: string[];
  related_nodes: string[];
  confidence: number;
}

export interface BreakpointSuggestion {
  node_id: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  condition?: string;
}

export interface OptimizationSuggestion {
  node_id: string;
  issue: string;
  suggestion: string;
  expected_improvement: string;
  implementation_difficulty: 'easy' | 'medium' | 'hard';
  code_example?: string;
}

// Monitoring types
export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  active_workflows: number;
  total_executions: number;
  success_count: number;
  error_count: number;
  error_rate: number;
  avg_execution_time: number;
  cpu_percent: number;
  memory_mb: number;
  unacknowledged_alerts: number;
  timestamp: string;
}

export interface WorkflowStatus {
  workflow_id: string;
  status: string;
  current_node_id?: string;
  start_time: string;
  end_time?: string;
  progress_percent: number;
  completed_nodes: number;
  failed_nodes: number;
  total_nodes: number;
  estimated_completion?: string;
}

export interface Alert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  workflow_id: string;
  node_id?: string;
  timestamp: string;
  acknowledged: boolean;
  metadata?: Record<string, any>;
}

export interface ResourceHistory {
  timestamp: string;
  cpu_percent: number;
  memory_mb: number;
  active_workflows: number;
}

// Workflow canvas props
export interface WorkflowCanvasProps {
  workflowId?: string;
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
  onSave?: () => Promise<void>;
}

// Node data types
export interface AgentNodeData {
  label: string;
  description?: string;
  status: NodeStatus;
  agentType: string;
  executionTime?: number;
}

export interface ControlNodeData {
  label: string;
  description?: string;
  status: NodeStatus;
  controlType: string;
  executionTime?: number;
}

// Chat message types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
}

// API response types
export interface APIResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

// Workflow history types
export interface HistoryState {
  nodes: Node[];
  edges: Edge[];
  timestamp: Date;
}
