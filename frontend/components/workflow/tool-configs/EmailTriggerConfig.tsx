'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Mail, Filter, Clock } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function EmailTriggerConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    provider: data.provider || 'gmail',
    credentials: data.credentials || '',
    poll_interval: data.poll_interval || 60,
    // Filters
    from_filter: data.from_filter || '',
    to_filter: data.to_filter || '',
    subject_filter: data.subject_filter || '',
    label_filter: data.label_filter || 'INBOX',
    has_attachment: data.has_attachment || false,
    // Options
    mark_as_read: data.mark_as_read || true,
    include_body: data.include_body || true,
    include_attachments: data.include_attachments || false,
    max_attachments_size: data.max_attachments_size || 10,
    only_unread: data.only_unread !== false,
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
        <div className="p-2 rounded-lg bg-red-100 dark:bg-red-950">
          <Mail className="h-5 w-5 text-red-600 dark:text-red-400" />
        </div>
        <div>
          <h3 className="font-semibold">Email Trigger</h3>
          <p className="text-sm text-muted-foreground">Trigger on incoming emails</p>
        </div>
      </div>

      {/* Provider */}
      <div className="space-y-2">
        <Label>Email Provider</Label>
        <Select value={config.provider} onValueChange={(v) => updateConfig('provider', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="gmail">Gmail</SelectItem>
            <SelectItem value="outlook">Outlook / Office 365</SelectItem>
            <SelectItem value="imap">IMAP (Custom)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Credentials */}
      <div className="space-y-2">
        <Label>Credentials</Label>
        <Input
          type="password"
          placeholder="OAuth token or App Password"
          value={config.credentials}
          onChange={(e) => updateConfig('credentials', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Use environment variable: {'{{env.EMAIL_CREDENTIALS}}'}
        </p>
      </div>

      {/* Poll Interval */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Poll Interval (seconds)
        </Label>
        <Input
          type="number"
          min="10"
          value={config.poll_interval}
          onChange={(e) => updateConfig('poll_interval', parseInt(e.target.value) || 60)}
        />
        <p className="text-xs text-muted-foreground">
          How often to check for new emails (minimum 10 seconds)
        </p>
      </div>

      {/* Filters Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <Label className="text-base font-semibold">Email Filters</Label>
        </div>

        <div className="space-y-2">
          <Label>From Address</Label>
          <Input
            placeholder="sender@example.com or *@company.com"
            value={config.from_filter}
            onChange={(e) => updateConfig('from_filter', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Filter by sender (supports wildcards)
          </p>
        </div>

        <div className="space-y-2">
          <Label>To Address</Label>
          <Input
            placeholder="recipient@example.com"
            value={config.to_filter}
            onChange={(e) => updateConfig('to_filter', e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <Label>Subject Contains</Label>
          <Input
            placeholder="[URGENT], Invoice, Support"
            value={config.subject_filter}
            onChange={(e) => updateConfig('subject_filter', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Comma-separated keywords to match in subject
          </p>
        </div>

        <div className="space-y-2">
          <Label>Label / Folder</Label>
          <Select value={config.label_filter} onValueChange={(v) => updateConfig('label_filter', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="INBOX">Inbox</SelectItem>
              <SelectItem value="STARRED">Starred</SelectItem>
              <SelectItem value="IMPORTANT">Important</SelectItem>
              <SelectItem value="CATEGORY_PERSONAL">Personal</SelectItem>
              <SelectItem value="CATEGORY_SOCIAL">Social</SelectItem>
              <SelectItem value="CATEGORY_PROMOTIONS">Promotions</SelectItem>
              <SelectItem value="CATEGORY_UPDATES">Updates</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Has Attachment</Label>
            <p className="text-xs text-muted-foreground">Only emails with attachments</p>
          </div>
          <Switch
            checked={config.has_attachment}
            onCheckedChange={(checked) => updateConfig('has_attachment', checked)}
          />
        </div>
      </div>

      {/* Options Section */}
      <div className="space-y-4 pt-4 border-t">
        <Label className="text-base font-semibold">Options</Label>

        <div className="flex items-center justify-between">
          <div>
            <Label>Only Unread</Label>
            <p className="text-xs text-muted-foreground">Only trigger on unread emails</p>
          </div>
          <Switch
            checked={config.only_unread}
            onCheckedChange={(checked) => updateConfig('only_unread', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Mark as Read</Label>
            <p className="text-xs text-muted-foreground">Mark email as read after processing</p>
          </div>
          <Switch
            checked={config.mark_as_read}
            onCheckedChange={(checked) => updateConfig('mark_as_read', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Include Body</Label>
            <p className="text-xs text-muted-foreground">Include email body in trigger data</p>
          </div>
          <Switch
            checked={config.include_body}
            onCheckedChange={(checked) => updateConfig('include_body', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Include Attachments</Label>
            <p className="text-xs text-muted-foreground">Download and include attachments</p>
          </div>
          <Switch
            checked={config.include_attachments}
            onCheckedChange={(checked) => updateConfig('include_attachments', checked)}
          />
        </div>

        {config.include_attachments && (
          <div className="space-y-2">
            <Label>Max Attachment Size (MB)</Label>
            <Input
              type="number"
              min="1"
              max="50"
              value={config.max_attachments_size}
              onChange={(e) => updateConfig('max_attachments_size', parseInt(e.target.value) || 10)}
            />
          </div>
        )}
      </div>

      {/* Output Schema */}
      <div className="p-3 bg-muted rounded-lg space-y-2">
        <p className="text-xs font-medium">Available Output Variables:</p>
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div><Badge variant="outline">{'{{email.from}}'}</Badge></div>
          <div><Badge variant="outline">{'{{email.to}}'}</Badge></div>
          <div><Badge variant="outline">{'{{email.subject}}'}</Badge></div>
          <div><Badge variant="outline">{'{{email.body}}'}</Badge></div>
          <div><Badge variant="outline">{'{{email.date}}'}</Badge></div>
          <div><Badge variant="outline">{'{{email.attachments}}'}</Badge></div>
        </div>
      </div>
    </div>
  );
}
