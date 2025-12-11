'use client';

/**
 * CalculatorConfig - Mathematical Calculations Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Calculator, TestTube } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TextField,
  TextareaField,
  SelectField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

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
] as const;

const PRECISION_OPTIONS = [
  { value: '0', label: '0 decimal places' },
  { value: '1', label: '1 decimal place' },
  { value: '2', label: '2 decimal places' },
  { value: '3', label: '3 decimal places' },
  { value: '4', label: '4 decimal places' },
  { value: '5', label: '5 decimal places' },
  { value: '6', label: '6 decimal places' },
] as const;

// ============================================
// Types
// ============================================

interface CalculatorConfigData {
  operation: string;
  expression: string;
  value_a: string;
  value_b: string;
  values: string;
  precision: number;
}

const DEFAULTS: CalculatorConfigData = {
  operation: 'expression',
  expression: '',
  value_a: '',
  value_b: '',
  values: '',
  precision: 2,
};

// ============================================
// Component
// ============================================

export default function CalculatorConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<CalculatorConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const handleTest = useCallback(() => {
    onTest?.();
  }, [onTest]);

  const needsTwoValues = ['add', 'subtract', 'multiply', 'divide', 'modulo', 'power'].includes(config.operation);
  const needsOneValue = ['sqrt', 'abs', 'round', 'floor', 'ceil'].includes(config.operation);
  const needsMultipleValues = ['min', 'max', 'average', 'sum'].includes(config.operation);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Calculator}
          iconBgColor="bg-purple-100 dark:bg-purple-950"
          iconColor="text-purple-600 dark:text-purple-400"
          title="Calculator"
          description="수학 계산 수행"
        />

        {/* Operation */}
        <SelectField
          label="연산"
          value={config.operation}
          onChange={(v) => updateField('operation', v)}
          options={OPERATIONS.map(op => ({ value: op.value, label: op.label }))}
        />

        {/* Custom Expression */}
        {config.operation === 'expression' && (
          <TextareaField
            label="수식"
            value={config.expression}
            onChange={(v) => updateField('expression', v)}
            placeholder="e.g., (a + b) * 2 / c"
            rows={3}
            mono
            hint="{{input.value}} 같은 변수나 표준 수학 연산자 사용 가능"
          />
        )}

        {/* Two Values */}
        {needsTwoValues && (
          <div className="grid grid-cols-2 gap-4">
            <TextField
              label="값 A"
              value={config.value_a}
              onChange={(v) => updateField('value_a', v)}
              placeholder="10 or {{input.a}}"
            />
            <TextField
              label="값 B"
              value={config.value_b}
              onChange={(v) => updateField('value_b', v)}
              placeholder="5 or {{input.b}}"
            />
          </div>
        )}

        {/* One Value */}
        {needsOneValue && (
          <TextField
            label="값"
            value={config.value_a}
            onChange={(v) => updateField('value_a', v)}
            placeholder="25 or {{input.value}}"
          />
        )}

        {/* Multiple Values */}
        {needsMultipleValues && (
          <TextField
            label="값 (쉼표로 구분)"
            value={config.values}
            onChange={(v) => updateField('values', v)}
            placeholder="1, 2, 3, 4, 5 or {{input.values}}"
          />
        )}

        {/* Precision */}
        <SelectField
          label="소수점 자릿수"
          value={String(config.precision)}
          onChange={(v) => updateField('precision', parseInt(v))}
          options={PRECISION_OPTIONS.map(p => ({ value: p.value, label: p.label }))}
        />

        {/* Test Button */}
        {onTest && (
          <Button onClick={handleTest} variant="outline" className="w-full">
            <TestTube className="h-4 w-4 mr-2" />
            계산 테스트
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}
