import { Node, Edge } from 'reactflow';

export interface ValidationError {
  nodeId: string;
  nodeName: string;
  field?: string;
  message: string;
  severity: 'error' | 'warning';
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
}

/**
 * Validate a single node configuration
 */
export function validateNode(node: Node): ValidationError[] {
  const errors: ValidationError[] = [];
  const nodeName = node.data?.name || node.type || 'Unknown';

  switch (node.type) {
    case 'agent':
      if (!node.data?.agentId && !node.data?.agent_id) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'agentId',
          message: 'Agent must be selected',
          severity: 'error',
        });
      }
      break;

    case 'http_request':
      if (!node.data?.url) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'url',
          message: 'URL is required',
          severity: 'error',
        });
      } else if (!isValidUrl(node.data.url)) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'url',
          message: 'Invalid URL format',
          severity: 'error',
        });
      }

      if (!node.data?.method) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'method',
          message: 'HTTP method is required',
          severity: 'error',
        });
      }
      break;

    case 'condition':
      if (!node.data?.condition && !node.data?.expression) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'condition',
          message: 'Condition expression is required',
          severity: 'error',
        });
      }
      break;

    case 'code':
      if (!node.data?.code) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'code',
          message: 'Code is required',
          severity: 'error',
        });
      }
      break;

    case 'slack':
      if (!node.data?.channel && !node.data?.channelId) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'channel',
          message: 'Slack channel is required',
          severity: 'error',
        });
      }
      if (!node.data?.message) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'message',
          message: 'Message is required',
          severity: 'error',
        });
      }
      break;

    case 'discord':
      if (!node.data?.webhookUrl) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'webhookUrl',
          message: 'Discord webhook URL is required',
          severity: 'error',
        });
      }
      if (!node.data?.message) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'message',
          message: 'Message is required',
          severity: 'error',
        });
      }
      break;

    case 'email':
      if (!node.data?.to) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'to',
          message: 'Recipient email is required',
          severity: 'error',
        });
      } else if (!isValidEmail(node.data.to)) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'to',
          message: 'Invalid email format',
          severity: 'error',
        });
      }
      if (!node.data?.subject) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'subject',
          message: 'Email subject is required',
          severity: 'error',
        });
      }
      break;

    case 'database':
      if (!node.data?.query) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'query',
          message: 'Database query is required',
          severity: 'error',
        });
      }
      break;

    case 'delay':
      if (!node.data?.duration || node.data.duration <= 0) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'duration',
          message: 'Valid delay duration is required',
          severity: 'error',
        });
      }
      break;

    case 'loop':
      if (!node.data?.iterations && !node.data?.condition) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'iterations',
          message: 'Loop iterations or condition is required',
          severity: 'error',
        });
      }
      break;

    case 'webhook_trigger':
      if (!node.data?.path) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'path',
          message: 'Webhook path is required',
          severity: 'warning',
        });
      }
      break;

    case 'schedule_trigger':
      if (!node.data?.schedule && !node.data?.cron) {
        errors.push({
          nodeId: node.id,
          nodeName,
          field: 'schedule',
          message: 'Schedule or cron expression is required',
          severity: 'error',
        });
      }
      break;
  }

  return errors;
}

/**
 * Validate workflow structure
 */
export function validateWorkflow(nodes: Node[], edges: Edge[]): ValidationResult {
  const errors: ValidationError[] = [];
  const warnings: ValidationError[] = [];

  // Check for start node
  const startNodes = nodes.filter(n => n.type === 'start' || n.type === 'trigger');
  if (startNodes.length === 0) {
    errors.push({
      nodeId: '',
      nodeName: 'Workflow',
      message: 'Workflow must have a start or trigger node',
      severity: 'error',
    });
  } else if (startNodes.length > 1) {
    warnings.push({
      nodeId: '',
      nodeName: 'Workflow',
      message: 'Multiple start/trigger nodes detected',
      severity: 'warning',
    });
  }

  // Check for end node
  const endNodes = nodes.filter(n => n.type === 'end');
  if (endNodes.length === 0) {
    warnings.push({
      nodeId: '',
      nodeName: 'Workflow',
      message: 'Workflow should have at least one end node',
      severity: 'warning',
    });
  }

  // Check for disconnected nodes
  const connectedNodeIds = new Set<string>();
  edges.forEach(edge => {
    connectedNodeIds.add(edge.source);
    connectedNodeIds.add(edge.target);
  });

  nodes.forEach(node => {
    if (!connectedNodeIds.has(node.id) && node.type !== 'start' && node.type !== 'trigger') {
      warnings.push({
        nodeId: node.id,
        nodeName: node.data?.name || node.type || 'Unknown',
        message: 'Node is not connected to the workflow',
        severity: 'warning',
      });
    }
  });

  // Validate each node
  nodes.forEach(node => {
    const nodeErrors = validateNode(node);
    nodeErrors.forEach(error => {
      if (error.severity === 'error') {
        errors.push(error);
      } else {
        warnings.push(error);
      }
    });
  });

  // Check for circular dependencies (basic check)
  const hasCircularDependency = detectCircularDependency(nodes, edges);
  if (hasCircularDependency) {
    warnings.push({
      nodeId: '',
      nodeName: 'Workflow',
      message: 'Potential circular dependency detected',
      severity: 'warning',
    });
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Helper: Validate URL format
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    // Check if it's a relative URL or template
    return url.startsWith('/') || url.includes('{{') || url.includes('${');
  }
}

/**
 * Helper: Validate email format
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email) || email.includes('{{') || email.includes('${');
}

/**
 * Helper: Detect circular dependencies
 */
function detectCircularDependency(nodes: Node[], edges: Edge[]): boolean {
  const adjacencyList = new Map<string, string[]>();
  
  // Build adjacency list
  nodes.forEach(node => adjacencyList.set(node.id, []));
  edges.forEach(edge => {
    const neighbors = adjacencyList.get(edge.source) || [];
    neighbors.push(edge.target);
    adjacencyList.set(edge.source, neighbors);
  });

  // DFS to detect cycles
  const visited = new Set<string>();
  const recursionStack = new Set<string>();

  function hasCycle(nodeId: string): boolean {
    visited.add(nodeId);
    recursionStack.add(nodeId);

    const neighbors = adjacencyList.get(nodeId) || [];
    for (const neighbor of neighbors) {
      if (!visited.has(neighbor)) {
        if (hasCycle(neighbor)) return true;
      } else if (recursionStack.has(neighbor)) {
        return true;
      }
    }

    recursionStack.delete(nodeId);
    return false;
  }

  for (const node of nodes) {
    if (!visited.has(node.id)) {
      if (hasCycle(node.id)) return true;
    }
  }

  return false;
}

/**
 * Get validation summary for display
 */
export function getValidationSummary(result: ValidationResult): {
  hasErrors: boolean;
  hasWarnings: boolean;
  errorCount: number;
  warningCount: number;
  message: string;
} {
  const errorCount = result.errors.length;
  const warningCount = result.warnings.length;

  let message = '';
  if (errorCount > 0) {
    message = `${errorCount} error${errorCount > 1 ? 's' : ''} found`;
  }
  if (warningCount > 0) {
    if (message) message += ', ';
    message += `${warningCount} warning${warningCount > 1 ? 's' : ''} found`;
  }
  if (!message) {
    message = 'No issues found';
  }

  return {
    hasErrors: errorCount > 0,
    hasWarnings: warningCount > 0,
    errorCount,
    warningCount,
    message,
  };
}
