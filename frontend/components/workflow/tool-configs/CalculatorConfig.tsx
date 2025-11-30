'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Calculator, TestTube } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const OPERATIONS = [
  { value: 'expression', label: 'Custom Expression' },
  { value: 'add', label: 'Add (+)' },
  { value: 'subtract', label: 'Subtract (-)' },
  { value: 'multiply', label: 'Multiply (×)' },
  { value: 'divide', label: 'Divide (÷)' },
  { value: 'modulo', label: 'Modulo (%)' },
  { value: 'power', label: 'Power (^)' },
  { value: 'sqrt', label: 'Square Root (√)' },
  { value: 'abs', label: 'Absolute Value' },
  { value: 'round', label: 'Round' },
  { value: 'floor', label: 'Floor' },
  { value: 'ceil', label: 'Ceiling' },
  { value: 'min', label: 'Minimum' },
  { value: 'max', label: 'Maximum' },
  { value: 'average', label: 'Average' },
  { value: 'sum', label: 'Sum' },
];

export default function CalculatorConfig({ data, onChange, onTest }: ToolConfigProps) {
  const [config, setConfig] = useState({
    operation: data.operation || 'expression',
    expression: data.expression || '',
    value_a: data.value_a || '',
    value_b: data.value_b || '',
    values: data.values || '',
    precision: data.precision || 2,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const needsTwoValues = ['add', 'subtract', 'multiply', 'divide', 'modulo', 'power'].includes(config.operation);
  const needsOneValue = ['sqrt', 'abs', 'round', 'floor', 'ceil'].includes(config.operation);
  const needsMultipleValues = ['min', 'max', 'average', 'sum'].includes(config.operation);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950">
          <Calculator className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="font-semibold">Calculator</h3>
          <p className="text-sm text-muted-foreground">Mathematical calculations</p>
        </div>
      </div>

      {/* Operation */}
      <div className="space-y-2">
        <Label>Operation</Label>
        <Select value={config.operation} onValueChange={(v) => updateConfig('operation', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {OPERATIONS.map(op => (
              <SelectItem key={op.value} value={op.value}>
                {op.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Custom Expression */}
      {config.operation === 'expression' && (
        <div className="space-y-2">
          <Label>Expression</Label>
          <Textarea
            placeholder="e.g., (a + b) * 2 / c"
            value={config.expression}
            onChange={(e) => updateConfig('expression', e.target.value)}
            rows={3}
            className="font-mono"
          />
          <p className="text-xs text-muted-foreground">
            Use variables like {'{{input.value}}'} or standard math operators
          </p>
        </div>
      )}

      {/* Two Values */}
      {needsTwoValues && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Value A</Label>
            <Input
              type="text"
              placeholder="10 or {{input.a}}"
              value={config.value_a}
              onChange={(e) => updateConfig('value_a', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Value B</Label>
            <Input
              type="text"
              placeholder="5 or {{input.b}}"
              value={config.value_b}
              onChange={(e) => updateConfig('value_b', e.target.value)}
            />
          </div>
        </div>
      )}

      {/* One Value */}
      {needsOneValue && (
        <div className="space-y-2">
          <Label>Value</Label>
          <Input
            type="text"
            placeholder="25 or {{input.value}}"
            value={config.value_a}
            onChange={(e) => updateConfig('value_a', e.target.value)}
          />
        </div>
      )}

      {/* Multiple Values */}
      {needsMultipleValues && (
        <div className="space-y-2">
          <Label>Values (comma-separated)</Label>
          <Input
            type="text"
            placeholder="1, 2, 3, 4, 5 or {{input.values}}"
            value={config.values}
            onChange={(e) => updateConfig('values', e.target.value)}
          />
        </div>
      )}

      {/* Precision */}
      <div className="space-y-2">
        <Label>Decimal Precision</Label>
        <Select value={String(config.precision)} onValueChange={(v) => updateConfig('precision', parseInt(v))}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {[0, 1, 2, 3, 4, 5, 6].map(p => (
              <SelectItem key={p} value={String(p)}>
                {p} decimal places
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Test Button */}
      {onTest && (
        <Button onClick={onTest} variant="outline" className="w-full">
          <TestTube className="h-4 w-4 mr-2" />
          Test Calculation
        </Button>
      )}
    </div>
  );
}
