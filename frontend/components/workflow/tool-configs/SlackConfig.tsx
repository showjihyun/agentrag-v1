'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MessageSquare, Key, Hash, User, TestTube } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const SLACK_ACTIONS = [
  { id: 'send_message', name: 'Send Message', description: 'Send a message to a channel or user' },
  { id: 'send_dm', name: 'Send Direct Message', description: 'Send a DM to a specific user' },
  { id: 'create_channel', name: 'Create Channel', description: 'Create a new channel' },
  { id: 'invite_user', name: 'Invite User', description: 'Invite user to a channel' },
];

export default function SlackConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    bot_token: data.bot_token || '',
    action: data.action || 'send_message',
    channel: data.channel || '',
    user_id: data.user_id || '',
    message: data.message || '',
    thread_ts: data.thread_ts || '',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950">
          <MessageSquare className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="font-semibold">Slack</h3>
          <p className="text-sm text-muted-foreground">Send messages and manage channels</p>
        </div>
        <Badge variant="secondary" className="ml-auto">New</Badge>
      </div>

      {/* Bot Token */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Key className="h-4 w-4" />
          Bot Token *
        </Label>
        <Input
          type="password"
          placeholder="xoxb-..."
          value={config.bot_token}
          onChange={(e) => updateConfig('bot_token', e.target.value)}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Get your bot token from <a href="https://api.slack.com/apps" target="_blank" className="text-primary hover:underline">Slack API</a>
        </p>
      </div>

      {/* Action */}
      <div className="space-y-2">
        <Label>Action</Label>
        <Select value={config.action} onValueChange={(v) => updateConfig('action', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SLACK_ACTIONS.map(action => (
              <SelectItem key={action.id} value={action.id}>
                <div className="flex flex-col">
                  <span className="font-medium">{action.name}</span>
                  <span className="text-xs text-muted-foreground">{action.description}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Channel (for send_message) */}
      {(config.action === 'send_message' || config.action === 'create_channel') && (
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <Hash className="h-4 w-4" />
            Channel {config.action === 'send_message' && '*'}
          </Label>
          <Input
            placeholder="#general or C1234567890"
            value={config.channel}
            onChange={(e) => updateConfig('channel', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Channel name (with #) or Channel ID
          </p>
        </div>
      )}

      {/* User ID (for send_dm) */}
      {config.action === 'send_dm' && (
        <div className="space-y-2">
          <Label className="flex items-center gap-2">
            <User className="h-4 w-4" />
            User ID *
          </Label>
          <Input
            placeholder="U1234567890"
            value={config.user_id}
            onChange={(e) => updateConfig('user_id', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Slack user ID (starts with U)
          </p>
        </div>
      )}

      {/* Message */}
      {(config.action === 'send_message' || config.action === 'send_dm') && (
        <div className="space-y-2">
          <Label>Message *</Label>
          <Textarea
            placeholder="Hello from workflow! Use {{variables}} for dynamic content..."
            value={config.message}
            onChange={(e) => updateConfig('message', e.target.value)}
            rows={5}
          />
          <p className="text-xs text-muted-foreground">
            Supports Slack markdown and <code className="px-1 py-0.5 bg-muted rounded">{'{{variables}}'}</code>
          </p>
        </div>
      )}

      {/* Thread TS (optional) */}
      {(config.action === 'send_message' || config.action === 'send_dm') && (
        <div className="space-y-2">
          <Label>Thread Timestamp (Optional)</Label>
          <Input
            placeholder="1234567890.123456"
            value={config.thread_ts}
            onChange={(e) => updateConfig('thread_ts', e.target.value)}
            className="font-mono text-sm"
          />
          <p className="text-xs text-muted-foreground">
            Reply to a specific thread
          </p>
        </div>
      )}

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
          disabled={!config.bot_token || !config.message}
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Connection
        </Button>
      )}
    </div>
  );
}
