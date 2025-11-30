'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { MessageSquare } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function SlackTriggerConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    event_type: data.event_type || 'message',
    channel: data.channel || '',
    user_filter: data.user_filter || '',
    keyword_filter: data.keyword_filter || '',
    bot_token: data.bot_token || '',
    include_thread_replies: data.include_thread_replies || false,
    ignore_bot_messages: data.ignore_bot_messages !== false,
    mention_only: data.mention_only || false,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950">
          <MessageSquare className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="font-semibold">Slack Trigger</h3>
          <p className="text-sm text-muted-foreground">Trigger on Slack events</p>
        </div>
      </div>

      {/* Bot Token */}
      <div className="space-y-2">
        <Label>Bot Token</Label>
        <Input
          type="password"
          placeholder="xoxb-..."
          value={config.bot_token}
          onChange={(e) => updateConfig('bot_token', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Slack Bot OAuth Token (or use environment variable)
        </p>
      </div>

      {/* Event Type */}
      <div className="space-y-2">
        <Label>Event Type</Label>
        <Select value={config.event_type} onValueChange={(v) => updateConfig('event_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="message">New Message</SelectItem>
            <SelectItem value="reaction_added">Reaction Added</SelectItem>
            <SelectItem value="file_shared">File Shared</SelectItem>
            <SelectItem value="channel_created">Channel Created</SelectItem>
            <SelectItem value="member_joined">Member Joined Channel</SelectItem>
            <SelectItem value="app_mention">App Mentioned</SelectItem>
            <SelectItem value="slash_command">Slash Command</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Channel Filter */}
      <div className="space-y-2">
        <Label>Channel (optional)</Label>
        <Input
          placeholder="#general or C1234567890"
          value={config.channel}
          onChange={(e) => updateConfig('channel', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Leave empty to listen to all channels
        </p>
      </div>

      {/* User Filter */}
      <div className="space-y-2">
        <Label>User Filter (optional)</Label>
        <Input
          placeholder="U1234567890 or @username"
          value={config.user_filter}
          onChange={(e) => updateConfig('user_filter', e.target.value)}
        />
      </div>

      {/* Keyword Filter */}
      {config.event_type === 'message' && (
        <div className="space-y-2">
          <Label>Keyword Filter (optional)</Label>
          <Input
            placeholder="help, support, urgent"
            value={config.keyword_filter}
            onChange={(e) => updateConfig('keyword_filter', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Comma-separated keywords to match
          </p>
        </div>
      )}

      {/* Options */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Mention Only</Label>
            <p className="text-xs text-muted-foreground">Only trigger when bot is mentioned</p>
          </div>
          <Switch
            checked={config.mention_only}
            onCheckedChange={(checked) => updateConfig('mention_only', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Ignore Bot Messages</Label>
            <p className="text-xs text-muted-foreground">Don't trigger on messages from bots</p>
          </div>
          <Switch
            checked={config.ignore_bot_messages}
            onCheckedChange={(checked) => updateConfig('ignore_bot_messages', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Include Thread Replies</Label>
            <p className="text-xs text-muted-foreground">Trigger on thread replies too</p>
          </div>
          <Switch
            checked={config.include_thread_replies}
            onCheckedChange={(checked) => updateConfig('include_thread_replies', checked)}
          />
        </div>
      </div>
    </div>
  );
}
