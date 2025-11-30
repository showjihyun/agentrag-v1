'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Mail, TestTube, Key, Plus, Trash, Paperclip } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

interface SendGridConfig {
  apiKey: string;
  from: string;
  fromName: string;
  to: string;
  cc: string;
  bcc: string;
  subject: string;
  contentType: string;
  body: string;
  templateId: string;
  dynamicTemplateData: string;
  attachments: Array<{ filename: string; content: string; type: string }>;
  replyTo: string;
  categories: string;
  sendAt: string;
  trackOpens: boolean;
  trackClicks: boolean;
}

export default function SendGridConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState<SendGridConfig>({
    apiKey: data.apiKey || data.api_key || '',
    from: data.from || '',
    fromName: data.fromName || data.from_name || '',
    to: data.to || '',
    cc: data.cc || '',
    bcc: data.bcc || '',
    subject: data.subject || '',
    contentType: data.contentType || data.content_type || 'text/plain',
    body: data.body || '',
    templateId: data.templateId || data.template_id || '',
    dynamicTemplateData: data.dynamicTemplateData || data.dynamic_template_data || '{}',
    attachments: data.attachments || [],
    replyTo: data.replyTo || data.reply_to || '',
    categories: data.categories || '',
    sendAt: data.sendAt || data.send_at || '',
    trackOpens: data.trackOpens ?? data.track_opens ?? true,
    trackClicks: data.trackClicks ?? data.track_clicks ?? true,
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: keyof SendGridConfig, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const addAttachment = () => {
    updateConfig('attachments', [
      ...config.attachments,
      { filename: '', content: '', type: 'application/octet-stream' }
    ]);
  };

  const updateAttachment = (index: number, field: string, value: string) => {
    const newAttachments = [...config.attachments];
    newAttachments[index] = { ...newAttachments[index], [field]: value };
    updateConfig('attachments', newAttachments);
  };

  const removeAttachment = (index: number) => {
    updateConfig('attachments', config.attachments.filter((_, i) => i !== index));
  };

  const useTemplate = !!config.templateId;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950">
          <Mail className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold">SendGrid</h3>
          <p className="text-sm text-muted-foreground">Send transactional emails</p>
        </div>
        <Badge variant="secondary" className="ml-auto">Email</Badge>
      </div>

      {/* API Key */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Key className="h-4 w-4" />
          API Key
        </Label>
        <Input
          type="password"
          placeholder="SG.xxxxxxxx"
          value={config.apiKey}
          onChange={(e) => updateConfig('apiKey', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Or use {'{{env.SENDGRID_API_KEY}}'}
        </p>
      </div>

      <Tabs defaultValue="message" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="message">Message</TabsTrigger>
          <TabsTrigger value="recipients">Recipients</TabsTrigger>
          <TabsTrigger value="template">Template</TabsTrigger>
          <TabsTrigger value="options">Options</TabsTrigger>
        </TabsList>

        {/* Message Tab */}
        <TabsContent value="message" className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>From Email</Label>
              <Input
                type="email"
                placeholder="sender@example.com"
                value={config.from}
                onChange={(e) => updateConfig('from', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>From Name</Label>
              <Input
                placeholder="Sender Name"
                value={config.fromName}
                onChange={(e) => updateConfig('fromName', e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Subject</Label>
            <Input
              placeholder="Email subject or {{variable}}"
              value={config.subject}
              onChange={(e) => updateConfig('subject', e.target.value)}
            />
          </div>

          {!useTemplate && (
            <>
              <div className="space-y-2">
                <Label>Content Type</Label>
                <Select value={config.contentType} onValueChange={(v) => updateConfig('contentType', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text/plain">Plain Text</SelectItem>
                    <SelectItem value="text/html">HTML</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Body</Label>
                <Textarea
                  placeholder={config.contentType === 'text/html' 
                    ? '<html><body>Your HTML content</body></html>'
                    : 'Your email content...'}
                  value={config.body}
                  onChange={(e) => updateConfig('body', e.target.value)}
                  rows={8}
                  className={config.contentType === 'text/html' ? 'font-mono text-sm' : ''}
                />
              </div>
            </>
          )}

          {useTemplate && (
            <p className="text-sm text-muted-foreground bg-muted p-3 rounded">
              Using template. Configure template data in the Template tab.
            </p>
          )}
        </TabsContent>

        {/* Recipients Tab */}
        <TabsContent value="recipients" className="space-y-4">
          <div className="space-y-2">
            <Label>To (comma-separated)</Label>
            <Textarea
              placeholder="recipient1@example.com, recipient2@example.com"
              value={config.to}
              onChange={(e) => updateConfig('to', e.target.value)}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label>CC (optional)</Label>
            <Input
              placeholder="cc@example.com"
              value={config.cc}
              onChange={(e) => updateConfig('cc', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>BCC (optional)</Label>
            <Input
              placeholder="bcc@example.com"
              value={config.bcc}
              onChange={(e) => updateConfig('bcc', e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Reply-To (optional)</Label>
            <Input
              placeholder="reply@example.com"
              value={config.replyTo}
              onChange={(e) => updateConfig('replyTo', e.target.value)}
            />
          </div>

          {/* Attachments */}
          <div className="space-y-3">
            <Label className="flex items-center gap-2">
              <Paperclip className="h-4 w-4" />
              Attachments
            </Label>
            
            {config.attachments.map((attachment, index) => (
              <div key={index} className="flex gap-2 p-3 bg-muted/50 rounded-lg">
                <Input
                  placeholder="filename.pdf"
                  value={attachment.filename}
                  onChange={(e) => updateAttachment(index, 'filename', e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Base64 content or {{variable}}"
                  value={attachment.content}
                  onChange={(e) => updateAttachment(index, 'content', e.target.value)}
                  className="flex-1"
                />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => removeAttachment(index)}
                >
                  <Trash className="h-4 w-4" />
                </Button>
              </div>
            ))}

            <Button
              variant="outline"
              size="sm"
              onClick={addAttachment}
              className="w-full"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Attachment
            </Button>
          </div>
        </TabsContent>

        {/* Template Tab */}
        <TabsContent value="template" className="space-y-4">
          <div className="space-y-2">
            <Label>Template ID (optional)</Label>
            <Input
              placeholder="d-xxxxxxxxxxxxxxxx"
              value={config.templateId}
              onChange={(e) => updateConfig('templateId', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Use a SendGrid Dynamic Template instead of custom content
            </p>
          </div>

          {useTemplate && (
            <div className="space-y-2">
              <Label>Dynamic Template Data (JSON)</Label>
              <Textarea
                placeholder={'{\n  "name": "John",\n  "order_id": "12345"\n}'}
                value={config.dynamicTemplateData}
                onChange={(e) => updateConfig('dynamicTemplateData', e.target.value)}
                rows={8}
                className="font-mono text-sm"
              />
              <p className="text-xs text-muted-foreground">
                Variables to pass to your template
              </p>
            </div>
          )}

          {!useTemplate && (
            <p className="text-sm text-muted-foreground text-center py-8">
              Enter a Template ID to use SendGrid Dynamic Templates
            </p>
          )}
        </TabsContent>

        {/* Options Tab */}
        <TabsContent value="options" className="space-y-4">
          <div className="space-y-2">
            <Label>Categories (comma-separated)</Label>
            <Input
              placeholder="marketing, newsletter"
              value={config.categories}
              onChange={(e) => updateConfig('categories', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              For analytics and filtering in SendGrid
            </p>
          </div>

          <div className="space-y-2">
            <Label>Schedule Send (optional)</Label>
            <Input
              type="datetime-local"
              value={config.sendAt}
              onChange={(e) => updateConfig('sendAt', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Leave empty to send immediately
            </p>
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label>Track Opens</Label>
              <p className="text-xs text-muted-foreground">Track when recipients open the email</p>
            </div>
            <Switch
              checked={config.trackOpens}
              onCheckedChange={(v) => updateConfig('trackOpens', v)}
            />
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <Label>Track Clicks</Label>
              <p className="text-xs text-muted-foreground">Track when recipients click links</p>
            </div>
            <Switch
              checked={config.trackClicks}
              onCheckedChange={(v) => updateConfig('trackClicks', v)}
            />
          </div>
        </TabsContent>
      </Tabs>

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
          disabled={!config.apiKey || !config.from || !config.to}
        >
          <TestTube className="h-4 w-4 mr-2" />
          Send Test Email
        </Button>
      )}
    </div>
  );
}
