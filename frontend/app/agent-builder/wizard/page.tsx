'use client';

import { useRouter } from 'next/navigation';
import { WorkflowWizard } from '@/components/agent-builder';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function WorkflowWizardPage() {
  const router = useRouter();

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => router.push('/agent-builder')}
        className="mb-6"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        대시보드로 돌아가기
      </Button>

      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-3">
          워크플로우 생성 마법사
        </h1>
        <p className="text-lg text-muted-foreground">
          단계별 가이드를 따라 쉽게 워크플로우를 만들어보세요
        </p>
      </div>

      {/* Wizard Component */}
      <WorkflowWizard
        onComplete={(data) => {
          console.log('Workflow created:', data);
        }}
        onCancel={() => router.push('/agent-builder')}
      />
    </div>
  );
}
