import { useState, useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { toast } from 'sonner';
import { useWorkflowDebugger } from './useWorkflowDebugger';

interface UseWorkflowExecutionProps {
  nodes: Node[];
  setNodes: (nodes: Node[] | ((nodes: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((edges: Edge[]) => Edge[])) => void;
}

export function useWorkflowExecution({
  nodes,
  setNodes,
  setEdges,
}: UseWorkflowExecutionProps) {
  const [isExecuting, setIsExecuting] = useState(false);
  const workflowDebugger = useWorkflowDebugger();

  const execute = useCallback(async () => {
    setIsExecuting(true);
    workflowDebugger.startDebugging();

    // Reset all nodes
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: { ...node.data, status: 'idle', executionTime: undefined },
      }))
    );

    // Animate edges
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: true })));

    try {
      // Execute nodes sequentially with debugging
      for (const node of nodes) {
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id ? { ...n, data: { ...n.data, status: 'running' } } : n
          )
        );

        await workflowDebugger.executeNodeWithDebug(node.id, async () => {
          const executionTime = Math.random() * 1000 + 500;
          await new Promise((resolve) => setTimeout(resolve, executionTime));

          const success = Math.random() > 0.1;
          if (!success) {
            throw new Error(`Node ${node.data.label} failed`);
          }

          return {
            result: `Output from ${node.data.label}`,
            executionTime: Math.round(executionTime),
          };
        });

        const currentState = workflowDebugger.getCurrentState();
        setNodes((nds) =>
          nds.map((n) =>
            n.id === node.id
              ? {
                  ...n,
                  data: {
                    ...n.data,
                    status: currentState?.status === 'error' ? 'error' : 'success',
                    executionTime: currentState?.duration,
                  },
                }
              : n
          )
        );

        if (currentState?.status === 'error') {
          break;
        }
      }

      toast.success('Workflow execution completed');
    } catch (error: any) {
      toast.error(`Execution failed: ${error.message}`);
    } finally {
      setEdges((eds) => eds.map((edge) => ({ ...edge, animated: false })));
      setIsExecuting(false);
      workflowDebugger.stopDebugging();
    }
  }, [nodes, setNodes, setEdges, workflowDebugger]);

  const stop = useCallback(() => {
    setIsExecuting(false);
    workflowDebugger.stopDebugging();
    setEdges((eds) => eds.map((edge) => ({ ...edge, animated: false })));
  }, [setEdges, workflowDebugger]);

  const reset = useCallback(() => {
    setNodes((nds) =>
      nds.map((node) => ({
        ...node,
        data: {
          ...node.data,
          status: 'idle',
          executionTime: undefined,
        },
      }))
    );
    workflowDebugger.restart();
  }, [setNodes, workflowDebugger]);

  return {
    isExecuting,
    execute,
    stop,
    reset,
    debugger: workflowDebugger,
  };
}
