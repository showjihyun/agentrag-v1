'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Key, MessageSquare, Settings2 } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const OPENAI_MODELS = [
  { id: 'gpt-4-turbo-preview', name: 'GPT-4 Turbo', description: 'Most capable, best for complex tasks' },
  { id: 'gpt-4', name: 'GPT-4', description: 'High intelligence, slower' },
  { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Fast and efficient' },
];

export default function OpenAIChatConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    api_key: data.api_key || '',
    model: data.model || 'gpt-4-turbo-preview',
    prompt: data.prompt || '',
    system_message: data.system_message || 'You are a helpful assistant.',
    temperature: data.temperature || 0.7,
    max_tokens: data.max_tokens || 2000,
    stream: data.stream !== false,
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
          <Sparkles className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="font-semibold">OpenAI Chat</h3>
          <p className="text-sm text-muted-foreground">Configure GPT model and parameters</p>
        </div>
      </div>

      {/* API Key */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Key className="h-4 w-4" />
          API Key *
        </Label>
        <Input
          type="password"
          placeholder="sk-..."
          value={config.api_key}
          onChange={(e) => updateConfig('api_key', e.target.value)}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" className="text-primary hover:underline">OpenAI Platform</a>
        </p>
      </div>

      {/* Model Selection */}
      <div className="space-y-2">
        <Label>Model</Label>
        <Select value={config.model} onValueChange={(v) => updateConfig('model', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {OPENAI_MODELS.map(model => (
              <SelectItem key={model.id} value={model.id}>
                <div className="flex flex-col">
                  <span className="font-medium">{model.name}</span>
                  <span className="text-xs text-muted-foreground">{model.description}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* System Message */}
      <div className="space-y-2">
        <Label>System Message</Label>
        <Textarea
          placeholder="You are a helpful assistant..."
          value={config.system_message}
          onChange={(e) => updateConfig('system_message', e.target.value)}
          rows={3}
        />
        <p className="text-xs text-muted-foreground">
          Sets the behavior and personality of the assistant
        </p>
      </div>

      {/* Prompt Template */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          Prompt Template
        </Label>
        <Textarea
          placeholder="Use {{input}} for dynamic values..."
          value={config.prompt}
          onChange={(e) => updateConfig('prompt', e.target.value)}
          rows={4}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Use <code className="px-1 py-0.5 bg-muted rounded">{'{{variable}}'}</code> for dynamic values
        </p>
      </div>

      {/* Advanced Settings */}
      <div className="space-y-4 pt-4 border-t">
        <div className="flex items-center gap-2">
          <Settings2 className="h-4 w-4" />
          <Label className="text-base font-semibold">Advanced Settings</Label>
        </div>

        {/* Temperature */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Temperature</Label>
            <Badge variant="outline">{config.temperature}</Badge>
          </div>
          <Slider
            value={[config.temperature]}
            onValueChange={([v]) => updateConfig('temperature', v)}
            min={0}
            max={2}
            step={0.1}
            className="w-full"
          />
          <p className="text-xs text-muted-foreground">
            Higher values = more creative, Lower values = more focused
          </p>
        </div>

        {/* Max Tokens */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label>Max Tokens</Label>
            <Badge variant="outline">{config.max_tokens}</Badge>
          </div>
          <Slider
            value={[config.max_tokens]}
            onValueChange={([v]) => updateConfig('max_tokens', v)}
            min={100}
            max={4000}
            step={100}
            className="w-full"
          />
        </div>

        {/* Stream */}
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label>Stream Response</Label>
            <p className="text-xs text-muted-foreground">
              Stream tokens as they're generated
            </p>
          </div>
          <Switch
            checked={config.stream}
            onCheckedChange={(v) => updateConfig('stream', v)}
          />
        </div>
      </div>
    </div>
  );
}
