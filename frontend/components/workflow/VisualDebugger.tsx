'use client';

/**
 * Visual Debugger Component
 * 
 * World-class debugging experience for workflows:
 * - Real-time execution visualization
 * - Breakpoint management
 * - Step-by-step execution
 * - Variable inspector
 * - Time-travel debugging
 */

import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  Play,
  Pause,
  Square,
  SkipForward,
  StepInto,
  StepOut,
  RotateCcw,
  Circle,
  CircleDot,
  Bug,
  Eye,
  EyeOff,
  ChevronRight,
  ChevronDown,
  Clock,
  Zap,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  History,
  Variable,
  Layers,
  Terminal,
  Sparkles,
} from 'lucide-react';

// Types
export interface DebugNode {
  id: string;
  name: string;
  type: string;
  status: 'pending' | 'running' | 'success' | 'error' | 'skipped' | 'paused';
  hasBreakpoint: boolean;
  input?: Record<string, unknown>;
  output?: Record<string, unknown>;
  error?: string;
  duration?: number;
  startTime?: number;
  endTime?: number;
}

export interface DebugState {
  executionId: string;
  status: 'idle' | 'running' | 'paused' | 'completed' | 'error';
  currentNodeId: string | null;
  nodes: DebugNode[];
  variables: Record<string, unknown>;
  callStack: string[];
  history: DebugSnapshot[];
}

export interface DebugSnapshot {
  id: string;
  timestamp: number;
  nodeId: string;
  nodeName: string;
  variables: Record<string, unknown>;
  description: string;
}

export interface WatchExpression {
  id: string;
  expression: string;
  value: unknown;
  error?: string;
}

interface VisualDebuggerProps {
  workflowId: string;
  debugState: DebugState;
  onToggleBreakpoint: (nodeId: string) => void;
  onStepOver: () => void;
  onStepInto: () => void;
  onStepOut: () => void;
  onContinue: () => void;
  onPause: () => void;
  onStop: () => void;
  onRestart: () => void;
  onTimeTravel: (snapshotId: string) => void;
  onAddWatch: (expression: string) => void;
  onRemoveWatch: (id: string) => void;
  watchExpressions: WatchExpression[];
  className?: string;
}

// Variable Inspector Component
const VariableInspector: React.FC<{
  data: unknown;
  name?: string;
  depth?: number;
  expanded?: boolean;
}> = ({ data, name, depth = 0, expanded: initialExpanded = depth < 2 }) => {
  const [expanded, setExpanded] = useState(initialExpanded);
  
  const isExpandable = typeof data === 'object' && data !== null;
  const type = Array.isArray(data) ? 'array' : typeof data;
  
  const getPreview = (value: unknown): string => {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'string') return `"${value.slice(0, 50)}${value.length > 50 ? '...' : ''}"`;
    if (typeof value === 'number' || typeof value === 'boolean') return String(value);
    if (Array.isArray(value)) return `Array(${value.length})`;
    if (typeof value === 'object') return `{${Object.keys(value).length} keys}`;
    return String(value);
  };

  const getTypeColor = (t: string): string => {
    switch (t) {
      case 'string': return 'text-green-600';
      case 'number': return 'text-blue-600';
      case 'boolean': return 'text-purple-600';
      case 'array': return 'text-orange-600';
      case 'object': return 'text-cyan-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="font-mono text-xs">
      <div 
        className={cn(
          'flex items-center gap-1 py-0.5 hover:bg-muted/50 rounded cursor-pointer',
          depth > 0 && 'ml-4'
        )}
        onClick={() => isExpandable && setExpanded(!expanded)}
      >
        {isExpandable ? (
          expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />
        ) : (
          <span className="w-3" />
        )}
        {name && <span className="text-purple-600">{name}:</span>}
        <span className={getTypeColor(type)}>{getPreview(data)}</span>
      </div>
      
      {expanded && isExpandable && (
        <div className="border-l border-muted ml-1.5">
          {Object.entries(data as Record<string, unknown>).map(([key, value]) => (
            <VariableInspector 
              key={key} 
              name={key} 
              data={value} 
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Node Status Badge
const NodeStatusBadge: React.FC<{ status: DebugNode['status'] }> = ({ status }) => {
  const config = {
    pending: { icon: Circle, color: 'bg-gray-100 text-gray-600', label: '대기' },
    running: { icon: Loader2, color: 'bg-blue-100 text-blue-600', label: '실행중', animate: true },
    success: { icon: CheckCircle2, color: 'bg-green-100 text-green-600', label: '성공' },
    error: { icon: XCircle, color: 'bg-red-100 text-red-600', label: '오류' },
    skipped: { icon: SkipForward, color: 'bg-gray-100 text-gray-500', label: '건너뜀' },
    paused: { icon: Pause, color: 'bg-yellow-100 text-yellow-600', label: '일시정지' },
  };

  const { icon: Icon, color, label, animate } = config[status];

  return (
    <Badge variant="outline" className={cn('gap-1 text-xs', color)}>
      <Icon className={cn('w-3 h-3', animate && 'animate-spin')} />
      {label}
    </Badge>
  );
};

// Main Component
export function VisualDebugger({
  workflowId,
  debugState,
  onToggleBreakpoint,
  onStepOver,
  onStepInto,
  onStepOut,
  onContinue,
  onPause,
  onStop,
  onRestart,
  onTimeTravel,
  onAddWatch,
  onRemoveWatch,
  watchExpressions,
  className,
}: VisualDebuggerProps) {
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [newWatchExpr, setNewWatchExpr] = useState('');
  const [activeTab, setActiveTab] = useState('variables');

  // Auto-select current node
  useEffect(() => {
    if (debugState.currentNodeId) {
      setSelectedNodeId(debugState.currentNodeId);
    }
  }, [debugState.currentNodeId]);

  const selectedNode = useMemo(() => 
    debugState.nodes.find(n => n.id === selectedNodeId),
    [debugState.nodes, selectedNodeId]
  );

  const isRunning = debugState.status === 'running';
  const isPaused = debugState.status === 'paused';
  const canStep = isPaused;

  const handleAddWatch = useCallback(() => {
    if (newWatchExpr.trim()) {
      onAddWatch(newWatchExpr.trim());
      setNewWatchExpr('');
    }
  }, [newWatchExpr, onAddWatch]);

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className={cn('flex flex-col h-full bg-background border rounded-lg', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b bg-muted/30">
        <div className="flex items-center gap-2">
          <Bug className="w-5 h-5 text-orange-500" />
          <span className="font-semibold">Visual Debugger</span>
          <Badge variant={debugState.status === 'running' ? 'default' : 'secondary'}>
            {debugState.status === 'idle' && '대기'}
            {debugState.status === 'running' && '실행중'}
            {debugState.status === 'paused' && '일시정지'}
            {debugState.status === 'completed' && '완료'}
            {debugState.status === 'error' && '오류'}
          </Badge>
        </div>
        
        {/* Control Buttons */}
        <div className="flex items-center gap-1">
          <TooltipProvider>
            {isRunning ? (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={onPause}>
                    <Pause className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>일시정지 (F8)</TooltipContent>
              </Tooltip>
            ) : (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button size="sm" variant="outline" onClick={onContinue} disabled={!isPaused}>
                    <Play className="w-4 h-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>계속 (F5)</TooltipContent>
              </Tooltip>
            )}
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="sm" variant="outline" onClick={onStepOver} disabled={!canStep}>
                  <SkipForward className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Step Over (F10)</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="sm" variant="outline" onClick={onStepInto} disabled={!canStep}>
                  <StepInto className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Step Into (F11)</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="sm" variant="outline" onClick={onStepOut} disabled={!canStep}>
                  <StepOut className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Step Out (Shift+F11)</TooltipContent>
            </Tooltip>
            
            <div className="w-px h-6 bg-border mx-1" />
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="sm" variant="outline" onClick={onStop}>
                  <Square className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>중지 (Shift+F5)</TooltipContent>
            </Tooltip>
            
            <Tooltip>
              <TooltipTrigger asChild>
                <Button size="sm" variant="outline" onClick={onRestart}>
                  <RotateCcw className="w-4 h-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>재시작 (Ctrl+Shift+F5)</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Node List */}
        <div className="w-64 border-r flex flex-col">
          <div className="p-2 border-b bg-muted/20">
            <span className="text-xs font-medium text-muted-foreground">노드 목록</span>
          </div>
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {debugState.nodes.map((node) => (
                <div
                  key={node.id}
                  className={cn(
                    'flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors',
                    selectedNodeId === node.id ? 'bg-primary/10 border border-primary/30' : 'hover:bg-muted/50',
                    debugState.currentNodeId === node.id && 'ring-2 ring-blue-500'
                  )}
                  onClick={() => setSelectedNodeId(node.id)}
                >
                  {/* Breakpoint indicator */}
                  <button
                    className="flex-shrink-0"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleBreakpoint(node.id);
                    }}
                  >
                    {node.hasBreakpoint ? (
                      <CircleDot className="w-4 h-4 text-red-500" />
                    ) : (
                      <Circle className="w-4 h-4 text-gray-300 hover:text-red-300" />
                    )}
                  </button>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{node.name}</span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-xs text-muted-foreground">{node.type}</span>
                      {node.duration && (
                        <span className="text-xs text-muted-foreground flex items-center gap-0.5">
                          <Clock className="w-3 h-3" />
                          {formatDuration(node.duration)}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <NodeStatusBadge status={node.status} />
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Detail Panel */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
            <TabsList className="mx-2 mt-2">
              <TabsTrigger value="variables" className="gap-1">
                <Variable className="w-3 h-3" />
                변수
              </TabsTrigger>
              <TabsTrigger value="watch" className="gap-1">
                <Eye className="w-3 h-3" />
                Watch
              </TabsTrigger>
              <TabsTrigger value="callstack" className="gap-1">
                <Layers className="w-3 h-3" />
                Call Stack
              </TabsTrigger>
              <TabsTrigger value="history" className="gap-1">
                <History className="w-3 h-3" />
                History
              </TabsTrigger>
            </TabsList>

            <TabsContent value="variables" className="flex-1 overflow-hidden m-0 p-2">
              <ScrollArea className="h-full">
                {selectedNode ? (
                  <div className="space-y-4">
                    {/* Input */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold text-muted-foreground">INPUT</span>
                        {selectedNode.input && (
                          <Badge variant="outline" className="text-xs">
                            {Object.keys(selectedNode.input).length} keys
                          </Badge>
                        )}
                      </div>
                      {selectedNode.input ? (
                        <div className="bg-muted/30 rounded-md p-2">
                          <VariableInspector data={selectedNode.input} />
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">No input data</p>
                      )}
                    </div>

                    {/* Output */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold text-muted-foreground">OUTPUT</span>
                        {selectedNode.output && (
                          <Badge variant="outline" className="text-xs">
                            {Object.keys(selectedNode.output).length} keys
                          </Badge>
                        )}
                      </div>
                      {selectedNode.output ? (
                        <div className="bg-muted/30 rounded-md p-2">
                          <VariableInspector data={selectedNode.output} />
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">No output data</p>
                      )}
                    </div>

                    {/* Error */}
                    {selectedNode.error && (
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <AlertTriangle className="w-3 h-3 text-red-500" />
                          <span className="text-xs font-semibold text-red-500">ERROR</span>
                        </div>
                        <div className="bg-red-50 border border-red-200 rounded-md p-2">
                          <pre className="text-xs text-red-700 whitespace-pre-wrap">
                            {selectedNode.error}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* Global Variables */}
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold text-muted-foreground">GLOBAL VARIABLES</span>
                      </div>
                      <div className="bg-muted/30 rounded-md p-2">
                        <VariableInspector data={debugState.variables} />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
                    <p className="text-sm">노드를 선택하세요</p>
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="watch" className="flex-1 overflow-hidden m-0 p-2">
              <div className="space-y-2">
                {/* Add watch expression */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={newWatchExpr}
                    onChange={(e) => setNewWatchExpr(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAddWatch()}
                    placeholder="Watch expression (e.g., data.items.length)"
                    className="flex-1 px-2 py-1 text-sm border rounded-md"
                  />
                  <Button size="sm" onClick={handleAddWatch}>
                    추가
                  </Button>
                </div>

                {/* Watch list */}
                <ScrollArea className="h-[calc(100%-40px)]">
                  <div className="space-y-1">
                    {watchExpressions.map((watch) => (
                      <div
                        key={watch.id}
                        className="flex items-start gap-2 p-2 bg-muted/30 rounded-md"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="text-xs font-mono text-purple-600">{watch.expression}</div>
                          {watch.error ? (
                            <div className="text-xs text-red-500 mt-0.5">{watch.error}</div>
                          ) : (
                            <div className="mt-0.5">
                              <VariableInspector data={watch.value} />
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => onRemoveWatch(watch.id)}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <EyeOff className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                    {watchExpressions.length === 0 && (
                      <p className="text-xs text-muted-foreground text-center py-4">
                        Watch expression을 추가하세요
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </div>
            </TabsContent>

            <TabsContent value="callstack" className="flex-1 overflow-hidden m-0 p-2">
              <ScrollArea className="h-full">
                <div className="space-y-1">
                  {debugState.callStack.map((frame, index) => (
                    <div
                      key={index}
                      className={cn(
                        'flex items-center gap-2 p-2 rounded-md text-sm',
                        index === 0 ? 'bg-primary/10 font-medium' : 'hover:bg-muted/50'
                      )}
                    >
                      <Zap className="w-3 h-3 text-muted-foreground" />
                      <span className="font-mono">{frame}</span>
                    </div>
                  ))}
                  {debugState.callStack.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      Call stack이 비어있습니다
                    </p>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="history" className="flex-1 overflow-hidden m-0 p-2">
              <ScrollArea className="h-full">
                <div className="space-y-1">
                  {debugState.history.map((snapshot, index) => (
                    <div
                      key={snapshot.id}
                      className="flex items-center gap-2 p-2 rounded-md hover:bg-muted/50 cursor-pointer"
                      onClick={() => onTimeTravel(snapshot.id)}
                    >
                      <div className="flex-shrink-0 w-6 h-6 rounded-full bg-muted flex items-center justify-center text-xs font-medium">
                        {debugState.history.length - index}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{snapshot.nodeName}</div>
                        <div className="text-xs text-muted-foreground">{snapshot.description}</div>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(snapshot.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  ))}
                  {debugState.history.length === 0 && (
                    <p className="text-xs text-muted-foreground text-center py-4">
                      실행 기록이 없습니다
                    </p>
                  )}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* AI Assistant Footer */}
      {selectedNode?.error && (
        <div className="border-t p-3 bg-gradient-to-r from-purple-50 to-blue-50">
          <div className="flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-purple-500 mt-0.5" />
            <div className="flex-1">
              <div className="text-xs font-medium text-purple-700 mb-1">AI 분석</div>
              <p className="text-xs text-gray-600">
                이 오류는 입력 데이터의 구조가 예상과 다를 때 발생합니다. 
                데이터가 null이거나 필요한 키가 없는지 확인하세요.
              </p>
              <div className="flex gap-2 mt-2">
                <Button size="sm" variant="outline" className="h-6 text-xs">
                  자동 수정
                </Button>
                <Button size="sm" variant="ghost" className="h-6 text-xs">
                  자세히 보기
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default VisualDebugger;
