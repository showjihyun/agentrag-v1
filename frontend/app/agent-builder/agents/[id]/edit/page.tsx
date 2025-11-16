'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ChevronLeft, Loader2 } from 'lucide-react';
import { agentBuilderAPI, type Agent } from '@/lib/api/agent-builder';
import { useToast } from '@/hooks/use-toast';
import { AgentWizard } from '@/components/agent-builder/AgentWizard';

export default function EditAgentPage() {
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (agentId) {
      loadAgent();
    }
  }, [agentId]);

  const loadAgent = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getAgent(agentId);
      setAgent(data);
    } catch (error: any) {
      console.error('Failed to load agent:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load agent',
      });
      // Redirect back if agent not found
      setTimeout(() => {
        router.push('/agent-builder/agents');
      }, 2000);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl">
        <div className="mb-6">
          <Skeleton className="h-8 w-32 mb-4" />
          <Skeleton className="h-10 w-64 mb-2" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="space-y-4">
          <Skeleton className="h-[600px] w-full" />
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="container mx-auto p-6 max-w-5xl">
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold mb-4">Agent Not Found</h2>
          <p className="text-muted-foreground mb-6">
            The agent you're trying to edit doesn't exist or you don't have access to it.
          </p>
          <Button onClick={() => router.push('/agent-builder/agents')}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Back to Agents
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push(`/agent-builder/agents/${agentId}`)}
          className="mb-4"
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-3xl font-bold">Edit Agent</h1>
        <p className="text-muted-foreground">
          Update your agent configuration
        </p>
      </div>

      <AgentWizard agentId={agentId} initialData={agent} mode="edit" />
    </div>
  );
}
