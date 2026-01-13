'use client';

import React from 'react';
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useTheme } from '@/contexts/ThemeContext';

interface ExecutionStep {
  id: string;
  name: string;
  type: 'agent' | 'tool' | 'llm' | 'condition' | 'loop';
  status: 'pending' | 'running' | 'completed' | 'failed';
  duration?: number;
  children?: string[];
}

interface ExecutionFlowDiagramProps {
  steps: ExecutionStep[];
  currentStepId?: string;
}

export function ExecutionFlowDiagram({
  steps,
  currentStepId,
}: ExecutionFlowDiagramProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Convert steps to nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = React.useMemo(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];
    const levelMap = new Map<string, number>();

    // Calculate levels (BFS)
    const queue: Array<{ id: string; level: number }> = [];
    const rootSteps = steps.filter(
      (s) => !steps.some((parent) => parent.children?.includes(s.id))
    );

    rootSteps.forEach((step) => {
      queue.push({ id: step.id, level: 0 });
    });

    while (queue.length > 0) {
      const { id, level } = queue.shift()!;
      levelMap.set(id, level);

      const step = steps.find((s) => s.id === id);
      step?.children?.forEach((childId) => {
        queue.push({ id: childId, level: level + 1 });
      });
    }

    // Create nodes
    const levelCounts = new Map<number, number>();
    steps.forEach((step) => {
      const level = levelMap.get(step.id) || 0;
      const countAtLevel = levelCounts.get(level) || 0;
      levelCounts.set(level, countAtLevel + 1);

      const x = countAtLevel * 250;
      const y = level * 150;

      nodes.push({
        id: step.id,
        type: 'default',
        position: { x, y },
        data: {
          label: (
            <div className="px-4 py-2">
              <div className="font-semibold text-sm">{step.name}</div>
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  variant={
                    step.status === 'completed'
                      ? 'default'
                      : step.status === 'failed'
                      ? 'destructive'
                      : 'secondary'
                  }
                  className="text-xs"
                >
                  {step.status}
                </Badge>
                {step.duration && (
                  <span className="text-xs text-muted-foreground">
                    {step.duration}ms
                  </span>
                )}
              </div>
            </div>
          ),
        },
        style: {
          background: isDark ? '#1f2937' : '#ffffff',
          border: `2px solid ${
            step.id === currentStepId
              ? '#3b82f6'
              : step.status === 'completed'
              ? '#10b981'
              : step.status === 'failed'
              ? '#ef4444'
              : step.status === 'running'
              ? '#f59e0b'
              : '#6b7280'
          }`,
          borderRadius: '8px',
          padding: 0,
        },
      });
    });

    // Create edges
    steps.forEach((step) => {
      step.children?.forEach((childId) => {
        edges.push({
          id: `${step.id}-${childId}`,
          source: step.id,
          target: childId,
          animated: step.status === 'running',
          style: {
            stroke: isDark ? '#6b7280' : '#9ca3af',
            strokeWidth: 2,
          },
        });
      });
    });

    return { nodes, edges };
  }, [steps, currentStepId, isDark]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Execution Flow</CardTitle>
        <CardDescription>
          Visual representation of execution steps
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[600px] w-full border rounded-lg overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
            attributionPosition="bottom-left"
          >
            <Background color={isDark ? '#374151' : '#e5e7eb'} />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const step = steps.find((s) => s.id === node.id);
                if (!step) return '#6b7280';
                
                switch (step.status) {
                  case 'completed':
                    return '#10b981';
                  case 'failed':
                    return '#ef4444';
                  case 'running':
                    return '#f59e0b';
                  default:
                    return '#6b7280';
                }
              }}
              maskColor={isDark ? 'rgba(0, 0, 0, 0.6)' : 'rgba(255, 255, 255, 0.6)'}
            />
          </ReactFlow>
        </div>
      </CardContent>
    </Card>
  );
}
