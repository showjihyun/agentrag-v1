import type { Node, Edge } from 'reactflow';

export interface ValidationError {
  type: 'error' | 'warning';
  message: string;
  nodeId?: string;
}

export function validateWorkflow(nodes: Node[], edges: Edge[]): ValidationError[] {
  const errors: ValidationError[] = [];

  // Check for Start nodes - include all trigger types
  const startNodes = nodes.filter(n => 
    n.type === 'start' || 
    n.type === 'trigger' ||
    n.type?.startsWith('trigger_')
  );
  if (startNodes.length === 0) {
    errors.push({ 
      type: 'error', 
      message: 'Workflow must have at least one Start or Trigger node' 
    });
  }
  
  // Check for multiple Start nodes (excluding triggers)
  const pureStartNodes = nodes.filter(n => n.type === 'start');
  if (pureStartNodes.length > 1) {
    errors.push({ 
      type: 'warning', 
      message: 'Workflow has multiple Start nodes. Only one will be used.' 
    });
  }

  // Check for End nodes
  const endNodes = nodes.filter(n => n.type === 'end');
  if (endNodes.length === 0) {
    errors.push({ 
      type: 'warning', 
      message: 'Workflow should have at least one End node' 
    });
  }

  // Check for isolated nodes
  nodes.forEach(node => {
    const hasIncoming = edges.some(e => e.target === node.id);
    const hasOutgoing = edges.some(e => e.source === node.id);
    
    // Start nodes and all trigger types don't need incoming connections
    const isStartNode = node.type === 'start' || node.type === 'trigger' || node.type?.startsWith('trigger_');
    
    if (!hasIncoming && !isStartNode) {
      errors.push({ 
        type: 'warning', 
        message: `Node "${node.data?.name || node.id}" has no incoming connections`,
        nodeId: node.id 
      });
    }
    
    if (!hasOutgoing && node.type !== 'end') {
      errors.push({ 
        type: 'warning', 
        message: `Node "${node.data?.name || node.id}" has no outgoing connections`,
        nodeId: node.id 
      });
    }
  });

  // Check for condition nodes with missing branches
  const conditionNodes = nodes.filter(n => n.type === 'condition');
  conditionNodes.forEach(node => {
    const outgoingEdges = edges.filter(e => e.source === node.id);
    if (outgoingEdges.length < 2) {
      errors.push({
        type: 'warning',
        message: `Condition node "${node.data?.name || node.id}" should have both True and False branches`,
        nodeId: node.id
      });
    }
  });

  // Check for empty workflow
  if (nodes.length === 0) {
    errors.push({ 
      type: 'error', 
      message: 'Workflow is empty. Add at least one node.' 
    });
  }

  return errors;
}

export function getValidationSummary(errors: ValidationError[]): {
  hasErrors: boolean;
  hasWarnings: boolean;
  errorCount: number;
  warningCount: number;
} {
  const errorCount = errors.filter(e => e.type === 'error').length;
  const warningCount = errors.filter(e => e.type === 'warning').length;

  return {
    hasErrors: errorCount > 0,
    hasWarnings: warningCount > 0,
    errorCount,
    warningCount,
  };
}
