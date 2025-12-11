'use client';

import { useState } from 'react';
import { Phase2WorkflowCanvas } from '@/components/agent-builder/workflow/Phase2WorkflowCanvas';
import { Node, Edge } from 'reactflow';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sparkles, FileText } from 'lucide-react';

// Sample workflow data
const sampleNodes: Node[] = [
  {
    id: '1',
    type: 'agent',
    position: { x: 100, y: 100 },
    data: {
      label: 'Data Collector',
      description: 'Collects data from various sources',
      status: 'idle',
      tags: ['data', 'input'],
    },
  },
  {
    id: '2',
    type: 'agent',
    position: { x: 400, y: 100 },
    data: {
      label: 'Data Processor',
      description: 'Processes and transforms data',
      status: 'idle',
      tags: ['processing', 'transform'],
    },
  },
  {
    id: '3',
    type: 'control',
    position: { x: 700, y: 100 },
    data: {
      label: 'Quality Check',
      description: 'Validates data quality',
      controlType: 'conditional',
      condition: 'quality > 0.8',
      status: 'idle',
      tags: ['validation', 'control'],
    },
  },
  {
    id: '4',
    type: 'agent',
    position: { x: 1000, y: 50 },
    data: {
      label: 'Success Handler',
      description: 'Handles successful processing',
      status: 'idle',
      tags: ['output', 'success'],
    },
  },
  {
    id: '5',
    type: 'agent',
    position: { x: 1000, y: 200 },
    data: {
      label: 'Error Handler',
      description: 'Handles processing errors',
      status: 'idle',
      tags: ['output', 'error'],
    },
  },
];

const sampleEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', type: 'animated' },
  { id: 'e2-3', source: '2', target: '3', type: 'animated' },
  { id: 'e3-4', source: '3', target: '4', sourceHandle: 'true', type: 'animated' },
  { id: 'e3-5', source: '3', target: '5', sourceHandle: 'false', type: 'animated' },
];

export default function WorkflowPhase2Demo() {
  const [nodes, setNodes] = useState<Node[]>(sampleNodes);
  const [edges, setEdges] = useState<Edge[]>(sampleEdges);

  const handleSave = async () => {
    // Simulate save
    await new Promise((resolve) => setTimeout(resolve, 1000));
    console.log('Workflow saved:', { nodes, edges });
  };

  const loadLargeWorkflow = () => {
    // Generate 100 nodes for performance testing
    const largeNodes: Node[] = Array.from({ length: 100 }, (_, i) => ({
      id: `node-${i}`,
      type: i % 3 === 0 ? 'control' : 'agent',
      position: {
        x: (i % 10) * 250 + 100,
        y: Math.floor(i / 10) * 200 + 100,
      },
      data: {
        label: `Node ${i + 1}`,
        description: `Sample node ${i + 1} for testing`,
        status: 'idle',
        tags: ['test', i % 2 === 0 ? 'even' : 'odd'],
        ...(i % 3 === 0 && {
          controlType: 'conditional',
          condition: 'value > 0',
        }),
      },
    }));

    const largeEdges: Edge[] = Array.from({ length: 99 }, (_, i) => ({
      id: `e${i}-${i + 1}`,
      source: `node-${i}`,
      target: `node-${i + 1}`,
      type: 'animated',
    }));

    setNodes(largeNodes);
    setEdges(largeEdges);
  };

  const resetWorkflow = () => {
    setNodes(sampleNodes);
    setEdges(sampleEdges);
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="border-b bg-background p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              Workflow Phase 2 Demo
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Advanced search, inline editing, keyboard shortcuts, and performance optimization
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadLargeWorkflow}>
              <FileText className="h-4 w-4 mr-2" />
              Load 100 Nodes
            </Button>
            <Button variant="outline" onClick={resetWorkflow}>
              Reset
            </Button>
          </div>
        </div>
      </div>

      {/* Info Cards */}
      <div className="p-4 bg-muted/30 border-b">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Inline Editing</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Double-click any node to edit
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Search & Filter</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Use search bar and filters
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Keyboard Shortcuts</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Press <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">?</kbd> for help
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Performance</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Handles 1000+ nodes smoothly
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1">
        <Phase2WorkflowCanvas
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
