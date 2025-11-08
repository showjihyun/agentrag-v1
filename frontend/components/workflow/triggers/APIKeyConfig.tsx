"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Copy, Check, Loader2, Key } from 'lucide-react';

interface APIKeyConfigProps {
  workflowId: string;
  onTriggerCreated?: (trigger: any) => void;
}

export function APIKeyConfig({ workflowId, onTriggerCreated }: APIKeyConfigProps) {
  const [apiKey, setApiKey] = useState<string>('');
  const [apiEndpoint, setApiEndpoint] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<'key' | 'endpoint' | null>(null);

  const handleGenerateKey = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/triggers/api`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to generate API key');
      }

      const data = await response.json();
      setApiKey(data.api_key);
      setApiEndpoint(data.api_endpoint);

      if (onTriggerCreated) {
        onTriggerCreated(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async (text: string, type: 'key' | 'endpoint') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const exampleCurl = apiKey && apiEndpoint ? `curl -X POST ${apiEndpoint} \\
  -H "X-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{"input_data": {"key": "value"}}'` : '';

  return (
    <div className="space-y-4">
      {!apiKey ? (
        <Button
          onClick={handleGenerateKey}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <Key className="mr-2 h-4 w-4" />
          Generate API Key
        </Button>
      ) : (
        <div className="space-y-4">
          <Alert>
            <AlertDescription>
              API key generated successfully! Use this key to authenticate API requests.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label>API Endpoint</Label>
            <div className="flex gap-2">
              <Input
                value={apiEndpoint}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                size="icon"
                variant="outline"
                onClick={() => copyToClipboard(apiEndpoint, 'endpoint')}
              >
                {copied === 'endpoint' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label>API Key</Label>
            <div className="flex gap-2">
              <Input
                value={apiKey}
                readOnly
                type="password"
                className="font-mono text-sm"
              />
              <Button
                size="icon"
                variant="outline"
                onClick={() => copyToClipboard(apiKey, 'key')}
              >
                {copied === 'key' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Include this key in the X-API-Key header for authentication
            </p>
          </div>

          <div className="space-y-2">
            <Label>Example cURL Request</Label>
            <div className="relative">
              <pre className="bg-muted p-4 rounded-md overflow-x-auto text-sm">
                <code>{exampleCurl}</code>
              </pre>
              <Button
                size="sm"
                variant="ghost"
                className="absolute top-2 right-2"
                onClick={() => copyToClipboard(exampleCurl, 'endpoint')}
              >
                {copied === 'endpoint' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <Alert>
            <AlertDescription>
              <strong>Rate Limit:</strong> 100 requests per hour
            </AlertDescription>
          </Alert>
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
