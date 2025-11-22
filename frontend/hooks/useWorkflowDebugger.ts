import { useState, useCallback, useRef } from 'react';
import { Node } from 'reactflow';

export interface BreakpointConfig {
  nodeId: string;
  enabled: boolean;
  condition?: string;
}

export interface ExecutionState {
  nodeId: string;
  timestamp: Date;
  status: 'running' | 'success' | 'error' | 'paused';
  input?: any;
  output?: any;
  error?: string;
  duration?: number;
  memory?: number;
  cpu?: number;
}

export interface DebuggerState {
  isDebugging: boolean;
  isPaused: boolean;
  currentNodeId?: string;
  breakpoints: BreakpointConfig[];
  executionHistory: ExecutionState[];
  timeTravelIndex?: number;
}

export function useWorkflowDebugger() {
  const [state, setState] = useState<DebuggerState>({
    isDebugging: false,
    isPaused: false,
    breakpoints: [],
    executionHistory: [],
  });

  const executionQueueRef = useRef<string[]>([]);
  const pauseResolveRef = useRef<(() => void) | null>(null);

  // Toggle breakpoint
  const toggleBreakpoint = useCallback((nodeId: string) => {
    setState((prev) => {
      const existing = prev.breakpoints.find(bp => bp.nodeId === nodeId);
      
      if (existing) {
        return {
          ...prev,
          breakpoints: prev.breakpoints.map(bp =>
            bp.nodeId === nodeId ? { ...bp, enabled: !bp.enabled } : bp
          ),
        };
      } else {
        return {
          ...prev,
          breakpoints: [...prev.breakpoints, { nodeId, enabled: true }],
        };
      }
    });
  }, []);

  // Add breakpoint with condition
  const addBreakpoint = useCallback((nodeId: string, condition?: string) => {
    setState((prev) => ({
      ...prev,
      breakpoints: [
        ...prev.breakpoints.filter(bp => bp.nodeId !== nodeId),
        { nodeId, enabled: true, condition },
      ],
    }));
  }, []);

  // Remove breakpoint
  const removeBreakpoint = useCallback((nodeId: string) => {
    setState((prev) => ({
      ...prev,
      breakpoints: prev.breakpoints.filter(bp => bp.nodeId !== nodeId),
    }));
  }, []);

  // Check if should pause at node
  const shouldPauseAtNode = useCallback((nodeId: string, context?: any): boolean => {
    const breakpoint = state.breakpoints.find(bp => bp.nodeId === nodeId);
    
    if (!breakpoint || !breakpoint.enabled) {
      return false;
    }

    // If no condition, always pause
    if (!breakpoint.condition) {
      return true;
    }

    // Evaluate condition (simple implementation)
    try {
      // In production, use a safe expression evaluator
      return eval(breakpoint.condition);
    } catch {
      return true; // Pause on condition error
    }
  }, [state.breakpoints]);

  // Start debugging
  const startDebugging = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isDebugging: true,
      isPaused: false,
      executionHistory: [],
      timeTravelIndex: undefined,
    }));
  }, []);

  // Stop debugging
  const stopDebugging = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isDebugging: false,
      isPaused: false,
      currentNodeId: undefined,
    }));
    
    // Resume if paused
    if (pauseResolveRef.current) {
      pauseResolveRef.current();
      pauseResolveRef.current = null;
    }
  }, []);

  // Pause execution
  const pause = useCallback((): Promise<void> => {
    return new Promise((resolve) => {
      setState((prev) => ({ ...prev, isPaused: true }));
      pauseResolveRef.current = () => {
        setState((prev) => ({ ...prev, isPaused: false }));
        resolve();
      };
    });
  }, []);

  // Continue execution
  const continueExecution = useCallback(() => {
    if (pauseResolveRef.current) {
      pauseResolveRef.current();
      pauseResolveRef.current = null;
    }
  }, []);

  // Step over (execute current node and pause at next)
  const stepOver = useCallback(() => {
    continueExecution();
    // Will pause at next breakpoint or node
  }, [continueExecution]);

  // Step into (if current node has sub-workflow, step into it)
  const stepInto = useCallback(() => {
    continueExecution();
    // Implementation depends on workflow structure
  }, [continueExecution]);

  // Record execution state
  const recordExecution = useCallback((executionState: ExecutionState) => {
    setState((prev) => ({
      ...prev,
      currentNodeId: executionState.nodeId,
      executionHistory: [...prev.executionHistory, executionState],
    }));
  }, []);

  // Time travel to specific execution
  const timeTravel = useCallback((timestamp: Date) => {
    setState((prev) => {
      const index = prev.executionHistory.findIndex(
        state => state.timestamp.getTime() === timestamp.getTime()
      );
      
      return {
        ...prev,
        timeTravelIndex: index >= 0 ? index : undefined,
      };
    });
  }, []);

  // Get current execution state (considering time travel)
  const getCurrentState = useCallback((): ExecutionState | undefined => {
    if (state.timeTravelIndex !== undefined) {
      return state.executionHistory[state.timeTravelIndex];
    }
    return state.executionHistory[state.executionHistory.length - 1];
  }, [state.executionHistory, state.timeTravelIndex]);

  // Execute node with debugging
  const executeNodeWithDebug = useCallback(async (
    nodeId: string,
    executeFn: () => Promise<any>
  ): Promise<any> => {
    const startTime = Date.now();
    
    // Record start
    recordExecution({
      nodeId,
      timestamp: new Date(),
      status: 'running',
    });

    // Check if should pause
    if (state.isDebugging && shouldPauseAtNode(nodeId)) {
      await pause();
    }

    try {
      // Execute node
      const result = await executeFn();
      const duration = Date.now() - startTime;

      // Record success
      recordExecution({
        nodeId,
        timestamp: new Date(),
        status: 'success',
        output: result,
        duration,
      });

      return result;
    } catch (error: any) {
      const duration = Date.now() - startTime;

      // Record error
      recordExecution({
        nodeId,
        timestamp: new Date(),
        status: 'error',
        error: error.message,
        duration,
      });

      throw error;
    }
  }, [state.isDebugging, shouldPauseAtNode, pause, recordExecution]);

  // Restart execution
  const restart = useCallback(() => {
    setState((prev) => ({
      ...prev,
      executionHistory: [],
      currentNodeId: undefined,
      timeTravelIndex: undefined,
      isPaused: false,
    }));
    
    if (pauseResolveRef.current) {
      pauseResolveRef.current();
      pauseResolveRef.current = null;
    }
  }, []);

  // Get performance metrics
  const getPerformanceMetrics = useCallback(() => {
    const { executionHistory } = state;
    
    if (executionHistory.length === 0) {
      return {
        totalDuration: 0,
        avgDuration: 0,
        successRate: 0,
        errorRate: 0,
        nodeMetrics: {},
      };
    }

    const totalDuration = executionHistory.reduce((sum, s) => sum + (s.duration || 0), 0);
    const successCount = executionHistory.filter(s => s.status === 'success').length;
    const errorCount = executionHistory.filter(s => s.status === 'error').length;

    // Calculate per-node metrics
    const nodeMetrics: Record<string, {
      executions: number;
      avgDuration: number;
      successRate: number;
      totalDuration: number;
    }> = {};

    executionHistory.forEach((state) => {
      if (!nodeMetrics[state.nodeId]) {
        nodeMetrics[state.nodeId] = {
          executions: 0,
          avgDuration: 0,
          successRate: 0,
          totalDuration: 0,
        };
      }

      const metric = nodeMetrics[state.nodeId];
      metric.executions++;
      metric.totalDuration += state.duration || 0;
    });

    // Calculate averages
    Object.keys(nodeMetrics).forEach((nodeId) => {
      const metric = nodeMetrics[nodeId];
      metric.avgDuration = metric.totalDuration / metric.executions;
      
      const nodeSuccessCount = executionHistory.filter(
        s => s.nodeId === nodeId && s.status === 'success'
      ).length;
      metric.successRate = (nodeSuccessCount / metric.executions) * 100;
    });

    return {
      totalDuration,
      avgDuration: totalDuration / executionHistory.length,
      successRate: (successCount / executionHistory.length) * 100,
      errorRate: (errorCount / executionHistory.length) * 100,
      nodeMetrics,
    };
  }, [state]);

  return {
    // State
    ...state,
    
    // Breakpoint management
    toggleBreakpoint,
    addBreakpoint,
    removeBreakpoint,
    
    // Debugging controls
    startDebugging,
    stopDebugging,
    continueExecution,
    stepOver,
    stepInto,
    restart,
    
    // Execution
    executeNodeWithDebug,
    recordExecution,
    
    // Time travel
    timeTravel,
    getCurrentState,
    
    // Metrics
    getPerformanceMetrics,
  };
}
