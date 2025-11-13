/**
 * Execution utilities for transforming workflow execution data
 */

export interface NodeExecution {
  nodeId: string;
  nodeName: string;
  nodeType: string;
  status: 'success' | 'error' | 'running' | 'pending';
  startTime?: string;
  endTime?: string;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
  retryCount?: number;
}

export interface ExecutionDetails {
  executionId: string;
  workflowName: string;
  status: 'running' | 'completed' | 'failed' | 'idle';
  startTime?: string;
  endTime?: string;
  totalDuration?: number;
  nodeExecutions: NodeExecution[];
}

/**
 * Transform workflow execution result to ExecutionDetails format
 */
export function transformExecutionResult(
  executionResult: any,
  workflowName: string,
  nodes: any[]
): ExecutionDetails {
  const nodeResults = executionResult.node_results || {};
  const retryCounts = executionResult.retry_counts || {};
  const executionContext = executionResult.execution_context || {};

  // Calculate total duration
  let totalDuration: number | undefined;
  if (executionContext.started_at && executionContext.completed_at) {
    const start = new Date(executionContext.started_at).getTime();
    const end = new Date(executionContext.completed_at).getTime();
    totalDuration = end - start;
  }

  // Transform node results
  const nodeExecutions: NodeExecution[] = Object.entries(nodeResults).map(
    ([nodeId, result]: [string, any]) => {
      const node = nodes.find((n) => n.id === nodeId);
      const nodeName = node?.data?.name || node?.data?.label || nodeId;
      const nodeType = node?.type || 'unknown';

      // Determine status
      let status: 'success' | 'error' | 'running' | 'pending' = 'success';
      let error: string | undefined;

      if (result && typeof result === 'object') {
        if (result.error) {
          status = 'error';
          error = result.error;
        } else if (result.status === 'error' || result.success === false) {
          status = 'error';
          error = result.error_message || result.message || 'Unknown error';
        }
      }

      return {
        nodeId,
        nodeName,
        nodeType,
        status,
        input: result?.input,
        output: result,
        error,
        retryCount: retryCounts[nodeId] || 0,
        duration: result?.duration_ms || result?.duration,
      };
    }
  );

  return {
    executionId: executionResult.execution_id || 'unknown',
    workflowName,
    status: executionResult.success ? 'completed' : 'failed',
    startTime: executionContext.started_at,
    endTime: executionContext.completed_at,
    totalDuration,
    nodeExecutions,
  };
}

/**
 * Format duration in milliseconds to human-readable string
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = ((ms % 60000) / 1000).toFixed(0);
  return `${minutes}m ${seconds}s`;
}

/**
 * Get status color class
 */
export function getStatusColor(status: string): string {
  switch (status) {
    case 'success':
    case 'completed':
      return 'text-green-500';
    case 'error':
    case 'failed':
      return 'text-red-500';
    case 'running':
      return 'text-blue-500';
    default:
      return 'text-gray-500';
  }
}

/**
 * Get status badge variant
 */
export function getStatusBadgeVariant(
  status: string
): 'default' | 'destructive' | 'secondary' | 'outline' {
  switch (status) {
    case 'success':
    case 'completed':
      return 'default';
    case 'error':
    case 'failed':
      return 'destructive';
    case 'running':
      return 'secondary';
    default:
      return 'outline';
  }
}
