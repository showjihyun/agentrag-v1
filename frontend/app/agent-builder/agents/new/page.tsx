'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ChevronLeft, Sparkles, Info } from 'lucide-react';
import { AgentWizard } from '@/components/agent-builder/AgentWizard';

export default function NewAgentPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [templateData, setTemplateData] = useState<any>(null);
  const [isFromTemplate, setIsFromTemplate] = useState(false);

  console.log('[NewAgentPage] Component rendered');

  useEffect(() => {
    const templateParam = searchParams.get('template');
    console.log('[NewAgentPage] Template param:', templateParam);
    if (templateParam) {
      try {
        const template = JSON.parse(decodeURIComponent(templateParam));
        console.log('[NewAgentPage] Parsed template:', template);
        setTemplateData(template);
        setIsFromTemplate(true);
      } catch (error) {
        console.error('[NewAgentPage] Failed to parse template data:', error);
      }
    }
  }, [searchParams]);

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
        
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Create New Agent
          </h1>
          {isFromTemplate && (
            <Badge className="bg-gradient-to-r from-blue-500 to-purple-500 text-white">
              <Sparkles className="h-3 w-3 mr-1" />
              From Template
            </Badge>
          )}
        </div>
        
        <p className="text-muted-foreground">
          {isFromTemplate 
            ? `Configure your AI agent based on the ${templateData?.name} template`
            : 'Follow the step-by-step guide to configure your AI agent'
          }
        </p>

        {isFromTemplate && templateData && (
          <Alert className="mt-4 border-blue-200 bg-blue-50 dark:bg-blue-950/20">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 dark:text-blue-200">
              <strong>{templateData.name}</strong> template has been applied. 
              {templateData.orchestrationType?.length > 0 && (
                <span> This template is optimized for <strong>{templateData.orchestrationType.join(', ')}</strong> orchestration.</span>
              )}
            </AlertDescription>
          </Alert>
        )}
      </div>

      <AgentWizard templateData={templateData} />
    </div>
  );
}
