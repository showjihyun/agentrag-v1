'use client';

import { useParams } from 'next/navigation';
import BlockTestPanel from '@/components/agent-builder/BlockTestPanel';

export default function BlockTestPage() {
  const params = useParams();
  const blockId = params.id as string;

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <BlockTestPanel blockId={blockId} />
    </div>
  );
}
