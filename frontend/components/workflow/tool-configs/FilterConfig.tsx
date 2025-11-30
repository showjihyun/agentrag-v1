'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Filter, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const OPERATORS = [
  { value: 'equals', label: 'Equals (==)' },
  { value: 'not_equals', label: 'Not Equals (!=)' },
  { value: 'contains', label: 'Contains' },
  { value: 'not_contains', label: 'Does Not Contain' },
  { value: 'starts_with', label: 'Starts With' },
  { value: 'ends_with', label: 'Ends With' },
  { value: 'greater_than', label: 'Greater Than (>)' },
  { value: 'less_than', label: 'Less Than (<)' },
  { value: 'greater_equal', label: 'Greater or Equal (>=)' },
  { value: 'less_equal', label: 'Less or Equal (<=)' },
  { value: 'is_empty', label: 'Is Empty' },
  { value: 'is_not_empty', label: 'Is Not Empty' },
  { value: 'regex', label: 'Matches Regex' },
  { value: 'in_list', label: 'In List' },
];

export default function FilterConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    input: data.input || '{{input.items}}',
    conditions: data.conditions || [{ field: '', operator: 'equals', value: '' }],
    logic: data.logic || 'and',
    keep_matching: data.keep_matching !== false,
    limit: data.limit || 0,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addCondition = () => {
    updateConfig('conditions', [...config.conditions, { field: '', operator: 'equals', value: '' }]);
  };

  const updateCondition = (index: number, field: string, value: string) => {
    const newConditions = [...config.conditions];
    newConditions[index][field] = value;
    updateConfig('conditions', newConditions);
  };

  const removeCondition = (index: number) => {
    updateConfig('conditions', config.conditions.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-950">
          <Filter className="h-5 w-5 text-rose-600 dark:text-rose-400" />
        </div>
        <div>
          <h3 className="font-semibold">Filter</h3>
          <p className="text-sm text-muted-foreground">Filter data items by conditions</p>
        </div>
      </div>

      {/* Input */}
      <div className="space-y-2">
        <Label>Input Data</Label>
        <Input
          placeholder="{{input.items}} or {{previous.data}}"
          value={config.input}
          onChange={(e) => updateConfig('input', e.target.value)}
        />
      </div>

      {/* Logic */}
      <div className="space-y-2">
        <Label>Condition Logic</Label>
        <Select value={config.logic} onValueChange={(v) => updateConfig('logic', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="and">AND (all conditions must match)</SelectItem>
            <SelectItem value="or">OR (any condition must match)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Conditions */}
      <div className="space-y-3">
        <Label>Conditions</Label>
        {config.conditions.map((condition: any, index: number) => (
          <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
            <div className="flex gap-2">
              <Input
                placeholder="field.path"
                value={condition.field}
                onChange={(e) => updateCondition(index, 'field', e.target.value)}
                className="flex-1"
              />
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeCondition(index)}
                disabled={config.conditions.length <= 1}
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Select
                value={condition.operator}
                onValueChange={(v) => updateCondition(index, 'operator', v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {OPERATORS.map(op => (
                    <SelectItem key={op.value} value={op.value}>
                      {op.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {!['is_empty', 'is_not_empty'].includes(condition.operator) && (
                <Input
                  placeholder="Value"
                  value={condition.value}
                  onChange={(e) => updateCondition(index, 'value', e.target.value)}
                />
              )}
            </div>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addCondition} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Condition
        </Button>
      </div>

      {/* Options */}
      <div className="flex items-center justify-between">
        <div>
          <Label>Keep Matching Items</Label>
          <p className="text-xs text-muted-foreground">
            {config.keep_matching ? 'Keep items that match' : 'Remove items that match'}
          </p>
        </div>
        <Switch
          checked={config.keep_matching}
          onCheckedChange={(checked) => updateConfig('keep_matching', checked)}
        />
      </div>

      {/* Limit */}
      <div className="space-y-2">
        <Label>Limit Results (0 = no limit)</Label>
        <Input
          type="number"
          min="0"
          value={config.limit}
          onChange={(e) => updateConfig('limit', parseInt(e.target.value) || 0)}
        />
      </div>
    </div>
  );
}
