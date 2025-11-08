"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Copy, Check, Loader2 } from 'lucide-react';

interface WebhookConfigProps {
  workflowId: string;
  onTriggerCreated?: (trigger: any) => void;
}

export function WebhookConfig({ workflowId, onTriggerCreated }: WebhookConfigProps) {
  const [httpMethod, setHttpMethod] = useState<string>('POST');
  const [webhookUrl, setWebhookUrl] = useState<string>('');
  const [webhookSecret, setWebhookSecret] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<'url' | 'secret' | null>(null);

  const handleCreateWebhook = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/triggers/webhook`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          http_method: httpMethod,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create webhook');
      }

      const data = await response.json();
      setWebhookUrl(data.webhook_url);
      setWebhookSecret(data.webhook_secret);

      if (onTriggerCreated) {
        onTriggerCreated(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async (text: string, type: 'url' | 'secret') => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(type);
      setTimeout(() => setCopied(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="http-method">HTTP Method</Label>
        <Select value={httpMethod} onValueChange={setHttpMethod}>
          <SelectTrigger id="http-method">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="GET">GET</SelectItem>
            <SelectItem value="POST">POST</SelectItem>
            <SelectItem value="PUT">PUT</SelectItem>
            <SelectItem value="PATCH">PATCH</SelectItem>
            <SelectItem value="DELETE">DELETE</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {!webhookUrl ? (
        <Button
          onClick={handleCreateWebhook}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Create Webhook
        </Button>
      ) : (
        <div className="space-y-4">
          <Alert>
            <AlertDescription>
              Webhook created successfully! Use the URL below to trigger this workflow.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label>Webhook URL</Label>
            <div className="flex gap-2">
              <Input
                value={webhookUrl}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                size="icon"
                variant="outline"
                onClick={() => copyToClipboard(webhookUrl, 'url')}
              >
                {copied === 'url' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Webhook Secret</Label>
            <div className="flex gap-2">
              <Input
                value={webhookSecret}
                readOnly
                type="password"
                className="font-mono text-sm"
              />
              <Button
                size="icon"
                variant="outline"
                onClick={() => copyToClipboard(webhookSecret, 'secret')}
              >
                {copied === 'secret' ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
            <p className="text-sm text-muted-foreground">
              Include this secret in the X-Webhook-Signature header for verification
            </p>
          </div>
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
