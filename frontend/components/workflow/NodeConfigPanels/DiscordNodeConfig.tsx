'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';

interface DiscordNodeConfigProps {
  data: {
    webhookUrl?: string;
    message?: string;
    username?: string;
    avatarUrl?: string;
    embedColor?: string;
    embedTitle?: string;
  };
  onChange: (data: any) => void;
}

export default function DiscordNodeConfig({ data, onChange }: DiscordNodeConfigProps) {
  const [webhookUrl, setWebhookUrl] = useState(data.webhookUrl || '');
  const [message, setMessage] = useState(data.message || '');
  const [username, setUsername] = useState(data.username || 'Workflow Bot');
  const [avatarUrl, setAvatarUrl] = useState(data.avatarUrl || '');
  const [embedColor, setEmbedColor] = useState(data.embedColor || '#5865F2');
  const [embedTitle, setEmbedTitle] = useState(data.embedTitle || '');

  const handleWebhookUrlChange = (value: string) => {
    setWebhookUrl(value);
    onChange({ ...data, webhookUrl: value });
  };

  const handleMessageChange = (value: string) => {
    setMessage(value);
    onChange({ ...data, message: value });
  };

  const handleUsernameChange = (value: string) => {
    setUsername(value);
    onChange({ ...data, username: value });
  };

  const handleAvatarUrlChange = (value: string) => {
    setAvatarUrl(value);
    onChange({ ...data, avatarUrl: value });
  };

  const handleEmbedColorChange = (value: string) => {
    setEmbedColor(value);
    onChange({ ...data, embedColor: value });
  };

  const handleEmbedTitleChange = (value: string) => {
    setEmbedTitle(value);
    onChange({ ...data, embedTitle: value });
  };

  const MESSAGE_TEMPLATES = [
    {
      name: 'Simple',
      template: '✅ Workflow completed successfully!',
    },
    {
      name: 'With Data',
      template: '**Result:** {{$json.result}}\\n**Status:** {{$json.status}}',
    },
    {
      name: 'Error',
      template: '🚨 **Error Alert**\\nWorkflow failed: {{$json.error}}',
    },
    {
      name: 'Detailed',
      template: '**Workflow Execution**\\n━━━━━━━━━━━━━━━\\n📊 Status: {{$json.status}}\\n⏱️ Duration: {{$json.duration}}s\\n📝 Result: {{$json.result}}',
    },
  ];

  const EMBED_COLORS = [
    { name: 'Discord Blue', value: '#5865F2' },
    { name: 'Success Green', value: '#57F287' },
    { name: 'Warning Yellow', value: '#FEE75C' },
    { name: 'Error Red', value: '#ED4245' },
    { name: 'Info Blue', value: '#3498DB' },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
        <p className="text-xs text-indigo-800 mb-2">
          <strong>Setup Required:</strong>
        </p>
        <ol className="text-xs text-indigo-700 space-y-1 ml-4 list-decimal">
          <li>Go to your Discord server settings</li>
          <li>Navigate to Integrations → Webhooks</li>
          <li>Click "New Webhook"</li>
          <li>Choose a channel and copy the webhook URL</li>
          <li>Paste the URL below</li>
        </ol>
        <Button
          variant="link"
          size="sm"
          className="text-indigo-600 p-0 h-auto mt-2"
          onClick={() => window.open('https://discord.com/developers/docs/resources/webhook', '_blank')}
        >
          <ExternalLink className="w-3 h-3 mr-1" />
          Discord Webhook Docs
        </Button>
      </div>

      <div>
        <Label>Webhook URL</Label>
        <Input
          type="password"
          value={webhookUrl}
          onChange={(e) => handleWebhookUrlChange(e.target.value)}
          placeholder="https://discord.com/api/webhooks/..."
          className="font-mono text-sm"
        />
        <p className="text-xs text-gray-500 mt-1">
          Keep this URL secret - it allows posting to your channel
        </p>
      </div>

      <div>
        <Label>Message Content</Label>
        <textarea
          value={message}
          onChange={(e) => handleMessageChange(e.target.value)}
          className="w-full h-32 p-3 border rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter your message..."
        />
        <p className="text-xs text-gray-500 mt-1">
          Use {'{'}$json.field{'}'} to reference data
        </p>
      </div>

      <div>
        <Label>Message Templates</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {MESSAGE_TEMPLATES.map((template) => (
            <Button
              key={template.name}
              onClick={() => handleMessageChange(template.template)}
              variant="outline"
              size="sm"
              className="text-xs justify-start h-auto py-2"
            >
              {template.name}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label>Bot Username</Label>
          <Input
            value={username}
            onChange={(e) => handleUsernameChange(e.target.value)}
            placeholder="Workflow Bot"
          />
        </div>

        <div>
          <Label>Avatar URL (optional)</Label>
          <Input
            value={avatarUrl}
            onChange={(e) => handleAvatarUrlChange(e.target.value)}
            placeholder="https://..."
          />
        </div>
      </div>

      <div>
        <Label>Embed Title (optional)</Label>
        <Input
          value={embedTitle}
          onChange={(e) => handleEmbedTitleChange(e.target.value)}
          placeholder="Workflow Notification"
        />
        <p className="text-xs text-gray-500 mt-1">
          Creates a rich embed with this title
        </p>
      </div>

      <div>
        <Label>Embed Color</Label>
        <div className="flex gap-2 mt-2">
          <Input
            type="color"
            value={embedColor}
            onChange={(e) => handleEmbedColorChange(e.target.value)}
            className="w-16 h-10"
          />
          <Input
            value={embedColor}
            onChange={(e) => handleEmbedColorChange(e.target.value)}
            placeholder="#5865F2"
            className="flex-1 font-mono"
          />
        </div>
        <div className="flex gap-1 mt-2 flex-wrap">
          {EMBED_COLORS.map((color) => (
            <button
              key={color.value}
              onClick={() => handleEmbedColorChange(color.value)}
              className="px-2 py-1 text-xs rounded border hover:bg-gray-50"
              style={{ borderColor: color.value }}
            >
              {color.name}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-2">
          Discord Markdown Support:
        </p>
        <div className="text-xs text-blue-700 space-y-1 font-mono">
          <div>**bold** - Bold text</div>
          <div>*italic* - Italic text</div>
          <div>__underline__ - Underline</div>
          <div>~~strike~~ - Strikethrough</div>
          <div>`code` - Inline code</div>
          <div>```code block``` - Code block</div>
        </div>
      </div>
    </div>
  );
}
