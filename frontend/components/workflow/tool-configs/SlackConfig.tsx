'use client';

/**
 * SlackConfig - Slack Integration Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { MessageSquare, Key, Hash, User, TestTube } from 'lucide-react';
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

const SLACK_ACTIONS = [
  { value: 'send_message', label: 'Send Message', description: 'Send a message to a channel or user' },
  { value: 'send_dm', label: 'Send Direct Message', description: 'Send a DM to a specific user' },
  { value: 'create_channel', label: 'Create Channel', description: 'Create a new channel' },
  { value: 'invite_user', label: 'Invite User', description: 'Invite user to a channel' },
] as const;

// ============================================
// Types
// ============================================

interface SlackConfigData {
  bot_token: string;
  action: string;
  channel: string;
  user_id: string;
  message: string;
  thread_ts: string;
}

const DEFAULTS: SlackConfigData = {
  bot_token: '',
  action: 'send_message',
  channel: '',
  user_id: '',
  message: '',
  thread_ts: '',
};

// ============================================
// Component
// ============================================

export default function SlackConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<SlackConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const handleTest = useCallback(() => {
    onTest?.();
  }, [onTest]);

  const showChannel = config.action === 'send_message' || config.action === 'create_channel';
  const showUserId = config.action === 'send_dm';
  const showMessage = config.action === 'send_message' || config.action === 'send_dm';

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={MessageSquare}
          {...TOOL_HEADER_PRESETS.slack}
          title="Slack"
          description="Send messages and manage channels"
          badge="Popular"
        />

        {/* Bot Token */}
        <TextField
          label="Bot Token"
          value={config.bot_token}
          onChange={(v) => updateField('bot_token', v)}
          type="password"
          placeholder="xoxb-..."
          required
          icon={Key}
          hint="Get your bot token from Slack API (api.slack.com/apps)"
          mono
        />

        {/* Action */}
        <SelectField
          label="Action"
          value={config.action}
          onChange={(v) => updateField('action', v)}
          options={SLACK_ACTIONS.map(a => ({ value: a.value, label: a.label, description: a.description }))}
        />

        {/* Channel */}
        {showChannel && (
          <TextField
            label="Channel"
            value={config.channel}
            onChange={(v) => updateField('channel', v)}
            placeholder="#general or C1234567890"
            required={config.action === 'send_message'}
            icon={Hash}
            hint="Channel name (with #) or Channel ID"
          />
        )}

        {/* User ID */}
        {showUserId && (
          <TextField
            label="User ID"
            value={config.user_id}
            onChange={(v) => updateField('user_id', v)}
            placeholder="U1234567890"
            required
            icon={User}
            hint="Slack user ID (starts with U)"
          />
        )}

        {/* Message */}
        {showMessage && (
          <TextareaField
            label="Message"
            value={config.message}
            onChange={(v) => updateField('message', v)}
            placeholder="Hello from workflow! Use {{variables}} for dynamic content..."
            rows={5}
            required
            hint="Supports Slack markdown and {{variables}}"
          />
        )}

        {/* Thread TS */}
        {showMessage && (
          <TextField
            label="Thread Timestamp"
            value={config.thread_ts}
            onChange={(v) => updateField('thread_ts', v)}
            placeholder="1234567890.123456"
            hint="Reply to a specific thread (optional)"
            mono
          />
        )}

        {/* Test Button */}
        {onTest && (
          <Button
            onClick={handleTest}
            variant="outline"
            className="w-full"
            disabled={!config.bot_token || !config.message}
          >
            <TestTube className="h-4 w-4 mr-2" />
            Test Connection
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}
