'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Bot } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const PROVIDERS = [
  { value: 'ollama', label: 'Ollama (Local)' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic (Claude)' },
  { value: 'google', label: 'Google (Gemini)' },
];

export default function AIBlockConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    provider: data.provider || 'ollama',
    model: data.model || 'llama3.1:8b',
    system_prompt: data.system_prompt || '',
    user_prompt: data.user_prompt || '{{input}}',
    temperature: data.temperature || 0.7,
    max_tokens: data.max_tokens || 2000,
    response_format: data.response_format || 'text',
    json_schema: data.json_schema || '',
    stream: data.stream || false,
    api_key: data.api_key || '',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const getModelsForProvider = (provider: string) => {
    switch (provider) {
      case 'ollama':
        return ['llama3.1:8b', 'llama3.1:70b', 'mistral', 'codellama', 'phi3'];
      case 'openai':
        return ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'];
      case 'anthropic':
        return ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'];
      case 'google':
        return ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'];
      default:
        return [];
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-950 dark:to-pink-950">
          <Bot className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="font-semibold">AI Processing</h3>
          <p className="text-sm text-muted-foreground">LLM-powered data processing</p>
        </div>
      </div>

      {/* Provider */}
      <div className="space-y-2">
        <Label>Provider</Label>
        <Select value={config.provider} onValueChange={(v) => {
          updateConfig('provider', v);
          updateConfig('model', getModelsForProvider(v)[0]);
        }}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {PROVIDERS.map(p => (
              <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Model */}
      <div className="space-y-2">
        <Label>Model</Label>
        <Select value={config.model} onValueChange={(v) => updateConfig('model', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {getModelsForProvider(config.provider).map(m => (
              <SelectItem key={m} value={m}>{m}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* API Key (for non-Ollama) */}
      {config.provider !== 'ollama' && (
        <div className="space-y-2">
          <Label>API Key</Label>
          <Input
            type="password"
            placeholder="sk-... or {{env.OPENAI_API_KEY}}"
            value={config.api_key}
            onChange={(e) => updateConfig('api_key', e.target.value)}
          />
        </div>
      )}

      {/* System Prompt */}
      <div className="space-y-2">
        <Label>System Prompt</Label>
        <Textarea
          placeholder="You are a helpful assistant that..."
          value={config.system_prompt}
          onChange={(e) => updateConfig('system_prompt', e.target.value)}
          rows={3}
        />
      </div>

      {/* User Prompt */}
      <div className="space-y-2">
        <Label>User Prompt</Label>
        <Textarea
          placeholder="Process the following data: {{input}}"
          value={config.user_prompt}
          onChange={(e) => updateConfig('user_prompt', e.target.value)}
          rows={4}
        />
        <p className="text-xs text-muted-foreground">
          Use {'{{input}}'} to include data from previous node
        </p>
      </div>

      {/* Temperature */}
      <div className="space-y-2">
        <div className="flex justify-between">
          <Label>Temperature</Label>
          <span className="text-sm text-muted-foreground">{config.temperature}</span>
        </div>
        <input
          type="range"
          min="0"
          max="2"
          step="0.1"
          value={config.temperature}
          onChange={(e) => updateConfig('temperature', parseFloat(e.target.value))}
          className="w-full"
        />
      </div>

      {/* Max Tokens */}
      <div className="space-y-2">
        <Label>Max Tokens</Label>
        <Input
          type="number"
          min="1"
          max="8192"
          value={config.max_tokens}
          onChange={(e) => updateConfig('max_tokens', parseInt(e.target.value) || 2000)}
        />
      </div>

      {/* Response Format */}
      <div className="space-y-2">
        <Label>Response Format</Label>
        <Select value={config.response_format} onValueChange={(v) => updateConfig('response_format', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="text">Text</SelectItem>
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="json_schema">JSON with Schema</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* JSON Schema */}
      {config.response_format === 'json_schema' && (
        <div className="space-y-2">
          <Label>JSON Schema</Label>
          <Textarea
            placeholder={'{\n  "type": "object",\n  "properties": {...}\n}'}
            value={config.json_schema}
            onChange={(e) => updateConfig('json_schema', e.target.value)}
            rows={5}
            className="font-mono text-sm"
          />
        </div>
      )}

      {/* Stream */}
      <div className="flex items-center justify-between">
        <div>
          <Label>Stream Response</Label>
          <p className="text-xs text-muted-foreground">Stream tokens as they're generated</p>
        </div>
        <Switch
          checked={config.stream}
          onCheckedChange={(checked) => updateConfig('stream', checked)}
        />
      </div>
    </div>
  );
}
