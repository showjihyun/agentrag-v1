'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Code, TestTube, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const TRANSFORM_TYPES = [
  { value: 'jmespath', label: 'JMESPath Query' },
  { value: 'jsonpath', label: 'JSONPath Query' },
  { value: 'mapping', label: 'Field Mapping' },
  { value: 'template', label: 'Template' },
  { value: 'filter', label: 'Filter' },
  { value: 'flatten', label: 'Flatten' },
  { value: 'group', label: 'Group By' },
];

export default function JSONTransformConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    transform_type: data.transform_type || 'mapping',
    input: data.input || '{{input}}',
    query: data.query || '',
    mappings: data.mappings || [{ source: '', target: '' }],
    template: data.template || '',
    filter_expression: data.filter_expression || '',
    group_by_field: data.group_by_field || '',
    output_format: data.output_format || 'object',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addMapping = () => {
    updateConfig('mappings', [...config.mappings, { source: '', target: '' }]);
  };

  const updateMapping = (index: number, field: 'source' | 'target', value: string) => {
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
        <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-950">
          <Code className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div>
          <h3 className="font-semibold">JSON Transform</h3>
          <p className="text-sm text-muted-foreground">Transform and manipulate JSON data</p>
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <Label>Input Data</Label>
        <Input
          placeholder="{{input}} or {{previous_node.output}}"
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
            {TRANSFORM_TYPES.map(t => (
              <SelectItem key={t.value} value={t.value}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* JMESPath / JSONPath Query */}
      {(config.transform_type === 'jmespath' || config.transform_type === 'jsonpath') && (
        <div className="space-y-2">
          <Label>{config.transform_type === 'jmespath' ? 'JMESPath' : 'JSONPath'} Query</Label>
          <Textarea
            placeholder={config.transform_type === 'jmespath' ? 'data.items[*].name' : '$.data.items[*].name'}
            value={config.query}
            onChange={(e) => updateConfig('query', e.target.value)}
            rows={3}
            className="font-mono text-sm"
          />
          <p className="text-xs text-muted-foreground">
            {config.transform_type === 'jmespath' 
              ? 'Use JMESPath syntax to query JSON' 
              : 'Use JSONPath syntax to query JSON'}
          </p>
        </div>
      )}

      {/* Field Mapping */}
      {config.transform_type === 'mapping' && (
        <div className="space-y-3">
          <Label>Field Mappings</Label>
          {config.mappings.map((mapping: any, index: number) => (
            <div key={index} className="flex gap-2 items-center">
              <Input
                placeholder="source.field"
                value={mapping.source}
                onChange={(e) => updateMapping(index, 'source', e.target.value)}
                className="flex-1"
              />
              <span className="text-muted-foreground">→</span>
              <Input
                placeholder="target_field"
                value={mapping.target}
                onChange={(e) => updateMapping(index, 'target', e.target.value)}
                className="flex-1"
              />
              <Button variant="ghost" size="icon" onClick={() => removeMapping(index)}>
                <Trash className="h-4 w-4" />
              </Button>
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
            placeholder={'{\n  "name": "{{input.first_name}} {{input.last_name}}",\n  "email": "{{input.email}}"\n}'}
            value={config.template}
            onChange={(e) => updateConfig('template', e.target.value)}
            rows={6}
            className="font-mono text-sm"
          />
        </div>
      )}

      {/* Filter */}
      {config.transform_type === 'filter' && (
        <div className="space-y-2">
          <Label>Filter Expression</Label>
          <Input
            placeholder="item.status === 'active'"
            value={config.filter_expression}
            onChange={(e) => updateConfig('filter_expression', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            JavaScript expression to filter array items
          </p>
        </div>
      )}

      {/* Group By */}
      {config.transform_type === 'group' && (
        <div className="space-y-2">
          <Label>Group By Field</Label>
          <Input
            placeholder="category"
            value={config.group_by_field}
            onChange={(e) => updateConfig('group_by_field', e.target.value)}
          />
        </div>
      )}

      {/* Output Format */}
      <div className="space-y-2">
        <Label>Output Format</Label>
        <Select value={config.output_format} onValueChange={(v) => updateConfig('output_format', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="object">Object</SelectItem>
            <SelectItem value="array">Array</SelectItem>
            <SelectItem value="string">JSON String</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Test Button */}
      {onTest && (
        <Button onClick={onTest} variant="outline" className="w-full">
          <TestTube className="h-4 w-4 mr-2" />
          Test Transform
        </Button>
      )}
    </div>
  );
}
