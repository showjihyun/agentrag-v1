'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Code, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function TransformConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    input: data.input || '{{input}}',
    transform_type: data.transform_type || 'mapping',
    mappings: data.mappings || [{ source: '', target: '', transform: '' }],
    template: data.template || '',
    expression: data.expression || '',
    operations: data.operations || [],
    output_type: data.output_type || 'object',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addMapping = () => {
    updateConfig('mappings', [...config.mappings, { source: '', target: '', transform: '' }]);
  };

  const updateMapping = (index: number, field: string, value: string) => {
    const newMappings = [...config.mappings];
    newMappings[index][field] = value;
    updateConfig('mappings', newMappings);
  };

  const removeMapping = (index: number) => {
    updateConfig('mappings', config.mappings.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-violet-100 dark:bg-violet-950">
          <Code className="h-5 w-5 text-violet-600 dark:text-violet-400" />
        </div>
        <div>
          <h3 className="font-semibold">Transform</h3>
          <p className="text-sm text-muted-foreground">Transform and reshape data</p>
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <Label>Input Data</Label>
        <Input
          placeholder="{{input}} or {{previous.output}}"
          value={config.input}
          onChange={(e) => updateConfig('input', e.target.value)}
        />
      </div>

      {/* Transform Type */}
      <div className="space-y-2">
        <Label>Transform Type</Label>
        <Select value={config.transform_type} onValueChange={(v) => updateConfig('transform_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="mapping">Field Mapping</SelectItem>
            <SelectItem value="template">Template</SelectItem>
            <SelectItem value="expression">Expression</SelectItem>
            <SelectItem value="rename">Rename Fields</SelectItem>
            <SelectItem value="pick">Pick Fields</SelectItem>
            <SelectItem value="omit">Omit Fields</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Field Mapping */}
      {config.transform_type === 'mapping' && (
        <div className="space-y-3">
          <Label>Field Mappings</Label>
          {config.mappings.map((mapping: any, index: number) => (
            <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
              <div className="grid grid-cols-2 gap-2">
                <Input
                  placeholder="source.field"
                  value={mapping.source}
                  onChange={(e) => updateMapping(index, 'source', e.target.value)}
                />
                <div className="flex gap-2">
                  <Input
                    placeholder="target_field"
                    value={mapping.target}
                    onChange={(e) => updateMapping(index, 'target', e.target.value)}
                    className="flex-1"
                  />
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeMapping(index)}
                    disabled={config.mappings.length <= 1}
                  >
                    <Trash className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <Input
                placeholder="Transform expression (optional): toUpperCase(), parseInt(), etc."
                value={mapping.transform}
                onChange={(e) => updateMapping(index, 'transform', e.target.value)}
                className="text-xs"
              />
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addMapping} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            Add Mapping
          </Button>
        </div>
      )}

      {/* Template */}
      {config.transform_type === 'template' && (
        <div className="space-y-2">
          <Label>Output Template</Label>
          <Textarea
            placeholder={'{\n  "fullName": "{{input.firstName}} {{input.lastName}}",\n  "email": "{{input.email}}"\n}'}
            value={config.template}
            onChange={(e) => updateConfig('template', e.target.value)}
            rows={8}
            className="font-mono text-sm"
          />
        </div>
      )}

      {/* Expression */}
      {config.transform_type === 'expression' && (
        <div className="space-y-2">
          <Label>Transform Expression</Label>
          <Textarea
            placeholder="input.items.map(item => ({ ...item, processed: true }))"
            value={config.expression}
            onChange={(e) => updateConfig('expression', e.target.value)}
            rows={4}
            className="font-mono text-sm"
          />
          <p className="text-xs text-muted-foreground">
            JavaScript expression. Use 'input' to access input data.
          </p>
        </div>
      )}

      {/* Pick/Omit Fields */}
      {(config.transform_type === 'pick' || config.transform_type === 'omit' || config.transform_type === 'rename') && (
        <div className="space-y-2">
          <Label>
            {config.transform_type === 'pick' ? 'Fields to Keep' : 
             config.transform_type === 'omit' ? 'Fields to Remove' : 
             'Fields to Rename (old:new)'}
          </Label>
          <Input
            placeholder={config.transform_type === 'rename' ? 'oldName:newName, field2:renamed2' : 'field1, field2, nested.field'}
            value={config.expression}
            onChange={(e) => updateConfig('expression', e.target.value)}
          />
        </div>
      )}

      {/* Output Type */}
      <div className="space-y-2">
        <Label>Output Type</Label>
        <Select value={config.output_type} onValueChange={(v) => updateConfig('output_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="object">Object</SelectItem>
            <SelectItem value="array">Array</SelectItem>
            <SelectItem value="string">String</SelectItem>
            <SelectItem value="preserve">Preserve Input Type</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
