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

  useEffect(() => {
    const templateParam = searchParams.get('template');
    if (templateParam) {
      try {
        const template = JSON.parse(decodeURIComponent(templateParam));
        setTemplateData(template);
        setIsFromTemplate(true);
      } catch (error) {
        console.error('Failed to parse template data:', error);
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
          뒤로가기
        </Button>
        
        <div className="flex items-center gap-3 mb-2">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            새 Agent 생성
          </h1>
          {isFromTemplate && (
            <Badge className="bg-gradient-to-r from-blue-500 to-purple-500 text-white">
              <Sparkles className="h-3 w-3 mr-1" />
              템플릿 기반
            </Badge>
          )}
        </div>
        
        <p className="text-muted-foreground">
          {isFromTemplate 
            ? `${templateData?.name} 템플릿을 기반으로 AI 에이전트를 구성하세요`
            : '단계별 가이드를 따라 AI 에이전트를 구성하세요'
          }
        </p>

        {isFromTemplate && templateData && (
          <Alert className="mt-4 border-blue-200 bg-blue-50 dark:bg-blue-950/20">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800 dark:text-blue-200">
              <strong>{templateData.name}</strong> 템플릿이 적용되었습니다. 
              {templateData.orchestrationType?.length > 0 && (
                <span> 이 템플릿은 <strong>{templateData.orchestrationType.join(', ')}</strong> 오케스트레이션에 최적화되어 있습니다.</span>
              )}
            </AlertDescription>
          </Alert>
        )}
      </div>

      <AgentWizard templateData={templateData} />
    </div>
  );
}
