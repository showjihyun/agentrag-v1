'use client';

import { RefactoredPhase5Canvas } from './RefactoredPhase5Canvas';
import { Node, Edge } from 'reactflow';

const demoNodes: Node[] = [
  {
    id: '1',
    type: 'agent',
    position: { x: 250, y: 50 },
    data: {
      label: 'Start Agent',
      description: 'Initial processing',
      status: 'idle',
      agentType: 'processor',
    },
  },
  {
    id: '2',
    type: 'agent',
    position: { x: 250, y: 200 },
    data: {
      label: 'Data Transformer',
      description: 'Transform input data',
      status: 'idle',
      agentType: 'transformer',
    },
  },
  {
    id: '3',
    type: 'control',
    position: { x: 250, y: 350 },
    data: {
      label: 'Decision Point',
      description: 'Route based on condition',
      status: 'idle',
      controlType: 'condition',
    },
  },
];

const demoEdges: Edge[] = [
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
];

export function Phase2RefactoredDemo() {
  return (
    <div className="h-screen w-full">
      <RefactoredPhase5Canvas
        workflowId="demo-refactored"
        initialNodes={demoNodes}
        initialEdges={demoEdges}
        onNodesChange={(nodes) => {
          console.log('Nodes changed:', nodes.length);
        }}
        onEdgesChange={(edges) => {
          console.log('Edges changed:', edges.length);
        }}
        onSave={async () => {
          console.log('Saving workflow...');
          await new Promise((resolve) => setTimeout(resolve, 1000));
          console.log('Workflow saved!');
        }}
      />
    </div>
  );
}
