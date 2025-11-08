'use client';

import { useRouter, useParams } from 'next/navigation';
import BlockEditor from '@/components/agent-builder/BlockEditor';
import { Block } from '@/lib/api/agent-builder';

export default function EditBlockPage() {
  const router = useRouter();
  const params = useParams();
  const blockId = params.id as string;

  const handleSave = (block: Block) => {
    router.push('/agent-builder/blocks');
  };

  const handleCancel = () => {
    router.push('/agent-builder/blocks');
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <BlockEditor blockId={blockId} onSave={handleSave} onCancel={handleCancel} />
    </div>
  );
}
