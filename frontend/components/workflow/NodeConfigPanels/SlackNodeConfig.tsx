'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ExternalLink } from 'lucide-react';

interface SlackNodeConfigProps {
  data: {
    channel?: string;
    message?: string;
    username?: string;
    iconEmoji?: string;
    attachments?: boolean;
  };
  onChange: (data: any) => void;
}

export default function SlackNodeConfig({ data, onChange }: SlackNodeConfigProps) {
  const [channel, setChannel] = useState(data.channel || '');
  const [message, setMessage] = useState(data.message || '');
  const [username, setUsername] = useState(data.username || 'Workflow Bot');
  const [iconEmoji, setIconEmoji] = useState(data.iconEmoji || ':robot_face:');
  const [attachments, setAttachments] = useState(data.attachments !== false);

  const handleChannelChange = (value: string) => {
    setChannel(value);
    onChange({ ...data, channel: value });
  };

  const handleMessageChange = (value: string) => {
    setMessage(value);
    onChange({ ...data, message: value });
  };

  const handleUsernameChange = (value: string) => {
    setUsername(value);
    onChange({ ...data, username: value });
  };

  const handleIconEmojiChange = (value: string) => {
    setIconEmoji(value);
    onChange({ ...data, iconEmoji: value });
  };

  const handleAttachmentsChange = (value: boolean) => {
    setAttachments(value);
    onChange({ ...data, attachments: value });
  };

  const MESSAGE_TEMPLATES = [
    {
      name: 'Simple Message',
      template: 'Workflow completed successfully!',
    },
    {
      name: 'With Data',
      template: 'Result: {{$json.result}}\\nStatus: {{$json.status}}',
    },
    {
      name: 'Error Alert',
      template: '🚨 Error occurred: {{$json.error}}\\nWorkflow: {{$workflow.name}}',
    },
    {
      name: 'Rich Format',
      template: '*Workflow Execution*\\n• Status: {{$json.status}}\\n• Duration: {{$json.duration}}s\\n• Result: {{$json.result}}',
    },
  ];

  return (
    <div className="space-y-4">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <p className="text-xs text-purple-800 mb-2">
          <strong>Setup Required:</strong>
        </p>
        <ol className="text-xs text-purple-700 space-y-1 ml-4 list-decimal">
          <li>Create a Slack App at api.slack.com</li>
          <li>Add Bot Token Scopes: chat:write, chat:write.public</li>
          <li>Install app to your workspace</li>
          <li>Copy Bot User OAuth Token</li>
          <li>Add token to API Keys settings</li>
        </ol>
        <Button
          variant="link"
          size="sm"
          className="text-purple-600 p-0 h-auto mt-2"
          onClick={() => window.open('https://api.slack.com/apps', '_blank')}
        >
          <ExternalLink className="w-3 h-3 mr-1" />
          Open Slack API
        </Button>
      </div>

      <div>
        <Label>Channel</Label>
        <Input
          value={channel}
          onChange={(e) => handleChannelChange(e.target.value)}
          placeholder="general"
          className="font-mono"
        />
        <p className="text-xs text-gray-500 mt-1">
          Channel name without # (e.g., "general", "alerts")
        </p>
      </div>

      <div>
        <Label>Message</Label>
        <textarea
          value={message}
          onChange={(e) => handleMessageChange(e.target.value)}
          className="w-full h-32 p-3 border rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter your message..."
        />
        <p className="text-xs text-gray-500 mt-1">
          Use {'{{$json.field}}'} to reference data
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
          <Label>Icon Emoji</Label>
          <Input
            value={iconEmoji}
            onChange={(e) => handleIconEmojiChange(e.target.value)}
            placeholder=":robot_face:"
            className="font-mono"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="attachments"
          checked={attachments}
          onChange={(e) => handleAttachmentsChange(e.target.checked)}
          className="rounded"
        />
        <Label htmlFor="attachments" className="cursor-pointer">
          Include rich attachments (colors, fields)
        </Label>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800 font-medium mb-2">
          Slack Markdown Support:
        </p>
        <div className="text-xs text-blue-700 space-y-1 font-mono">
          <div>*bold* - Bold text</div>
          <div>_italic_ - Italic text</div>
          <div>~strike~ - Strikethrough</div>
          <div>`code` - Inline code</div>
          <div>&gt; quote - Block quote</div>
        </div>
      </div>
    </div>
  );
}
