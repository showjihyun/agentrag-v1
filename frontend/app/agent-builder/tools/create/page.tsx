'use client';

import { useRouter } from 'next/navigation';
import { CustomToolBuilder } from '@/components/agent-builder/CustomToolBuilder';
import { toast } from 'sonner';

export default function CreateToolPage() {
  const router = useRouter();

  const handleSave = async (tool: any) => {
    try {
      const response = await fetch('/api/agent-builder/tools/custom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(tool),
      });

      if (!response.ok) {
        throw new Error('Failed to create tool');
      }

      toast.success('Custom tool created successfully!');
      router.push('/agent-builder/tools');
    } catch (error: any) {
      toast.error(error.message || 'Failed to create tool');
      throw error;
    }
  };

  return (
    <div className="container mx-auto py-8">
      <CustomToolBuilder onSave={handleSave} />
    </div>
  );
}
