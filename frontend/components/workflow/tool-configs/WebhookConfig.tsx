'use client';

/**
 * WebhookConfig - Webhook Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Zap, Copy, Check } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  InfoBox,
  useToolConfig,
} from './common';

// ============================================
// Types
// ============================================

interface WebhookConfigData {
  webhook_id: string;
  path: string;
}

const DEFAULTS: WebhookConfigData = {
  webhook_id: `webhook_${Date.now()}`,
  path: '/webhook',
};

// ============================================
// Component
// ============================================

export default function WebhookConfig({ data, onChange }: ToolConfigProps) {
  const { config } = useToolConfig<WebhookConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const [copied, setCopied] = useState(false);

  const webhookUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/api/webhooks/${config.webhook_id}`
    : `/api/webhooks/${config.webhook_id}`;

  const copyToClipboard = useCallback(() => {
    navigator.clipboard.writeText(webhookUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [webhookUrl]);


  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Zap}
          {...TOOL_HEADER_PRESETS.code}
          title="Webhook"
          description="HTTP 웹훅 수신"
        />

        {/* Webhook URL */}
        <div className="space-y-2">
          <Label>Webhook URL</Label>
          <div className="flex gap-2">
            <Input value={webhookUrl} readOnly className="font-mono text-sm" />
            <Button variant="outline" size="icon" onClick={copyToClipboard}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            이 URL로 POST 요청을 보내 워크플로우를 트리거하세요
          </p>
        </div>

        {/* Info Box */}
        <InfoBox title="사용 방법:">
          <ol className="space-y-1 list-decimal list-inside">
            <li>위의 웹훅 URL을 복사하세요</li>
            <li>서비스에서 이 URL로 POST 요청을 보내도록 설정하세요</li>
            <li>요청 본문은 <code className="px-1 py-0.5 bg-background rounded">{'{{webhook.body}}'}</code>로 접근 가능</li>
            <li>헤더는 <code className="px-1 py-0.5 bg-background rounded">{'{{webhook.headers}}'}</code>로 접근 가능</li>
          </ol>
        </InfoBox>

        {/* Example */}
        <div className="space-y-2">
          <Label>요청 예시</Label>
          <pre className="p-3 bg-muted rounded-lg text-xs font-mono overflow-x-auto">
{`curl -X POST ${webhookUrl} \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Hello from webhook!"}'`}
          </pre>
        </div>
      </div>
    </TooltipProvider>
  );
}
