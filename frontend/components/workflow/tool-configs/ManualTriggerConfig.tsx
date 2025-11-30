'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { Zap, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function ManualTriggerConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    name: data.name || 'Manual Trigger',
    description: data.description || '',
    input_schema: data.input_schema || [],
    require_confirmation: data.require_confirmation || false,
    confirmation_message: data.confirmation_message || 'Are you sure you want to run this workflow?',
    allowed_users: data.allowed_users || '',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addInputField = () => {
    updateConfig('input_schema', [
      ...config.input_schema,
      { name: '', type: 'string', required: false, default: '' }
    ]);
  };

  const updateInputField = (index: number, field: string, value: any) => {
    const newSchema = [...config.input_schema];
    newSchema[index][field] = value;
    updateConfig('input_schema', newSchema);
  };

  const removeInputField = (index: number) => {
    updateConfig('input_schema', config.input_schema.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-yellow-100 dark:bg-yellow-950">
          <Zap className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
        </div>
        <div>
          <h3 className="font-semibold">Manual Trigger</h3>
          <p className="text-sm text-muted-foreground">Manually start workflow execution</p>
        </div>
      </div>

      {/* Name & Description */}
      <div className="space-y-2">
        <Label>Trigger Name</Label>
        <Input
          value={config.name}
          onChange={(e) => updateConfig('name', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label>Description</Label>
        <Textarea
          placeholder="Describe when to use this trigger..."
          value={config.description}
          onChange={(e) => updateConfig('description', e.target.value)}
          rows={2}
        />
      </div>

      {/* Input Schema */}
      <div className="space-y-3">
        <Label>Input Fields</Label>
        <p className="text-xs text-muted-foreground">
          Define input fields that users must fill when triggering
        </p>
        {config.input_schema.map((field: any, index: number) => (
          <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="Field name"
                value={field.name}
                onChange={(e) => updateInputField(index, 'name', e.target.value)}
                className="flex-1"
              />
              <select
                value={field.type}
                onChange={(e) => updateInputField(index, 'type', e.target.value)}
                className="px-3 py-2 border rounded-md bg-background"
              >
                <option value="string">Text</option>
                <option value="number">Number</option>
                <option value="boolean">Boolean</option>
                <option value="file">File</option>
                <option value="json">JSON</option>
              </select>
              <Button variant="ghost" size="icon" onClick={() => removeInputField(index)}>
                <Trash className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex gap-2 items-center">
              <Input
                placeholder="Default value"
                value={field.default}
                onChange={(e) => updateInputField(index, 'default', e.target.value)}
                className="flex-1"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={field.required}
                  onChange={(e) => updateInputField(index, 'required', e.target.checked)}
                />
                Required
              </label>
            </div>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addInputField} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Input Field
        </Button>
      </div>

      {/* Confirmation */}
      <div className="flex items-center justify-between">
        <div>
          <Label>Require Confirmation</Label>
          <p className="text-xs text-muted-foreground">Ask for confirmation before running</p>
        </div>
        <Switch
          checked={config.require_confirmation}
          onCheckedChange={(checked) => updateConfig('require_confirmation', checked)}
        />
      </div>

      {config.require_confirmation && (
        <div className="space-y-2">
          <Label>Confirmation Message</Label>
          <Input
            value={config.confirmation_message}
            onChange={(e) => updateConfig('confirmation_message', e.target.value)}
          />
        </div>
      )}

      {/* Access Control */}
      <div className="space-y-2">
        <Label>Allowed Users (optional)</Label>
        <Input
          placeholder="user1@example.com, user2@example.com"
          value={config.allowed_users}
          onChange={(e) => updateConfig('allowed_users', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Leave empty to allow all users
        </p>
      </div>
    </div>
  );
}
