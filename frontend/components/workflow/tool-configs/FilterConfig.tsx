'use client';

/**
 * FilterConfig - Data Filter Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Filter, Plus, Trash } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TextField,
  NumberField,
  SelectField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

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
] as const;

const LOGIC_OPTIONS = [
  { value: 'and', label: 'AND (All conditions match)' },
  { value: 'or', label: 'OR (Any condition matches)' },
] as const;

// ============================================
// Types
// ============================================

interface ConditionItem {
  field: string;
  operator: string;
  value: string;
}

interface FilterConfigData {
  input: string;
  conditions: ConditionItem[];
  logic: string;
  keep_matching: boolean;
  limit: number;
}

const DEFAULTS: FilterConfigData = {
  input: '{{input.items}}',
  conditions: [{ field: '', operator: 'equals', value: '' }],
  logic: 'and',
  keep_matching: true,
  limit: 0,
};

// ============================================
// Component
// ============================================

export default function FilterConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<FilterConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const addCondition = useCallback(() => {
    updateField('conditions', [...config.conditions, { field: '', operator: 'equals', value: '' }]);
  }, [config.conditions, updateField]);

  const updateCondition = useCallback((index: number, field: keyof ConditionItem, value: string) => {
    const newConditions = [...config.conditions];
    newConditions[index] = { ...newConditions[index], [field]: value };
    updateField('conditions', newConditions);
  }, [config.conditions, updateField]);

  const removeCondition = useCallback((index: number) => {
    updateField('conditions', config.conditions.filter((_, i) => i !== index));
  }, [config.conditions, updateField]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Filter}
          iconBgColor="bg-rose-100 dark:bg-rose-950"
          iconColor="text-rose-600 dark:text-rose-400"
          title="Filter"
          description="Filter data items based on conditions"
        />

        {/* Input */}
        <TextField
          label="Input Data"
          value={config.input}
          onChange={(v) => updateField('input', v)}
          placeholder="{{input.items}} or {{previous.data}}"
        />

        {/* Logic */}
        <SelectField
          label="Condition Logic"
          value={config.logic}
          onChange={(v) => updateField('logic', v)}
          options={LOGIC_OPTIONS.map(l => ({ value: l.value, label: l.label }))}
        />

        {/* Conditions */}
        <div className="space-y-3">
          <Label>Conditions</Label>
          {config.conditions.map((condition, index) => (
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
        <SwitchField
          label="Keep Matching Items"
          description={config.keep_matching ? 'Keep matching items' : 'Remove matching items'}
          checked={config.keep_matching}
          onChange={(v) => updateField('keep_matching', v)}
        />

        {/* Limit */}
        <NumberField
          label="Result Limit (0 = No limit)"
          value={config.limit}
          onChange={(v) => updateField('limit', v)}
          min={0}
        />
      </div>
    </TooltipProvider>
  );
}
