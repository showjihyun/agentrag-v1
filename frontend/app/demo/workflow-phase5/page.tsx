'use client';

import { useState } from 'react';
import { Phase5WorkflowCanvas } from '@/components/agent-builder/workflow/Phase5WorkflowCanvas';
import { Node, Edge } from 'reactflow';

// Sample workflow data
const initialNodes: Node[] = [
  {
    id: '1',
    type: 'agent',
    position: { x: 100, y: 100 },
    data: {
      label: 'Data Fetcher',
      description: 'Fetch data from API',
      status: 'idle',
      agentType: 'data',
    },
  },
  {
    id: '2',
    type: 'agent',
    position: { x: 100, y: 250 },
    data: {
      label: 'Data Processor',
      description: 'Process and transform data',
      status: 'idle',
      agentType: 'transform',
    },
  },
  {
    id: '3',
    type: 'control',
    position: { x: 100, y: 400 },
    data: {
      label: 'Condition Check',
      description: 'Check if data is valid',
      status: 'idle',
      controlType: 'condition',
    },
  },
  {
    id: '4',
    type: 'agent',
    position: { x: 300, y: 400 },
    data: {
      label: 'Success Handler',
      description: 'Handle successful processing',
      status: 'idle',
      agentType: 'output',
    },
  },
  {
    id: '5',
    type: 'agent',
    position: { x: -100, y: 400 },
    data: {
      label: 'Error Handler',
      description: 'Handle errors',
      status: 'idle',
      agentType: 'error',
    },
  },
];

const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    type: 'animated',
  },
  {
    id: 'e2-3',
    source: '2',
    target: '3',
    type: 'animated',
  },
  {
    id: 'e3-4',
    source: '3',
    target: '4',
    type: 'animated',
    label: 'success',
  },
  {
    id: 'e3-5',
    source: '3',
    target: '5',
    type: 'animated',
    label: 'error',
  },
];

export default function WorkflowPhase5DemoPage() {
  const [nodes, setNodes] = useState<Node[]>(initialNodes);
  const [edges, setEdges] = useState<Edge[]>(initialEdges);

  const handleSave = async () => {
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 1000));
    console.log('Workflow saved:', { nodes, edges });
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 border-b bg-background">
        <h1 className="text-2xl font-bold">Workflow Phase 5 - AI Assistant</h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI-powered debugging, optimization suggestions, and natural language queries
        </p>
      </div>
      <div className="flex-1">
        <Phase5WorkflowCanvas
          workflowId="demo-workflow"
          initialNodes={nodes}
          initialEdges={edges}
          onNodesChange={setNodes}
          onEdgesChange={setEdges}
          onSave={handleSave}
        />
      </div>
    </div>
  );
}
