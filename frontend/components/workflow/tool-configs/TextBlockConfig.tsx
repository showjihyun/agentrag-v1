'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function TextBlockConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    content: data.content || '',
    content_type: data.content_type || 'text',
    template_engine: data.template_engine || 'simple',
    output_name: data.output_name || 'text',
    trim_whitespace: data.trim_whitespace !== false,
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
        <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-950">
          <FileText className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </div>
        <div>
          <h3 className="font-semibold">Text Block</h3>
          <p className="text-sm text-muted-foreground">Static text or template</p>
        </div>
      </div>

      {/* Content Type */}
      <div className="space-y-2">
        <Label>Content Type</Label>
        <Select value={config.content_type} onValueChange={(v) => updateConfig('content_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="text">Plain Text</SelectItem>
            <SelectItem value="json">JSON</SelectItem>
            <SelectItem value="html">HTML</SelectItem>
            <SelectItem value="markdown">Markdown</SelectItem>
            <SelectItem value="xml">XML</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Template Engine */}
      <div className="space-y-2">
        <Label>Template Engine</Label>
        <Select value={config.template_engine} onValueChange={(v) => updateConfig('template_engine', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="simple">Simple {'{{variable}}'}</SelectItem>
            <SelectItem value="jinja">Jinja2</SelectItem>
            <SelectItem value="handlebars">Handlebars</SelectItem>
            <SelectItem value="none">None (Static)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Content */}
      <div className="space-y-2">
        <Label>Content</Label>
        <Textarea
          placeholder={
            config.content_type === 'json' 
              ? '{\n  "message": "Hello {{input.name}}"\n}'
              : 'Hello {{input.name}}, welcome to our service!'
          }
          value={config.content}
          onChange={(e) => updateConfig('content', e.target.value)}
          rows={10}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Use {'{{variable}}'} syntax to include dynamic values
        </p>
      </div>

      {/* Output Name */}
      <div className="space-y-2">
        <Label>Output Variable Name</Label>
        <Input
          placeholder="text"
          value={config.output_name}
          onChange={(e) => updateConfig('output_name', e.target.value)}
        />
      </div>
    </div>
  );
}
