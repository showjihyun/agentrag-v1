'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import KnowledgebaseSearch from '@/components/agent-builder/KnowledgebaseSearch';

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
          <h1 className="text-2xl font-bold">Search Knowledgebase</h1>
          <p className="text-sm text-muted-foreground">
            Find relevant documents using semantic search
          </p>
        </div>
      </div>

      <KnowledgebaseSearch knowledgebaseId={kbId} />
    </div>
  );
}
