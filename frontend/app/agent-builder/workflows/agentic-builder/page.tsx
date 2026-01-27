'use client';

import { AgenticWorkflowCanvas } from '@/components/agent-builder/workflow/AgenticWorkflowCanvas';
import { Node, Edge } from 'reactflow';
import { useToast } from '@/hooks/use-toast';

export default function AgenticWorkflowBuilderPage() {
  const { toast } = useToast();

  const handleSave = (nodes: Node[], edges: Edge[]) => {
    console.log('Saving workflow:', { nodes, edges });
    
    toast({
      title: 'Workflow Saved',
      description: `Saved ${nodes.length} blocks and ${edges.length} connections`,
    });
    
    // Here you would typically save to backend
    // await workflowAPI.save({ nodes, edges });
  };

  return (
    <div className="h-screen">
      <AgenticWorkflowCanvas
        workflowId="agentic-workflow-1"
        onSave={handleSave}
      />
    </div>
  );
}
