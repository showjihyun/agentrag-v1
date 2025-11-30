'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Mail, Key, TestTube } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const GMAIL_ACTIONS = [
  { id: 'send_email', name: 'Send Email', description: 'Send an email' },
  { id: 'search_emails', name: 'Search Emails', description: 'Search for emails' },
  { id: 'get_email', name: 'Get Email', description: 'Get a specific email' },
];

export default function GmailConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    action: data.action || 'send_email',
    to: data.to || '',
    cc: data.cc || '',
    bcc: data.bcc || '',
    subject: data.subject || '',
    body: data.body || '',
    body_type: data.body_type || 'html',
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
        <div className="p-2 rounded-lg bg-red-100 dark:bg-red-950">
          <Mail className="h-5 w-5 text-red-600 dark:text-red-400" />
        </div>
        <div>
          <h3 className="font-semibold">Gmail</h3>
          <p className="text-sm text-muted-foreground">Send and manage emails</p>
        </div>
        <Badge variant="secondary" className="ml-auto">New</Badge>
      </div>

      {/* Action */}
      <div className="space-y-2">
        <Label>Action</Label>
        <Select value={config.action} onValueChange={(v) => updateConfig('action', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {GMAIL_ACTIONS.map(action => (
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

      {config.action === 'send_email' && (
        <>
          {/* To */}
          <div className="space-y-2">
            <Label>To *</Label>
            <Input
              placeholder="recipient@example.com"
              value={config.to}
              onChange={(e) => updateConfig('to', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Comma-separated for multiple recipients
            </p>
          </div>

          {/* CC */}
          <div className="space-y-2">
            <Label>CC (Optional)</Label>
            <Input
              placeholder="cc@example.com"
              value={config.cc}
              onChange={(e) => updateConfig('cc', e.target.value)}
            />
          </div>

          {/* BCC */}
          <div className="space-y-2">
            <Label>BCC (Optional)</Label>
            <Input
              placeholder="bcc@example.com"
              value={config.bcc}
              onChange={(e) => updateConfig('bcc', e.target.value)}
            />
          </div>

          {/* Subject */}
          <div className="space-y-2">
            <Label>Subject *</Label>
            <Input
              placeholder="Email subject..."
              value={config.subject}
              onChange={(e) => updateConfig('subject', e.target.value)}
            />
          </div>

          {/* Body Type */}
          <div className="space-y-2">
            <Label>Body Type</Label>
            <Select value={config.body_type} onValueChange={(v) => updateConfig('body_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="html">HTML</SelectItem>
                <SelectItem value="plain">Plain Text</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Body */}
          <div className="space-y-2">
            <Label>Body *</Label>
            <Textarea
              placeholder={config.body_type === 'html' ? '<p>Email content...</p>' : 'Email content...'}
              value={config.body}
              onChange={(e) => updateConfig('body', e.target.value)}
              rows={8}
            />
            <p className="text-xs text-muted-foreground">
              Use <code className="px-1 py-0.5 bg-muted rounded">{'{{variables}}'}</code> for dynamic content
            </p>
          </div>
        </>
      )}

      {/* Test Button */}
      {onTest && config.action === 'send_email' && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
          disabled={!config.to || !config.subject || !config.body}
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Email
        </Button>
      )}
    </div>
  );
}
