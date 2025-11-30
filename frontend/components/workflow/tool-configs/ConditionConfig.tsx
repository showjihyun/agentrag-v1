'use client';

import { useState, useEffect } from 'react';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { GitBranch, Code } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const CONDITION_OPERATORS = [
  { id: 'equals', name: 'Equals (==)', example: 'value == "expected"' },
  { id: 'not_equals', name: 'Not Equals (!=)', example: 'value != "expected"' },
  { id: 'greater_than', name: 'Greater Than (>)', example: 'value > 10' },
  { id: 'less_than', name: 'Less Than (<)', example: 'value < 10' },
  { id: 'contains', name: 'Contains', example: '"text" in value' },
  { id: 'starts_with', name: 'Starts With', example: 'value.startswith("prefix")' },
  { id: 'ends_with', name: 'Ends With', example: 'value.endswith("suffix")' },
  { id: 'is_empty', name: 'Is Empty', example: 'not value or value == ""' },
  { id: 'is_not_empty', name: 'Is Not Empty', example: 'value and value != ""' },
  { id: 'custom', name: 'Custom Expression', example: 'Write your own Python expression' },
];

export default function ConditionConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    operator: data.operator || 'equals',
    condition: data.condition || '',
    variable: data.variable || 'input',
    value: data.value || '',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const selectedOperator = CONDITION_OPERATORS.find(op => op.id === config.operator);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950">
          <GitBranch className="h-5 w-5 text-blue-600 dark:text-blue-400" />
        </div>
        <div>
          <h3 className="font-semibold">Condition</h3>
          <p className="text-sm text-muted-foreground">If/else branching logic</p>
        </div>
      </div>

      {/* Operator Selection */}
      <div className="space-y-2">
        <Label>Condition Type</Label>
        <Select value={config.operator} onValueChange={(v) => updateConfig('operator', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CONDITION_OPERATORS.map(op => (
              <SelectItem key={op.id} value={op.id}>
                <div className="flex flex-col">
                  <span className="font-medium">{op.name}</span>
                  <span className="text-xs text-muted-foreground">{op.example}</span>
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Variable Name */}
      {config.operator !== 'custom' && (
        <div className="space-y-2">
          <Label>Variable to Check</Label>
          <Select value={config.variable} onValueChange={(v) => updateConfig('variable', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="input">input (from previous node)</SelectItem>
              <SelectItem value="context.user_id">context.user_id</SelectItem>
              <SelectItem value="context.workflow_id">context.workflow_id</SelectItem>
              <SelectItem value="custom">Custom variable...</SelectItem>
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Condition Expression */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Code className="h-4 w-4" />
          {config.operator === 'custom' ? 'Python Expression *' : 'Condition *'}
        </Label>
        <Textarea
          placeholder={selectedOperator?.example || 'Enter condition...'}
          value={config.condition}
          onChange={(e) => updateConfig('condition', e.target.value)}
          rows={4}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Python expression that returns True or False. Available: <code className="px-1 py-0.5 bg-muted rounded">input</code>, <code className="px-1 py-0.5 bg-muted rounded">context</code>
        </p>
      </div>

      {/* Info Box */}
      <div className="p-3 bg-muted rounded-lg space-y-2">
        <p className="text-xs font-medium">Examples:</p>
        <div className="space-y-1 text-xs text-muted-foreground font-mono">
          <div>• <code>input.get("status") == "success"</code></div>
          <div>• <code>len(input.get("items", [])) &gt; 0</code></div>
          <div>• <code>context.user_id in ["admin", "user1"]</code></div>
        </div>
      </div>

      {/* Output Info */}
      <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-1">Outputs:</p>
        <div className="space-y-1 text-xs text-blue-700 dark:text-blue-300">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">True</Badge>
            <span>→ Connects to "true" output</span>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">False</Badge>
            <span>→ Connects to "false" output</span>
          </div>
        </div>
      </div>
    </div>
  );
}
