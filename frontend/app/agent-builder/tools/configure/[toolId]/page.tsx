'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ToolConfigurationPanel } from '@/components/agent-builder/ToolConfigurationPanel';
import { toast } from 'sonner';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ToolConfigurePage() {
  const params = useParams();
  const router = useRouter();
  const toolId = params.toolId as string;

  const [toolConfig, setToolConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [savedConfig, setSavedConfig] = useState<any>(null);

  useEffect(() => {
    fetchToolConfig();
    fetchSavedConfig();
  }, [toolId]);

  const fetchToolConfig = async () => {
    try {
      const response = await fetch(`/api/agent-builder/marketplace/${toolId}`);
      if (!response.ok) throw new Error('Failed to fetch tool');
      
      const data = await response.json();
      setToolConfig({
        tool_id: data.id,
        tool_name: data.name,
        description: data.description,
        parameters: data.parameters,
        examples: data.examples
      });
    } catch (error: any) {
      toast.error(error.message || 'Failed to load tool configuration');
    } finally {
      setLoading(false);
    }
  };

  const fetchSavedConfig = async () => {
    try {
      const response = await fetch(`/api/agent-builder/tools/${toolId}/config`);
      if (response.ok) {
        const data = await response.json();
        setSavedConfig(data.config);
      }
    } catch (error) {
      // No saved config yet
    }
  };

  const handleSave = async (values: Record<string, any>) => {
    try {
      const response = await fetch(`/api/agent-builder/tools/${toolId}/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ config: values }),
      });

      if (!response.ok) throw new Error('Failed to save configuration');

      toast.success('Configuration saved successfully!');
      setSavedConfig(values);
    } catch (error: any) {
      toast.error(error.message || 'Failed to save configuration');
    }
  };

  const handleTest = async (values: Record<string, any>) => {
    const response = await fetch('/api/agent-builder/tools/execute', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        tool_id: toolId,
        parameters: values,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Test failed');
    }

    const result = await response.json();
    if (!result.success) {
      throw new Error(result.error || 'Test failed');
    }

    return result.result;
  };

  if (loading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  if (!toolConfig) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <p className="text-muted-foreground">Tool not found</p>
          <Button onClick={() => router.back()} className="mt-4">
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.back()}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Configure Tool</h1>
          <p className="text-muted-foreground">
            Set up parameters for {toolConfig.tool_name}
          </p>
        </div>
      </div>

      {/* Configuration Panel */}
      <ToolConfigurationPanel
        toolConfig={toolConfig}
        initialValues={savedConfig}
        onSave={handleSave}
        onTest={handleTest}
      />
    </div>
  );
}
