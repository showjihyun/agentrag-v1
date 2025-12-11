'use client';

/**
 * SlackTriggerConfig - Slack Trigger Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { MessageSquare } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  SelectField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const EVENT_TYPES = [
  { value: 'message', label: 'New Message' },
  { value: 'reaction_added', label: 'Reaction Added' },
  { value: 'file_shared', label: 'File Shared' },
  { value: 'channel_created', label: 'Channel Created' },
  { value: 'member_joined', label: 'Member Joined Channel' },
  { value: 'app_mention', label: 'App Mentioned' },
  { value: 'slash_command', label: 'Slash Command' },
] as const;

// ============================================
// Types
// ============================================

interface SlackTriggerConfigData {
  event_type: string;
  channel: string;
  user_filter: string;
  keyword_filter: string;
  bot_token: string;
  include_thread_replies: boolean;
  ignore_bot_messages: boolean;
  mention_only: boolean;
}

const DEFAULTS: SlackTriggerConfigData = {
  event_type: 'message',
  channel: '',
  user_filter: '',
  keyword_filter: '',
  bot_token: '',
  include_thread_replies: false,
  ignore_bot_messages: true,
  mention_only: false,
};


// ============================================
// Component
// ============================================

export default function SlackTriggerConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<SlackTriggerConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={MessageSquare}
          {...TOOL_HEADER_PRESETS.slack}
          title="Slack Trigger"
          description="Slack 이벤트 발생 시 트리거"
        />

        {/* Bot Token */}
        <TextField
          label="Bot Token"
          value={config.bot_token}
          onChange={(v) => updateField('bot_token', v)}
          type="password"
          placeholder="xoxb-..."
          hint="Slack Bot OAuth Token (또는 환경 변수 사용)"
        />

        {/* Event Type */}
        <SelectField
          label="이벤트 유형"
          value={config.event_type}
          onChange={(v) => updateField('event_type', v)}
          options={EVENT_TYPES.map(e => ({ value: e.value, label: e.label }))}
        />

        {/* Channel Filter */}
        <TextField
          label="채널 (선택)"
          value={config.channel}
          onChange={(v) => updateField('channel', v)}
          placeholder="#general or C1234567890"
          hint="비워두면 모든 채널에서 수신"
        />

        {/* User Filter */}
        <TextField
          label="사용자 필터 (선택)"
          value={config.user_filter}
          onChange={(v) => updateField('user_filter', v)}
          placeholder="U1234567890 or @username"
        />

        {/* Keyword Filter */}
        {config.event_type === 'message' && (
          <TextField
            label="키워드 필터 (선택)"
            value={config.keyword_filter}
            onChange={(v) => updateField('keyword_filter', v)}
            placeholder="help, support, urgent"
            hint="쉼표로 구분된 매칭 키워드"
          />
        )}

        {/* Options */}
        <SwitchField
          label="멘션만"
          description="봇이 멘션될 때만 트리거"
          checked={config.mention_only}
          onChange={(v) => updateField('mention_only', v)}
        />

        <SwitchField
          label="봇 메시지 무시"
          description="봇의 메시지에는 트리거하지 않음"
          checked={config.ignore_bot_messages}
          onChange={(v) => updateField('ignore_bot_messages', v)}
        />

        <SwitchField
          label="스레드 답글 포함"
          description="스레드 답글에도 트리거"
          checked={config.include_thread_replies}
          onChange={(v) => updateField('include_thread_replies', v)}
        />
      </div>
    </TooltipProvider>
  );
}
