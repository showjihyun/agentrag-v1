"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Copy, Check, Loader2, MessageSquare } from 'lucide-react';

interface ChatConfigProps {
  workflowId: string;
  onTriggerCreated?: (trigger: any) => void;
}

export function ChatConfig({ workflowId, onTriggerCreated }: ChatConfigProps) {
  const [chatUrl, setChatUrl] = useState<string>('');
  const [enableStreaming, setEnableStreaming] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleCreateChat = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/triggers/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          enable_streaming: enableStreaming,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create chat interface');
      }

      const data = await response.json();
      setChatUrl(data.chat_url);

      if (onTriggerCreated) {
        onTriggerCreated(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <Label htmlFor="streaming">Enable Streaming</Label>
          <p className="text-sm text-muted-foreground">
            Stream responses in real-time
          </p>
        </div>
        <Switch
          id="streaming"
          checked={enableStreaming}
          onCheckedChange={setEnableStreaming}
          disabled={!!chatUrl}
        />
      </div>

      {!chatUrl ? (
        <Button
          onClick={handleCreateChat}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          <MessageSquare className="mr-2 h-4 w-4" />
          Create Chat Interface
        </Button>
      ) : (
        <div className="space-y-4">
          <Alert>
            <AlertDescription>
              Chat interface created successfully! Share this URL to allow users to chat with your workflow.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label>Chat URL</Label>
            <div className="flex gap-2">
              <Input
                value={chatUrl}
                readOnly
                className="font-mono text-sm"
              />
              <Button
                size="icon"
                variant="outline"
                onClick={() => copyToClipboard(chatUrl)}
              >
                {copied ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <Copy className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Features</Label>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Conversation history (last 10 messages)</li>
              <li>• {enableStreaming ? 'Real-time streaming responses' : 'Standard responses'}</li>
              <li>• WebSocket support for live updates</li>
              <li>• Session management</li>
            </ul>
          </div>

          <Button
            variant="outline"
            className="w-full"
            onClick={() => window.open(chatUrl, '_blank')}
          >
            Open Chat Interface
          </Button>
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
