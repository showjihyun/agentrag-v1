'use client';

import { useRouter } from 'next/navigation';
import BlockEditor from '@/components/agent-builder/BlockEditor';
import { Block } from '@/lib/api/agent-builder';

export default function NewBlockPage() {
  const router = useRouter();

  const handleSave = (block: Block) => {
    // Redirect and force refresh
    router.push('/agent-builder/blocks?refresh=' + Date.now());
    router.refresh();
  };

  const handleCancel = () => {
    router.push('/agent-builder/blocks');
  };

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <BlockEditor onSave={handleSave} onCancel={handleCancel} />
    </div>
  );
}
