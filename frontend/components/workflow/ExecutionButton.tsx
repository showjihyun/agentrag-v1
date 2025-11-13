'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Loader2, Eye } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { transformExecutionResult } from '@/lib/execution-utils';
import type { Node } from 'reactflow';

interface ExecutionButtonProps {
  workflowId: string;
  workflowName: string;
  nodes: Node[];
  onExecutionComplete?: (executionDetails: any) => void;
  onShowDetails?: () => void;
  hasExecutionData?: boolean;
}

export function ExecutionButton({
  workflowId,
  workflowName,
  nodes,
  onExecutionComplete,
  onShowDetails,
  hasExecutionData = false,
}: ExecutionButtonProps) {
  const [executing, setExecuting] = useState(false);
  const { toast } = useToast();

  const handleExecute = async () => {
    try {
      setExecuting(true);

      toast({
        title: 'Executing Workflow',
        description: 'Your workflow is being executed...',
      });

      // Execute workflow
      const result = await agentBuilderAPI.executeWorkflow(workflowId, {
        test: true,
        input: 'Test execution',
      });

      // Transform result to execution details format
      const executionDetails = transformExecutionResult(
        result,
        workflowName,
        nodes
      );

      // Notify parent component
      if (onExecutionComplete) {
        onExecutionComplete(executionDetails);
      }

      if (result.success) {
        toast({
          title: 'Execution Completed',
          description: 'Workflow executed successfully',
        });
      } else {
        toast({
          title: 'Execution Failed',
          description: result.error || 'An error occurred during execution',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      console.error('Execution error:', error);
      toast({
        title: 'Execution Error',
        description: error.message || 'Failed to execute workflow',
        variant: 'destructive',
      });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        onClick={handleExecute}
        disabled={executing}
        className="gap-2"
      >
        {executing ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Executing...
          </>
        ) : (
          <>
            <Play className="h-4 w-4" />
            Execute
          </>
        )}
      </Button>

      {hasExecutionData && onShowDetails && (
        <Button
          variant="outline"
          onClick={onShowDetails}
          className="gap-2"
        >
          <Eye className="h-4 w-4" />
          View Details
        </Button>
      )}
    </div>
  );
}
