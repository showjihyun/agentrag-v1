'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react';

interface ExecutionLog {
  timestamp: number;
  nodeId: string;
  nodeName: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'waiting';
  message: string;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
  config?: any;
}

interface ExecutionLogPanelProps {
  nodeStatuses: Record<string, any>;
  isExecuting: boolean;
  startTime?: number;
  endTime?: number;
}

export function ExecutionLogPanel({ nodeStatuses, isExecuting, startTime, endTime }: ExecutionLogPanelProps) {
  // Generate logs from node statuses
  const logs: ExecutionLog[] = Object.values(nodeStatuses)
    .sort((a, b) => (a.timestamp || 0) - (b.timestamp || 0))
    .map((status) => ({
      timestamp: status.timestamp || Date.now(),
      nodeId: status.nodeId,
      nodeName: status.nodeName || 'Unknown Node',
      status: status.status,
      message: getStatusMessage(status.status, status.nodeName),
      duration: status.endTime && status.startTime ? status.endTime - status.startTime : undefined,
      input: status.input,
      output: status.output,
      error: status.error,
      config: status.config,
    }));

  // Calculate total duration: if completed, use endTime; otherwise use current time
  const totalDuration = startTime 
    ? (endTime || Date.now()) - startTime 
    : 0;
  const completedNodes = logs.filter(l => l.status === 'success').length;
  const failedNodes = logs.filter(l => l.status === 'failed').length;
  const totalNodes = logs.length;

  return (
    <Card className="h-full flex flex-col border-t-4 border-t-blue-500">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {isExecuting ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                <span>Execution in Progress</span>
              </>
            ) : (
              <>
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span>Execution Complete</span>
              </>
            )}
          </CardTitle>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{formatDuration(totalDuration)}</span>
          </div>
        </div>
        
        {/* Progress Summary */}
        <div className="flex items-center gap-4 mt-2 text-sm">
          <div className="flex items-center gap-1">
            <span className="text-muted-foreground">Progress:</span>
            <span className="font-semibold">{completedNodes}/{totalNodes}</span>
          </div>
          {failedNodes > 0 && (
            <Badge variant="destructive" className="text-xs">
              {failedNodes} Failed
            </Badge>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="flex-1 overflow-hidden p-0">
        <ScrollArea className="h-full px-6 pb-4">
          <div className="space-y-2">
            {logs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No execution logs yet</p>
                <p className="text-xs mt-1">Logs will appear here when execution starts</p>
              </div>
            ) : (
              logs.map((log, index) => (
                <LogEntry key={`${log.nodeId}-${index}`} log={log} />
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

function LogEntry({ log }: { log: ExecutionLog }) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  
  const getStatusIcon = () => {
    switch (log.status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'waiting':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (log.status) {
      case 'running':
        return 'border-l-blue-500 bg-blue-50/50';
      case 'success':
        return 'border-l-green-500 bg-green-50/50';
      case 'failed':
        return 'border-l-red-500 bg-red-50/50';
      case 'waiting':
        return 'border-l-yellow-500 bg-yellow-50/50';
      default:
        return 'border-l-gray-300 bg-gray-50/50';
    }
  };

  const hasDetails = log.input || log.output || log.error || log.config;

  return (
    <div className={`rounded-lg border-l-4 ${getStatusColor()} transition-all`}>
      <div 
        className={`flex items-start gap-3 p-3 ${hasDetails ? 'cursor-pointer hover:bg-black/5' : ''}`}
        onClick={() => hasDetails && setIsExpanded(!isExpanded)}
      >
        <div className="mt-0.5">{getStatusIcon()}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="font-medium text-sm truncate">{log.nodeName}</span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {new Date(log.timestamp).toLocaleTimeString()}
              </span>
              {hasDetails && (
                <button className="text-xs text-blue-600 hover:text-blue-800">
                  {isExpanded ? '▼' : '▶'}
                </button>
              )}
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{log.message}</p>
          {log.duration !== undefined && (
            <p className="text-xs text-muted-foreground mt-1">
              Duration: {formatDuration(log.duration)}
            </p>
          )}
          
          {/* Error message (always visible if present) */}
          {log.error && (
            <div className="mt-2 p-2 bg-red-100 border border-red-200 rounded text-xs text-red-800">
              <strong>Error:</strong> {log.error}
            </div>
          )}
        </div>
      </div>
      
      {/* Expanded details */}
      {isExpanded && hasDetails && (
        <div className="px-3 pb-3 space-y-3 border-t border-gray-200 pt-3 mt-2 bg-gray-50/50">
          {log.config && Object.keys(log.config).length > 0 && (
            <div>
              <div className="text-xs font-semibold text-gray-800 mb-1.5 flex items-center gap-1">
                <span className="text-blue-600">⚙️</span> Configuration:
              </div>
              <pre className="text-xs bg-slate-800 text-slate-100 p-3 rounded-md overflow-x-auto max-h-40 border border-slate-700 font-mono">
                {JSON.stringify(log.config, null, 2)}
              </pre>
            </div>
          )}
          
          {log.input && (
            <div>
              <div className="text-xs font-semibold text-gray-800 mb-1.5 flex items-center gap-1">
                <span className="text-green-600">📥</span> Input:
              </div>
              <pre className="text-xs bg-slate-800 text-green-100 p-3 rounded-md overflow-x-auto max-h-40 border border-slate-700 font-mono">
                {typeof log.input === 'string' ? log.input : JSON.stringify(log.input, null, 2)}
              </pre>
            </div>
          )}
          
          {log.output && (
            <div>
              <div className="text-xs font-semibold text-gray-800 mb-1.5 flex items-center gap-1">
                <span className="text-purple-600">📤</span> Output:
              </div>
              <pre className="text-xs bg-slate-800 text-purple-100 p-3 rounded-md overflow-x-auto max-h-40 border border-slate-700 font-mono">
                {typeof log.output === 'string' ? log.output : JSON.stringify(log.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function getStatusMessage(status: string, nodeName: string): string {
  switch (status) {
    case 'pending':
      return 'Waiting to execute...';
    case 'running':
      return 'Executing node...';
    case 'success':
      return 'Completed successfully';
    case 'failed':
      return 'Execution failed';
    case 'waiting':
      return 'Waiting for dependencies...';
    default:
      return 'Unknown status';
  }
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  return `${minutes}m ${seconds}s`;
}
