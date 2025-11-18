'use client';

import { useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  AlertCircle,
  ChevronRight
} from 'lucide-react';

interface Node {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    type: string;
    config: any;
  };
}

interface NodeExecution {
  nodeId: string;
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped';
  duration?: number;
}

interface VisualWorkflowCanvasProps {
  nodes: Node[];
  edges: any[];
  nodeExecutions: NodeExecution[];
  isExecuting: boolean;
}

export function VisualWorkflowCanvas({
  nodes,
  edges,
  nodeExecutions,
  isExecuting
}: VisualWorkflowCanvasProps) {
  
  const getNodeStatus = (nodeId: string) => {
    const execution = nodeExecutions.find(e => e.nodeId === nodeId);
    return execution?.status || 'pending';
  };

  const getNodeDuration = (nodeId: string) => {
    const execution = nodeExecutions.find(e => e.nodeId === nodeId);
    return execution?.duration;
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'skipped':
        return <AlertCircle className="h-5 w-5 text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950 shadow-lg shadow-blue-500/50';
      case 'success':
        return 'border-green-500 bg-green-50 dark:bg-green-950';
      case 'error':
        return 'border-red-500 bg-red-50 dark:bg-red-950';
      case 'skipped':
        return 'border-gray-300 bg-gray-50 dark:bg-gray-900';
      default:
        return 'border-gray-300 bg-white dark:bg-gray-950';
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  if (nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <div className="text-6xl mb-4">🎨</div>
          <h3 className="text-xl font-semibold mb-2">Workflow Canvas</h3>
          <p className="text-sm mb-4">
            Add blocks from the palette to start building your workflow
          </p>
          <div className="flex items-center justify-center gap-2 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span>Running</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-green-500"></div>
              <span>Success</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span>Error</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-8">
      <div className="max-w-4xl mx-auto">
        {/* Workflow Title */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold mb-2">Workflow Execution</h2>
          <p className="text-sm text-muted-foreground">
            {nodes.length} node{nodes.length > 1 ? 's' : ''} in workflow
            {isExecuting && (
              <Badge variant="secondary" className="ml-2">
                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                Executing...
              </Badge>
            )}
          </p>
        </div>

        {/* Nodes Flow */}
        <div className="space-y-4">
          {nodes.map((node, index) => {
            const status = getNodeStatus(node.id);
            const duration = getNodeDuration(node.id);
            const isActive = status === 'running';

            return (
              <div key={node.id} className="relative">
                {/* Node Card */}
                <Card
                  className={`
                    p-4 transition-all duration-300
                    ${getStatusColor(status)}
                    ${isActive ? 'scale-105 ring-2 ring-blue-500' : ''}
                  `}
                >
                  <div className="flex items-center gap-4">
                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                      {getStatusIcon(status)}
                    </div>

                    {/* Node Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg truncate">
                          {node.data.label}
                        </h3>
                        <Badge variant="outline" className="text-xs">
                          {node.type}
                        </Badge>
                      </div>
                      
                      {/* Node Details */}
                      <div className="flex items-center gap-3 text-sm text-muted-foreground">
                        <span>Step {index + 1}</span>
                        {duration && (
                          <>
                            <span>•</span>
                            <span className="font-medium">{formatDuration(duration)}</span>
                          </>
                        )}
                        {status === 'running' && (
                          <>
                            <span>•</span>
                            <span className="text-blue-600 dark:text-blue-400 font-medium">
                              Processing...
                            </span>
                          </>
                        )}
                      </div>

                      {/* Config Preview */}
                      {node.data.config && Object.keys(node.data.config).length > 0 && (
                        <div className="mt-2 text-xs text-muted-foreground">
                          {node.data.config.toolId && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                              Tool: {node.data.config.toolId}
                            </span>
                          )}
                          {node.data.config.blockType && (
                            <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded">
                              Type: {node.data.config.blockType}
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Status Badge */}
                    <div className="flex-shrink-0">
                      <Badge
                        variant={
                          status === 'success' ? 'default' :
                          status === 'error' ? 'destructive' :
                          status === 'running' ? 'secondary' :
                          'outline'
                        }
                        className="capitalize"
                      >
                        {status}
                      </Badge>
                    </div>
                  </div>

                  {/* Progress Bar for Running */}
                  {isActive && (
                    <div className="mt-3 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 animate-pulse" style={{ width: '60%' }}></div>
                    </div>
                  )}
                </Card>

                {/* Connector Arrow */}
                {index < nodes.length - 1 && (
                  <div className="flex justify-center py-2">
                    <ChevronRight className="h-6 w-6 text-gray-400 rotate-90" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Execution Summary */}
        {nodeExecutions.length > 0 && (
          <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border">
            <h4 className="font-semibold mb-3">Execution Summary</h4>
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                  {nodeExecutions.length}
                </div>
                <div className="text-xs text-muted-foreground">Total</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {nodeExecutions.filter(n => n.status === 'success').length}
                </div>
                <div className="text-xs text-muted-foreground">Success</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-red-600">
                  {nodeExecutions.filter(n => n.status === 'error').length}
                </div>
                <div className="text-xs text-muted-foreground">Failed</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {nodeExecutions.filter(n => n.status === 'running').length}
                </div>
                <div className="text-xs text-muted-foreground">Running</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
