/**
 * Workflow Templates
 * Pre-defined workflow templates with nodes and edges
 */

import type { Node, Edge } from 'reactflow';

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: string;
  nodes: Omit<Node, 'id'>[];
  edges: Omit<Edge, 'id'>[];
}

export const workflowTemplates: Record<string, WorkflowTemplate> = {
  'template-1': {
    id: 'template-1',
    name: 'Customer Support Automation',
    description: 'Classify and route customer inquiries automatically',
    category: 'Support',
    icon: '🎧',
    nodes: [
      {
        type: 'trigger',
        position: { x: 100, y: 100 },
        data: {
          name: 'Email Received',
          triggerType: 'email',
          description: 'Trigger when customer email arrives',
        },
      },
      {
        type: 'agent',
        position: { x: 100, y: 250 },
        data: {
          name: 'Classify Inquiry',
          description: 'Classify customer inquiry type',
          agentType: 'classifier',
        },
      },
      {
        type: 'condition',
        position: { x: 100, y: 400 },
        data: {
          name: 'Route by Type',
          condition: 'inquiry_type',
        },
      },
      {
        type: 'agent',
        position: { x: -150, y: 550 },
        data: {
          name: 'Technical Support',
          description: 'Handle technical issues',
          agentType: 'technical',
        },
      },
      {
        type: 'agent',
        position: { x: 100, y: 550 },
        data: {
          name: 'Billing Support',
          description: 'Handle billing questions',
          agentType: 'billing',
        },
      },
      {
        type: 'agent',
        position: { x: 350, y: 550 },
        data: {
          name: 'General Support',
          description: 'Handle general inquiries',
          agentType: 'general',
        },
      },
      {
        type: 'block',
        position: { x: 100, y: 700 },
        data: {
          name: 'Send Response',
          description: 'Send email response to customer',
        },
      },
      {
        type: 'end',
        position: { x: 100, y: 850 },
        data: {
          name: 'End',
        },
      },
    ],
    edges: [
      { source: 'node-0', target: 'node-1', type: 'custom' },
      { source: 'node-1', target: 'node-2', type: 'custom' },
      { source: 'node-2', target: 'node-3', type: 'custom', sourceHandle: 'false' },
      { source: 'node-2', target: 'node-4', type: 'custom', sourceHandle: 'true' },
      { source: 'node-2', target: 'node-5', type: 'custom', sourceHandle: 'default' },
      { source: 'node-3', target: 'node-6', type: 'custom' },
      { source: 'node-4', target: 'node-6', type: 'custom' },
      { source: 'node-5', target: 'node-6', type: 'custom' },
      { source: 'node-6', target: 'node-7', type: 'custom' },
    ],
  },
  'template-2': {
    id: 'template-2',
    name: 'Content Generation Pipeline',
    description: 'Generate, review, and publish content with AI',
    category: 'Content',
    icon: '✍️',
    nodes: [
      {
        type: 'trigger',
        position: { x: 250, y: 50 },
        data: {
          name: 'Schedule Trigger',
          triggerType: 'schedule',
          description: 'Run daily at 9 AM',
          schedule: '0 9 * * *',
        },
      },
      {
        type: 'agent',
        position: { x: 250, y: 200 },
        data: {
          name: 'Generate Content',
          description: 'AI generates blog post',
          agentType: 'writer',
        },
      },
      {
        type: 'agent',
        position: { x: 250, y: 350 },
        data: {
          name: 'Review Content',
          description: 'AI reviews for quality',
          agentType: 'reviewer',
        },
      },
      {
        type: 'condition',
        position: { x: 250, y: 500 },
        data: {
          name: 'Quality Check',
          condition: 'quality_score > 0.8',
        },
      },
      {
        type: 'tool',
        position: { x: 250, y: 650 },
        data: {
          name: 'Publish to CMS',
          description: 'Publish approved content',
        },
      },
      {
        type: 'end',
        position: { x: 250, y: 800 },
        data: {
          name: 'End',
        },
      },
    ],
    edges: [
      { source: 'node-0', target: 'node-1', type: 'custom' },
      { source: 'node-1', target: 'node-2', type: 'custom' },
      { source: 'node-2', target: 'node-3', type: 'custom' },
      { source: 'node-3', target: 'node-4', type: 'custom', sourceHandle: 'true' },
      { source: 'node-3', target: 'node-1', type: 'custom', sourceHandle: 'false' },
      { source: 'node-4', target: 'node-5', type: 'custom' },
    ],
  },
  'template-3': {
    id: 'template-3',
    name: 'Data Analysis Workflow',
    description: 'Fetch, analyze, and visualize data automatically',
    category: 'Analytics',
    icon: '📊',
    nodes: [
      {
        type: 'trigger',
        position: { x: 250, y: 50 },
        data: {
          name: 'Database Change',
          triggerType: 'database',
          description: 'Trigger on new data',
        },
      },
      {
        type: 'tool',
        position: { x: 250, y: 200 },
        data: {
          name: 'Fetch Data',
          description: 'Query database',
        },
      },
      {
        type: 'block',
        position: { x: 250, y: 350 },
        data: {
          name: 'Clean Data',
          description: 'Remove duplicates and nulls',
        },
      },
      {
        type: 'agent',
        position: { x: 250, y: 500 },
        data: {
          name: 'Analyze Data',
          description: 'AI analyzes patterns',
          agentType: 'analyst',
        },
      },
      {
        type: 'block',
        position: { x: 250, y: 650 },
        data: {
          name: 'Create Visualization',
          description: 'Generate charts',
        },
      },
      {
        type: 'tool',
        position: { x: 250, y: 800 },
        data: {
          name: 'Send Report',
          description: 'Email report to team',
        },
      },
      {
        type: 'end',
        position: { x: 250, y: 950 },
        data: {
          name: 'End',
        },
      },
    ],
    edges: [
      { source: 'node-0', target: 'node-1', type: 'custom' },
      { source: 'node-1', target: 'node-2', type: 'custom' },
      { source: 'node-2', target: 'node-3', type: 'custom' },
      { source: 'node-3', target: 'node-4', type: 'custom' },
      { source: 'node-4', target: 'node-5', type: 'custom' },
      { source: 'node-5', target: 'node-6', type: 'custom' },
    ],
  },
  'template-4': {
    id: 'template-4',
    name: 'Email Processing',
    description: 'Process incoming emails and create tasks',
    category: 'Automation',
    icon: '📧',
    nodes: [
      {
        type: 'trigger',
        position: { x: 250, y: 50 },
        data: {
          name: 'Email Received',
          triggerType: 'email',
          description: 'Monitor inbox',
        },
      },
      {
        type: 'agent',
        position: { x: 250, y: 200 },
        data: {
          name: 'Extract Information',
          description: 'Extract key details from email',
          agentType: 'extractor',
        },
      },
      {
        type: 'tool',
        position: { x: 250, y: 350 },
        data: {
          name: 'Create Task',
          description: 'Create task in project management tool',
        },
      },
      {
        type: 'agent',
        position: { x: 250, y: 500 },
        data: {
          name: 'Send Confirmation',
          description: 'Send confirmation email',
          agentType: 'responder',
        },
      },
      {
        type: 'end',
        position: { x: 250, y: 650 },
        data: {
          name: 'End',
        },
      },
    ],
    edges: [
      { source: 'node-0', target: 'node-1', type: 'custom' },
      { source: 'node-1', target: 'node-2', type: 'custom' },
      { source: 'node-2', target: 'node-3', type: 'custom' },
      { source: 'node-3', target: 'node-4', type: 'custom' },
    ],
  },
};

/**
 * Generate unique IDs for nodes and edges
 */
export function instantiateTemplate(templateId: string): {
  nodes: Node[];
  edges: Edge[];
} | null {
  const template = workflowTemplates[templateId];
  if (!template) return null;

  // Generate unique IDs for nodes
  const nodes: Node[] = template.nodes.map((node, index) => ({
    ...node,
    id: `node-${index}`,
  }));

  // Generate unique IDs for edges and map to actual node IDs
  const edges: Edge[] = template.edges.map((edge, index) => ({
    ...edge,
    id: `edge-${index}`,
  }));

  return { nodes, edges };
}

/**
 * Get template by ID
 */
export function getTemplate(templateId: string): WorkflowTemplate | null {
  return workflowTemplates[templateId] || null;
}

/**
 * Get all templates
 */
export function getAllTemplates(): WorkflowTemplate[] {
  return Object.values(workflowTemplates);
}
