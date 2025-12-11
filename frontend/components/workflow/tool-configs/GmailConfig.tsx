'use client';

/**
 * GmailConfig - Gmail Integration Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Mail, TestTube } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  TextareaField,
  SelectField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const GMAIL_ACTIONS = [
  { value: 'send_email', label: 'Send Email', description: 'Send an email' },
  { value: 'search_emails', label: 'Search Emails', description: 'Search for emails' },
  { value: 'get_email', label: 'Get Email', description: 'Get a specific email' },
] as const;

const BODY_TYPES = [
  { value: 'html', label: 'HTML' },
  { value: 'plain', label: 'Plain Text' },
] as const;

// ============================================
// Types
// ============================================

interface GmailConfigData {
  action: string;
  to: string;
  cc: string;
  bcc: string;
  subject: string;
  body: string;
  body_type: string;
}

const DEFAULTS: GmailConfigData = {
  action: 'send_email',
  to: '',
  cc: '',
  bcc: '',
  subject: '',
  body: '',
  body_type: 'html',
};

// ============================================
// Component
// ============================================

export default function GmailConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<GmailConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const handleTest = useCallback(() => {
    onTest?.();
  }, [onTest]);

  const isSendEmail = config.action === 'send_email';

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Mail}
          {...TOOL_HEADER_PRESETS.email}
          title="Gmail"
          description="Send and manage emails"
          badge="Popular"
        />

        {/* Action */}
        <SelectField
          label="Action"
          value={config.action}
          onChange={(v) => updateField('action', v)}
          options={GMAIL_ACTIONS.map(a => ({ value: a.value, label: a.label, description: a.description }))}
        />

        {isSendEmail && (
          <>
            {/* To */}
            <TextField
              label="To"
              value={config.to}
              onChange={(v) => updateField('to', v)}
              placeholder="recipient@example.com"
              required
              hint="Comma-separated for multiple recipients"
              tooltip="수신자 이메일 주소. 여러 명에게 보내려면 쉼표로 구분하세요."
            />

            {/* CC */}
            <TextField
              label="CC"
              value={config.cc}
              onChange={(v) => updateField('cc', v)}
              placeholder="cc@example.com"
              hint="Optional"
            />

            {/* BCC */}
            <TextField
              label="BCC"
              value={config.bcc}
              onChange={(v) => updateField('bcc', v)}
              placeholder="bcc@example.com"
              hint="Optional"
            />

            {/* Subject */}
            <TextField
              label="Subject"
              value={config.subject}
              onChange={(v) => updateField('subject', v)}
              placeholder="Email subject..."
              required
            />

            {/* Body Type */}
            <SelectField
              label="Body Type"
              value={config.body_type}
              onChange={(v) => updateField('body_type', v)}
              options={BODY_TYPES.map(t => ({ value: t.value, label: t.label }))}
            />

            {/* Body */}
            <TextareaField
              label="Body"
              value={config.body}
              onChange={(v) => updateField('body', v)}
              placeholder={config.body_type === 'html' ? '<p>Email content...</p>' : 'Email content...'}
              rows={8}
              required
              hint="Use {{variables}} for dynamic content"
              mono={config.body_type === 'html'}
            />
          </>
        )}

        {/* Test Button */}
        {onTest && isSendEmail && (
          <Button
            onClick={handleTest}
            variant="outline"
            className="w-full"
            disabled={!config.to || !config.subject || !config.body}
          >
            <TestTube className="h-4 w-4 mr-2" />
            Test Email
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}
