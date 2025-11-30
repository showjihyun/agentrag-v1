'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Zap, Copy, Check } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function WebhookConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    webhook_id: data.webhook_id || `webhook_${Date.now()}`,
    path: data.path || '/webhook',
    ...data
  });
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    onChange(config);
  }, [config]);

  const webhookUrl = `${window.location.origin}/api/webhooks/${config.webhook_id}`;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-950">
          <Zap className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div>
          <h3 className="font-semibold">Webhook</h3>
          <p className="text-sm text-muted-foreground">Receive HTTP webhooks</p>
        </div>
      </div>

      {/* Webhook URL */}
      <div className="space-y-2">
        <Label>Webhook URL</Label>
        <div className="flex gap-2">
          <Input
            value={webhookUrl}
            readOnly
            className="font-mono text-sm"
          />
          <Button
            variant="outline"
            size="icon"
            onClick={copyToClipboard}
          >
            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground">
          Send POST requests to this URL to trigger the workflow
        </p>
      </div>

      {/* Info Box */}
      <div className="p-4 bg-muted rounded-lg space-y-3">
        <p className="text-sm font-medium">How to use:</p>
        <ol className="text-xs space-y-2 list-decimal list-inside text-muted-foreground">
          <li>Copy the webhook URL above</li>
          <li>Configure your service to send POST requests to this URL</li>
          <li>The request body will be available as <code className="px-1 py-0.5 bg-background rounded">{'{{webhook.body}}'}</code></li>
          <li>Headers are available as <code className="px-1 py-0.5 bg-background rounded">{'{{webhook.headers}}'}</code></li>
        </ol>
      </div>

      {/* Example */}
      <div className="space-y-2">
        <Label>Example Request</Label>
        <pre className="p-3 bg-muted rounded-lg text-xs font-mono overflow-x-auto">
{`curl -X POST ${webhookUrl} \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello from webhook!"}'`}
        </pre>
      </div>
    </div>
  );
}
