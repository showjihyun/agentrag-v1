'use client';

import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import DocumentUpload from '@/components/agent-builder/DocumentUpload';

export default function KnowledgebaseUploadPage() {
  const params = useParams();
  const router = useRouter();
  const kbId = params.id as string;

  const handleUploadComplete = () => {
    // Optionally navigate back or show success message
    setTimeout(() => {
      router.push('/agent-builder/knowledgebases');
    }, 2000);
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/agent-builder/knowledgebases')}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Upload Documents</h1>
          <p className="text-sm text-muted-foreground">
            Add documents to your knowledgebase
          </p>
        </div>
      </div>

      <DocumentUpload
        knowledgebaseId={kbId}
        onUploadComplete={handleUploadComplete}
      />
    </div>
  );
}
