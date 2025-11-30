'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Loader2,
  Zap,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

// Types
interface NodeExecutionState {
  nodeId: string;
  nodeName: string;
  nodeType: string;
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped' | 'timeout';
  startedAt?: string;
  completedAt?: string;
  duration?: number;
  result?: any;
  error?: string;
  retryCount?: number;
}

interface ExecutionState {
  executionId: string;
  workflowId: string;
  status: 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'timeout';
  progress: number;
  currentNodeId?: string;
  nodeStates: Record<string, NodeExecutionState>;
  startedAt?: string;
  completedAt?: string;
  totalDuration?: number;
  error?: string;
}

interface ExecutionVisualizerProps {
  executionId: string;
  workflowId: string;
  nodes: Array<{ id: string; type: string; data: { label?: string } }>;
  onNodeClick?: (nodeId: string) => void;
  onPause?: () => void;
  onResume?: () => void;
  onCancel?: () => void;
  onRetry?: () => void;
}

// Status badge component
const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const config: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
    pending: { color: 'bg-gray-100 text-gray-600', icon: <Clock className="w-3 h-3" />, label: '대기중' },
    queued: { color: 'bg-blue-100 text-blue-600', icon: <Clock className="w-3 h-3" />, label: '큐 대기' },
    running: { color: 'bg-yellow-100 text-yellow-600', icon: <Loader2 className="w-3 h-3 animate-spin" />, label: '실행중' },
    paused: { color: 'bg-orange-100 text-orange-600', icon: <Pause className="w-3 h-3" />, label: '일시정지' },
    success: { color: 'bg-green-100 text-green-600', icon: <CheckCircle className="w-3 h-3" />, label: '성공' },
    completed: { color: 'bg-green-100 text-green-600', icon: <CheckCircle className="w-3 h-3" />, label: '완료' },
    error: { color: 'bg-red-100 text-red-600', icon: <XCircle className="w-3 h-3" />, label: '오류' },
    failed: { color: 'bg-red-100 text-red-600', icon: <XCircle className="w-3 h-3" />, label: '실패' },
    cancelled: { color: 'bg-gray-100 text-gray-600', icon: <Square className="w-3 h-3" />, label: '취소됨' },
    timeout: { color: 'bg-orange-100 text-orange-600', icon: <AlertTriangle className="w-3 h-3" />, label: '타임아웃' },
    skipped: { color: 'bg-gray-100 text-gray-500', icon: <ChevronRight className="w-3 h-3" />, label: '건너뜀' },
  };

  const { color, icon, label } = config[status] || config.pending;

  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', color)}>
      {icon}
      {label}
    </span>
  );
};

// Node execution row component
const NodeExecutionRow: React.FC<{
  state: NodeExecutionState;
  isActive: boolean;
  onClick?: () => void;
}> = ({ state, isActive, onClick }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div 
      className={cn(
        'border rounded-lg transition-all',
        isActive && 'ring-2 ring-blue-500 bg-blue-50',
        state.status === 'error' && 'border-red-200 bg-red-50',
        state.status === 'success' && 'border-green-200',
      )}
    >
      <div 
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50"
        onClick={() => {
          setExpanded(!expanded);
          onClick?.();
        }}
      >
        <div className="flex items-center gap-3">
          <button className="text-gray-400 hover:text-gray-600">
            {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>
          
          <div>
            <div className="font-medium text-sm">{state.nodeName || state.nodeId}</div>
            <div className="text-xs text-gray-500">{state.nodeType}</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {state.duration !== undefined && (
            <span className="text-xs text-gray-500">
              {state.duration < 1000 
                ? `${state.duration}ms` 
                : `${(state.duration / 1000).toFixed(2)}s`}
            </span>
          )}
          <StatusBadge status={state.status} />
        </div>
      </div>

      {expanded && (
        <div className="border-t px-3 py-2 bg-gray-50 text-sm">
          {state.error && (
            <div className="mb-2 p-2 bg-red-100 text-red-700 rounded text-xs">
              <strong>오류:</strong> {state.error}
            </div>
          )}
          
          {state.result && (
            <div className="mb-2">
              <div className="text-xs font-medium text-gray-500 mb-1">결과:</div>
              <pre className="p-2 bg-white rounded border text-xs overflow-auto max-h-40">
                {JSON.stringify(state.result, null, 2)}
              </pre>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
            {state.startedAt && (
              <div>시작: {new Date(state.startedAt).toLocaleTimeString()}</div>
            )}
            {state.completedAt && (
              <div>완료: {new Date(state.completedAt).toLocaleTimeString()}</div>
            )}
            {state.retryCount !== undefined && state.retryCount > 0 && (
              <div>재시도: {state.retryCount}회</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Progress bar component
const ExecutionProgress: React.FC<{ progress: number; status: string }> = ({ progress, status }) => {
  const getColor = () => {
    switch (status) {
      case 'running': return 'bg-blue-500';
      case 'completed': case 'success': return 'bg-green-500';
      case 'failed': case 'error': return 'bg-red-500';
      case 'paused': return 'bg-orange-500';
      default: return 'bg-gray-300';
    }
  };

  return (
    <div className="w-full bg-gray-200 rounded-full h-2">
      <div 
        className={cn('h-2 rounded-full transition-all duration-300', getColor())}
        style={{ width: `${progress}%` }}
      />
    </div>
  );
};

// Main component
export const ExecutionVisualizer: React.FC<ExecutionVisualizerProps> = ({
  executionId,
  workflowId,
  nodes,
  onNodeClick,
  onPause,
  onResume,
  onCancel,
  onRetry,
}) => {
  const [executionState, setExecutionState] = useState<ExecutionState>({
    executionId,
    workflowId,
    status: 'pending',
    progress: 0,
    nodeStates: {},
  });

  const [isConnected, setIsConnected] = useState(false);

  // SSE connection for real-time updates
  useEffect(() => {
    if (!executionId) return;

    const eventSource = new EventSource(
      `/api/agent-builder/workflows/executions/${executionId}/stream`
    );

    eventSource.onopen = () => {
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'state_update') {
          setExecutionState(prev => ({
            ...prev,
            ...data.state,
          }));
        } else if (data.type === 'node_update') {
          setExecutionState(prev => ({
            ...prev,
            nodeStates: {
              ...prev.nodeStates,
              [data.nodeId]: data.nodeState,
            },
            currentNodeId: data.nodeState.status === 'running' ? data.nodeId : prev.currentNodeId,
          }));
        }
      } catch (e) {
        console.error('Failed to parse SSE message:', e);
      }
    };

    eventSource.onerror = () => {
      setIsConnected(false);
    };

    return () => {
      eventSource.close();
    };
  }, [executionId]);

  // Calculate progress
  const calculateProgress = useCallback(() => {
    const totalNodes = nodes.length;
    if (totalNodes === 0) return 0;

    const completedNodes = Object.values(executionState.nodeStates).filter(
      n => n.status === 'success' || n.status === 'skipped'
    ).length;

    return Math.round((completedNodes / totalNodes) * 100);
  }, [nodes, executionState.nodeStates]);

  useEffect(() => {
    setExecutionState(prev => ({
      ...prev,
      progress: calculateProgress(),
    }));
  }, [calculateProgress]);

  const isRunning = executionState.status === 'running';
  const isPaused = executionState.status === 'paused';
  const isCompleted = ['completed', 'failed', 'cancelled', 'timeout'].includes(executionState.status);

  return (
    <div className="bg-white rounded-lg border shadow-sm">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-500" />
            <h3 className="font-semibold">실행 상태</h3>
            {isConnected && (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                실시간
              </span>
            )}
          </div>
          <StatusBadge status={executionState.status} />
        </div>

        {/* Progress */}
        <div className="mb-3">
          <div className="flex justify-between text-sm text-gray-500 mb-1">
            <span>진행률</span>
            <span>{executionState.progress}%</span>
          </div>
          <ExecutionProgress progress={executionState.progress} status={executionState.status} />
        </div>

        {/* Controls */}
        <div className="flex gap-2">
          {isRunning && onPause && (
            <Button size="sm" variant="outline" onClick={onPause}>
              <Pause className="w-4 h-4 mr-1" />
              일시정지
            </Button>
          )}
          {isPaused && onResume && (
            <Button size="sm" variant="outline" onClick={onResume}>
              <Play className="w-4 h-4 mr-1" />
              재개
            </Button>
          )}
          {(isRunning || isPaused) && onCancel && (
            <Button size="sm" variant="outline" onClick={onCancel}>
              <Square className="w-4 h-4 mr-1" />
              취소
            </Button>
          )}
          {isCompleted && executionState.status === 'failed' && onRetry && (
            <Button size="sm" variant="outline" onClick={onRetry}>
              <RotateCcw className="w-4 h-4 mr-1" />
              재시도
            </Button>
          )}
        </div>
      </div>

      {/* Execution Info */}
      <div className="p-4 border-b bg-gray-50 text-sm">
        <div className="grid grid-cols-2 gap-2 text-gray-600">
          <div>
            <span className="text-gray-400">실행 ID:</span>{' '}
            <span className="font-mono text-xs">{executionId.slice(0, 8)}...</span>
          </div>
          {executionState.startedAt && (
            <div>
              <span className="text-gray-400">시작:</span>{' '}
              {new Date(executionState.startedAt).toLocaleString()}
            </div>
          )}
          {executionState.totalDuration !== undefined && (
            <div>
              <span className="text-gray-400">총 소요시간:</span>{' '}
              {executionState.totalDuration < 1000 
                ? `${executionState.totalDuration}ms`
                : `${(executionState.totalDuration / 1000).toFixed(2)}s`}
            </div>
          )}
        </div>
      </div>

      {/* Node List */}
      <div className="p-4 space-y-2 max-h-96 overflow-y-auto">
        {nodes.map(node => {
          const nodeState = executionState.nodeStates[node.id] || {
            nodeId: node.id,
            nodeName: node.data.label || node.id,
            nodeType: node.type,
            status: 'pending' as const,
          };

          return (
            <NodeExecutionRow
              key={node.id}
              state={nodeState}
              isActive={executionState.currentNodeId === node.id}
              onClick={() => onNodeClick?.(node.id)}
            />
          );
        })}
      </div>

      {/* Error Display */}
      {executionState.error && (
        <div className="p-4 border-t bg-red-50">
          <div className="flex items-start gap-2 text-red-700">
            <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-medium">실행 오류</div>
              <div className="text-sm mt-1">{executionState.error}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionVisualizer;
