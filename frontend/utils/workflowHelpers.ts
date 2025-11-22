import { Node } from 'reactflow';
import { PerformanceMetrics, NodeMetrics } from '@/types/workflow';

/**
 * Calculate node-level metrics from performance data
 */
export function calculateNodeMetrics(
  metrics: PerformanceMetrics,
  nodes: Node[]
): Record<string, NodeMetrics> {
  const nodeMetrics: Record<string, NodeMetrics> = {};

  Object.entries(metrics.nodeMetrics).forEach(([nodeId, metric]) => {
    const node = nodes.find((n) => n.id === nodeId);
    nodeMetrics[nodeId] = {
      ...metric,
      nodeId,
      nodeName: node?.data.label || nodeId,
      errorRate: 100 - metric.successRate,
    };
  });

  return nodeMetrics;
}

/**
 * Find bottleneck nodes based on execution time
 */
export function findBottlenecks(
  nodeMetrics: Record<string, NodeMetrics>,
  threshold: number = 1000 // ms
): NodeMetrics[] {
  return Object.values(nodeMetrics)
    .filter((metric) => metric.avgDuration > threshold)
    .sort((a, b) => b.avgDuration - a.avgDuration);
}

/**
 * Calculate workflow completion percentage
 */
export function calculateProgress(
  completedNodes: string[],
  totalNodes: number
): number {
  if (totalNodes === 0) return 0;
  return Math.round((completedNodes.length / totalNodes) * 100);
}

/**
 * Format execution time for display
 */
export function formatExecutionTime(ms: number): string {
  if (ms < 1000) {
    return `${ms.toFixed(0)}ms`;
  } else if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  } else {
    const minutes = Math.floor(ms / 60000);
    const seconds = ((ms % 60000) / 1000).toFixed(0);
    return `${minutes}m ${seconds}s`;
  }
}

/**
 * Validate node connections
 */
export function validateConnections(nodes: Node[]): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  // Check for isolated nodes
  const isolatedNodes = nodes.filter(
    (node) => !node.data.inputs?.length && !node.data.outputs?.length
  );
  if (isolatedNodes.length > 0) {
    errors.push(
      `Found ${isolatedNodes.length} isolated node(s): ${isolatedNodes
        .map((n) => n.data.label)
        .join(', ')}`
    );
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Generate unique node ID
 */
export function generateNodeId(type: string): string {
  return `${type}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Deep clone nodes/edges for history
 */
export function cloneWorkflowState<T>(state: T): T {
  return JSON.parse(JSON.stringify(state));
}

/**
 * Check if node is a start node
 */
export function isStartNode(node: Node): boolean {
  return node.type === 'start' || node.data.isStart === true;
}

/**
 * Check if node is an end node
 */
export function isEndNode(node: Node): boolean {
  return node.type === 'end' || node.data.isEnd === true;
}

/**
 * Get execution path from start to end
 */
export function getExecutionPath(
  nodes: Node[],
  edges: any[]
): string[] {
  const startNode = nodes.find(isStartNode);
  if (!startNode) return [];

  const path: string[] = [startNode.id];
  let currentId = startNode.id;

  while (currentId) {
    const nextEdge = edges.find((e) => e.source === currentId);
    if (!nextEdge) break;

    currentId = nextEdge.target;
    path.push(currentId);

    const currentNode = nodes.find((n) => n.id === currentId);
    if (currentNode && isEndNode(currentNode)) break;
  }

  return path;
}
