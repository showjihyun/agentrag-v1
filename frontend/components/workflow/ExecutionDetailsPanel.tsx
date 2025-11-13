'use client';

import React, { useState } from 'react';
import { X, Clock, CheckCircle2, XCircle, AlertCircle, ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
// Collapsible components (inline implementation)
const Collapsible = ({ open, onOpenChange, children }: any) => (
  <div>{children}</div>
);
const CollapsibleTrigger = ({ children, className, ...props }: any) => (
  <button className={className} {...props}>{children}</button>
);
const CollapsibleContent = ({ children }: any) => children;

interface NodeExecution {
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

interface ExecutionDetailsPanelProps {
  executionId?: string;
  workflowName?: string;
  status: 'running' | 'completed' | 'failed' | 'idle';
  startTime?: string;
  endTime?: string;
  totalDuration?: number;
  nodeExecutions: NodeExecution[];
  onClose: () => void;
}

export function ExecutionDetailsPanel({
  executionId,
  workflowName,
  status,
  startTime,
  endTime,
  totalDuration,
  nodeExecutions,
  onClose,
}: ExecutionDetailsPanelProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const toggleNode = (nodeId: string) => {
    setExpandedNodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const expandAll = () => {
    setExpandedNodes(new Set(nodeExecutions.map((n) => n.nodeId)));
  };

  const collapseAll = () => {
    setExpandedNodes(new Set());
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, any> = {
      success: 'default',
      error: 'destructive',
      running: 'secondary',
      pending: 'outline',
    };

    return (
      <Badge variant={variants[status] || 'outline'} className="text-xs">
        {status}
      </Badge>
    );
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return 'N/A';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatTime = (time?: string) => {
    if (!time) return 'N/A';
    return new Date(time).toLocaleTimeString();
  };

  return (
    <div className="w-96 border-l bg-background flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-2">
          <h3 className="font-semibold text-lg">Execution Details</h3>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        {workflowName && (
          <p className="text-sm text-muted-foreground mb-2">{workflowName}</p>
        )}

        <div className="flex items-center gap-2 mb-3">
          {getStatusIcon(status)}
          {getStatusBadge(status)}
          {totalDuration !== undefined && (
            <span className="text-xs text-muted-foreground">
              {formatDuration(totalDuration)}
            </span>
          )}
        </div>

        {executionId && (
          <div className="text-xs text-muted-foreground">
            ID: {executionId.substring(0, 8)}...
          </div>
        )}

        {startTime && (
          <div className="text-xs text-muted-foreground mt-1">
            Started: {formatTime(startTime)}
          </div>
        )}

        {endTime && (
          <div className="text-xs text-muted-foreground">
            Ended: {formatTime(endTime)}
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="p-2 border-b flex gap-2">
        <Button variant="outline" size="sm" onClick={expandAll} className="flex-1">
          Expand All
        </Button>
        <Button variant="outline" size="sm" onClick={collapseAll} className="flex-1">
          Collapse All
        </Button>
      </div>

      {/* Node Executions */}
      <ScrollArea className="flex-1">
        <div className="p-3 space-y-2">
          {nodeExecutions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No execution data available</p>
            </div>
          ) : (
            nodeExecutions.map((node) => (
              <NodeExecutionItem
                key={node.nodeId}
                node={node}
                isExpanded={expandedNodes.has(node.nodeId)}
                onToggle={() => toggleNode(node.nodeId)}
                getStatusIcon={getStatusIcon}
                getStatusBadge={getStatusBadge}
                formatDuration={formatDuration}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface NodeExecutionItemProps {
  node: NodeExecution;
  isExpanded: boolean;
  onToggle: () => void;
  getStatusIcon: (status: string) => React.ReactNode;
  getStatusBadge: (status: string) => React.ReactNode;
  formatDuration: (ms?: number) => string;
}

function NodeExecutionItem({
  node,
  isExpanded,
  onToggle,
  getStatusIcon,
  getStatusBadge,
  formatDuration,
}: NodeExecutionItemProps) {
  const [copiedInput, setCopiedInput] = useState(false);
  const [copiedOutput, setCopiedOutput] = useState(false);

  const copyToClipboard = (data: any, type: 'input' | 'output') => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    if (type === 'input') {
      setCopiedInput(true);
      setTimeout(() => setCopiedInput(false), 2000);
    } else {
      setCopiedOutput(true);
      setTimeout(() => setCopiedOutput(false), 2000);
    }
  };

  return (
    <Collapsible open={isExpanded} onOpenChange={onToggle}>
      <div className="border rounded-lg overflow-hidden">
        <CollapsibleTrigger className="w-full p-3 hover:bg-accent transition-colors">
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
            {getStatusIcon(node.status)}
            <div className="flex-1 text-left">
              <div className="font-medium text-sm">{node.nodeName || node.nodeId}</div>
              <div className="text-xs text-muted-foreground">{node.nodeType}</div>
            </div>
            <div className="flex items-center gap-2">
              {node.retryCount !== undefined && node.retryCount > 0 && (
                <Badge variant="outline" className="text-xs">
                  {node.retryCount} retries
                </Badge>
              )}
              {node.duration !== undefined && (
                <span className="text-xs text-muted-foreground">
                  {formatDuration(node.duration)}
                </span>
              )}
            </div>
          </div>
        </CollapsibleTrigger>

        <CollapsibleContent>
          <Separator />
          <div className="p-3 space-y-3 bg-muted/30">
            {/* Status */}
            <div>
              <div className="text-xs font-medium mb-1">Status</div>
              {getStatusBadge(node.status)}
            </div>

            {/* Timing */}
            {node.duration !== undefined && (
              <div>
                <div className="text-xs font-medium mb-1">Duration</div>
                <div className="text-sm">{formatDuration(node.duration)}</div>
              </div>
            )}

            {/* Retry Count */}
            {node.retryCount !== undefined && node.retryCount > 0 && (
              <div>
                <div className="text-xs font-medium mb-1">Retry Attempts</div>
                <div className="text-sm">{node.retryCount}</div>
              </div>
            )}

            {/* Input */}
            {node.input !== undefined && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-medium">Input</div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2"
                    onClick={() => copyToClipboard(node.input, 'input')}
                  >
                    {copiedInput ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>
                <pre className="text-xs bg-background p-2 rounded border overflow-x-auto max-h-32">
                  {JSON.stringify(node.input, null, 2)}
                </pre>
              </div>
            )}

            {/* Output */}
            {node.output !== undefined && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <div className="text-xs font-medium">Output</div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2"
                    onClick={() => copyToClipboard(node.output, 'output')}
                  >
                    {copiedOutput ? (
                      <Check className="h-3 w-3" />
                    ) : (
                      <Copy className="h-3 w-3" />
                    )}
                  </Button>
                </div>
                <pre className="text-xs bg-background p-2 rounded border overflow-x-auto max-h-32">
                  {JSON.stringify(node.output, null, 2)}
                </pre>
              </div>
            )}

            {/* Error */}
            {node.error && (
              <div>
                <div className="text-xs font-medium mb-1 text-red-500">Error</div>
                <div className="text-xs bg-red-50 dark:bg-red-950 p-2 rounded border border-red-200 dark:border-red-800">
                  {node.error}
                </div>
              </div>
            )}
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  );
}
