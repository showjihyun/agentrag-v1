'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Check, ChevronLeft, ChevronRight } from 'lucide-react';
import { AgentWizard } from '@/components/agent-builder/AgentWizard';

export default function NewAgentPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        <h1 className="text-3xl font-bold">Create New Agent</h1>
        <p className="text-muted-foreground">
          Follow the steps to configure your AI agent
        </p>
      </div>

      <AgentWizard />
    </div>
  );
}
