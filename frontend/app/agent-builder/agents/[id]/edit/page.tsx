'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChevronLeft, Loader2, AlertCircle } from 'lucide-react';
import { AgentWizard } from '@/components/agent-builder/AgentWizard';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

export default function EditAgentPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  
  const [agentData, setAgentData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgent = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const agent = await agentBuilderAPI.getAgent(agentId);
        setAgentData(agent);
      } catch (err: any) {
        console.error('Failed to fetch agent:', err);
        setError(err.message || 'Failed to load agent');
      } finally {
        setIsLoading(false);
      }
    };

    if (agentId) {
      fetchAgent();
    }
  }, [agentId]);

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-5xl">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">Loading agent...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !agentData) {
    return (
      <div className="container mx-auto p-6 max-w-5xl">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          뒤로가기
        </Button>
        
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Agent를 찾을 수 없습니다'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          뒤로가기
        </Button>
        
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Agent 수정
          </h1>
        </div>
        
        <p className="text-muted-foreground">
          {agentData.name} Agent의 설정을 수정하세요
        </p>
      </div>

      <AgentWizard 
        agentId={agentId}
        initialData={agentData}
        mode="edit"
      />
    </div>
  );
}
