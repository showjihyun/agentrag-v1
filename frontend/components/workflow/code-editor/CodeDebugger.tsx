'use client';

import { useState, useCallback, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Bug,
  Play,
  Pause,
  SkipForward,
  ArrowDown,
  ArrowUp,
  Circle,
  CircleDot,
  Trash2,
  Eye,
  Plus,
  ChevronRight,
  ChevronDown,
  Loader2,
  AlertTriangle,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { toast } from 'sonner';

interface Breakpoint {
  line: number;
  condition?: string;
  enabled: boolean;
}

interface Variable {
  name: string;
  value: any;
  type: string;
}

interface StackFrame {
  function: string;
  line: number;
  file?: string;
}

interface DebugState {
  status: 'idle' | 'running' | 'paused' | 'finished' | 'error';
  currentLine?: number;
  variables: Variable[];
  callStack: StackFrame[];
  output: string[];
  error?: string;
}

interface CodeDebuggerProps {
  code: string;
  language: string;
  input: any;
  onBreakpointsChange?: (breakpoints: Breakpoint[]) => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function CodeDebugger({
  code,
  language,
  input,
  onBreakpointsChange,
}: CodeDebuggerProps) {
  const [breakpoints, setBreakpoints] = useState<Breakpoint[]>([]);
  const [debugState, setDebugState] = useState<DebugState>({
    status: 'idle',
    variables: [],
    callStack: [],
    output: [],
  });
  const [watchExpressions, setWatchExpressions] = useState<string[]>([]);
  const [newWatch, setNewWatch] = useState('');
  const [expandedVars, setExpandedVars] = useState<Set<string>>(new Set());
  const [sessionId, setSessionId] = useState<string | null>(null);

  // 디버그 세션 시작
  const startDebug = useCallback(async () => {
    setDebugState({ status: 'running', variables: [], callStack: [], output: [] });
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/debug/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          code,
          language,
          input,
          breakpoints: breakpoints.filter(b => b.enabled).map(b => b.line),
        }),
      });

      const result = await response.json();
      if (result.session_id) {
        setSessionId(result.session_id);
        setDebugState(prev => ({
          ...prev,
          status: result.status || 'paused',
          currentLine: result.current_line,
          variables: result.variables || [],
          callStack: result.call_stack || [],
        }));
      }
    } catch (error) {
      setDebugState(prev => ({ ...prev, status: 'error', error: '디버그 시작 실패' }));
      toast.error('디버그 세션 시작 실패');
    }
  }, [code, language, input, breakpoints]);

  // Continue 실행
  const continueExecution = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/debug/continue`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const result = await response.json();
      setDebugState(prev => ({
        ...prev,
        status: result.status,
        currentLine: result.current_line,
        variables: result.variables || prev.variables,
        callStack: result.call_stack || prev.callStack,
        output: [...prev.output, ...(result.output || [])],
      }));
    } catch (error) {
      toast.error('실행 계속 실패');
    }
  }, [sessionId]);

  // Step Over
  const stepOver = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/debug/step-over`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const result = await response.json();
      setDebugState(prev => ({
        ...prev,
        status: result.status,
        currentLine: result.current_line,
        variables: result.variables || prev.variables,
        callStack: result.call_stack || prev.callStack,
      }));
    } catch (error) {
      toast.error('Step Over 실패');
    }
  }, [sessionId]);

  // Step Into
  const stepInto = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/debug/step-into`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const result = await response.json();
      setDebugState(prev => ({
        ...prev,
        status: result.status,
        currentLine: result.current_line,
        variables: result.variables || prev.variables,
        callStack: result.call_stack || prev.callStack,
      }));
    } catch (error) {
      toast.error('Step Into 실패');
    }
  }, [sessionId]);

  // Step Out
  const stepOut = useCallback(async () => {
    if (!sessionId) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/workflow/debug/step-out`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ session_id: sessionId }),
      });

      const result = await response.json();
      setDebugState(prev => ({
        ...prev,
        status: result.status,
        currentLine: result.current_line,
        variables: result.variables || prev.variables,
        callStack: result.call_stack || prev.callStack,
      }));
    } catch (error) {
      toast.error('Step Out 실패');
    }
  }, [sessionId]);

  // 디버그 중지
  const stopDebug = useCallback(async () => {
    if (sessionId) {
      try {
        const token = localStorage.getItem('token');
        await fetch(`${API_BASE}/api/workflow/debug/stop`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({ session_id: sessionId }),
        });
      } catch (error) {
        console.error('Stop debug error:', error);
      }
    }
    setSessionId(null);
    setDebugState({ status: 'idle', variables: [], callStack: [], output: [] });
  }, [sessionId]);

  // Breakpoint 토글
  const toggleBreakpoint = (line: number) => {
    setBreakpoints(prev => {
      const existing = prev.find(b => b.line === line);
      if (existing) {
        return prev.filter(b => b.line !== line);
      }
      return [...prev, { line, enabled: true }];
    });
  };

  // Watch expression 추가
  const addWatchExpression = () => {
    if (newWatch.trim() && !watchExpressions.includes(newWatch.trim())) {
      setWatchExpressions(prev => [...prev, newWatch.trim()]);
      setNewWatch('');
    }
  };

  // 변수 확장 토글
  const toggleVarExpand = (name: string) => {
    setExpandedVars(prev => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  // Breakpoints 변경 알림
  useEffect(() => {
    onBreakpointsChange?.(breakpoints);
  }, [breakpoints, onBreakpointsChange]);

  const isDebugging = debugState.status === 'running' || debugState.status === 'paused';

  return (
    <div className="space-y-4">
      {/* Debugger Header */}
      <div className="flex items-center gap-2 p-3 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800">
        <Bug className="h-5 w-5 text-orange-600" />
        <span className="font-medium flex-1">Interactive Debugger</span>
        <Badge 
          variant={debugState.status === 'paused' ? 'default' : 'secondary'}
          className="text-xs"
        >
          {debugState.status === 'idle' && '대기'}
          {debugState.status === 'running' && '실행 중'}
          {debugState.status === 'paused' && `일시정지 (Line ${debugState.currentLine})`}
          {debugState.status === 'finished' && '완료'}
          {debugState.status === 'error' && '에러'}
        </Badge>
      </div>

      {/* Debug Controls */}
      <div className="flex gap-2 flex-wrap">
        {!isDebugging ? (
          <Button onClick={startDebug} size="sm" className="gap-2 bg-green-600 hover:bg-green-700">
            <Play className="h-4 w-4" />
            디버그 시작
          </Button>
        ) : (
          <>
            <Button onClick={continueExecution} size="sm" variant="outline" className="gap-1" disabled={debugState.status !== 'paused'}>
              <Play className="h-4 w-4" />
              계속
            </Button>
            <Button onClick={stepOver} size="sm" variant="outline" className="gap-1" disabled={debugState.status !== 'paused'}>
              <SkipForward className="h-4 w-4" />
              Step Over
            </Button>
            <Button onClick={stepInto} size="sm" variant="outline" className="gap-1" disabled={debugState.status !== 'paused'}>
              <ArrowDown className="h-4 w-4" />
              Step Into
            </Button>
            <Button onClick={stepOut} size="sm" variant="outline" className="gap-1" disabled={debugState.status !== 'paused'}>
              <ArrowUp className="h-4 w-4" />
              Step Out
            </Button>
            <Button onClick={stopDebug} size="sm" variant="destructive" className="gap-1">
              <Pause className="h-4 w-4" />
              중지
            </Button>
          </>
        )}
      </div>

      {/* Breakpoints */}
      <div className="space-y-2">
        <Label className="text-xs font-medium">Breakpoints</Label>
        <div className="flex flex-wrap gap-2">
          {breakpoints.length === 0 ? (
            <p className="text-xs text-muted-foreground">에디터에서 라인 번호를 클릭하여 breakpoint 추가</p>
          ) : (
            breakpoints.map((bp) => (
              <Badge
                key={bp.line}
                variant={bp.enabled ? 'default' : 'secondary'}
                className="gap-1 cursor-pointer"
                onClick={() => toggleBreakpoint(bp.line)}
              >
                <CircleDot className="h-3 w-3" />
                Line {bp.line}
                {bp.condition && <span className="text-xs opacity-70">({bp.condition})</span>}
              </Badge>
            ))
          )}
        </div>
      </div>

      {/* Variables Panel */}
      {debugState.variables.length > 0 && (
        <div className="space-y-2">
          <Label className="text-xs font-medium">Variables</Label>
          <ScrollArea className="h-40 border rounded-lg p-2">
            {debugState.variables.map((variable) => (
              <div key={variable.name} className="py-1">
                <div
                  className="flex items-center gap-2 cursor-pointer hover:bg-muted rounded px-1"
                  onClick={() => toggleVarExpand(variable.name)}
                >
                  {typeof variable.value === 'object' ? (
                    expandedVars.has(variable.name) ? (
                      <ChevronDown className="h-3 w-3" />
                    ) : (
                      <ChevronRight className="h-3 w-3" />
                    )
                  ) : (
                    <span className="w-3" />
                  )}
                  <span className="text-xs font-mono text-blue-600">{variable.name}</span>
                  <span className="text-xs text-muted-foreground">: {variable.type}</span>
                  <span className="text-xs font-mono ml-auto">
                    {typeof variable.value === 'object'
                      ? expandedVars.has(variable.name)
                        ? ''
                        : '{...}'
                      : String(variable.value).slice(0, 50)}
                  </span>
                </div>
                {expandedVars.has(variable.name) && typeof variable.value === 'object' && (
                  <pre className="text-xs ml-6 p-2 bg-muted rounded mt-1 overflow-auto max-h-20">
                    {JSON.stringify(variable.value, null, 2)}
                  </pre>
                )}
              </div>
            ))}
          </ScrollArea>
        </div>
      )}

      {/* Call Stack */}
      {debugState.callStack.length > 0 && (
        <div className="space-y-2">
          <Label className="text-xs font-medium">Call Stack</Label>
          <div className="border rounded-lg p-2 space-y-1">
            {debugState.callStack.map((frame, idx) => (
              <div
                key={idx}
                className={`text-xs font-mono px-2 py-1 rounded ${idx === 0 ? 'bg-yellow-100 dark:bg-yellow-900/30' : ''}`}
              >
                {frame.function}() <span className="text-muted-foreground">at line {frame.line}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Watch Expressions */}
      <div className="space-y-2">
        <Label className="text-xs font-medium">Watch Expressions</Label>
        <div className="flex gap-2">
          <Input
            value={newWatch}
            onChange={(e) => setNewWatch(e.target.value)}
            placeholder="변수 또는 표현식 입력"
            className="text-xs h-8"
            onKeyDown={(e) => e.key === 'Enter' && addWatchExpression()}
          />
          <Button size="sm" variant="outline" onClick={addWatchExpression}>
            <Plus className="h-4 w-4" />
          </Button>
        </div>
        {watchExpressions.length > 0 && (
          <div className="space-y-1">
            {watchExpressions.map((expr) => (
              <div key={expr} className="flex items-center gap-2 text-xs bg-muted rounded px-2 py-1">
                <Eye className="h-3 w-3" />
                <span className="font-mono">{expr}</span>
                <span className="text-muted-foreground ml-auto">= ...</span>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-5 w-5 p-0"
                  onClick={() => setWatchExpressions(prev => prev.filter(e => e !== expr))}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Output */}
      {debugState.output.length > 0 && (
        <div className="space-y-2">
          <Label className="text-xs font-medium">Output</Label>
          <pre className="text-xs bg-black text-green-400 p-2 rounded-lg overflow-auto max-h-32 font-mono">
            {debugState.output.join('\n')}
          </pre>
        </div>
      )}

      {/* Error Display */}
      {debugState.error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/30 rounded-lg border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-2 text-red-600">
            <XCircle className="h-4 w-4" />
            <span className="text-sm font-medium">에러</span>
          </div>
          <p className="text-xs text-red-500 mt-1">{debugState.error}</p>
        </div>
      )}
    </div>
  );
}
