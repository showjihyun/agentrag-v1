'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import HybridSearch from '@/components/agent-builder/HybridSearch';

export default function KnowledgebaseSearchPage() {
  const params = useParams();
  const router = useRouter();
  const kbId = params.id as string;

  return (
    <div className="container mx-auto p-6 max-w-6xl space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/agent-builder/knowledgebases')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">지식베이스 검색</h1>
          <p className="text-sm text-muted-foreground">
            하이브리드 검색을 통해 관련 문서와 지식을 찾아보세요
          </p>
        </div>
      </div>

      <HybridSearch knowledgebaseId={kbId} />
    </div>
  );
}
