'use client';

/**
 * ConditionConfig - Condition/Branching Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { Badge } from '@/components/ui/badge';
import { GitBranch, Code } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  SelectField,
  TextareaField,
  InfoBox,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const CONDITION_OPERATORS = [
  { value: 'equals', label: 'Equals (==)', description: 'value == "expected"' },
  { value: 'not_equals', label: 'Not Equals (!=)', description: 'value != "expected"' },
  { value: 'greater_than', label: 'Greater Than (>)', description: 'value > 10' },
  { value: 'less_than', label: 'Less Than (<)', description: 'value < 10' },
  { value: 'contains', label: 'Contains', description: '"text" in value' },
  { value: 'starts_with', label: 'Starts With', description: 'value.startswith("prefix")' },
  { value: 'ends_with', label: 'Ends With', description: 'value.endswith("suffix")' },
  { value: 'is_empty', label: 'Is Empty', description: 'not value or value == ""' },
  { value: 'is_not_empty', label: 'Is Not Empty', description: 'value and value != ""' },
  { value: 'custom', label: 'Custom Expression', description: 'Write your own Python expression' },
] as const;

const VARIABLE_OPTIONS = [
  { value: 'input', label: 'input (from previous node)' },
  { value: 'context.user_id', label: 'context.user_id' },
  { value: 'context.workflow_id', label: 'context.workflow_id' },
  { value: 'custom', label: 'Custom variable...' },
] as const;

// ============================================
// Types
// ============================================

interface ConditionConfigData {
  operator: string;
  condition: string;
  variable: string;
  value: string;
}

const DEFAULTS: ConditionConfigData = {
  operator: 'equals',
  condition: '',
  variable: 'input',
  value: '',
};

// ============================================
// Component
// ============================================

export default function ConditionConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<ConditionConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const selectedOperator = CONDITION_OPERATORS.find(op => op.value === config.operator);
  const isCustom = config.operator === 'custom';

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={GitBranch}
          {...TOOL_HEADER_PRESETS.control}
          title="Condition"
          description="If/else branching logic"
        />

        {/* Operator Selection */}
        <SelectField
          label="Condition Type"
          value={config.operator}
          onChange={(v) => updateField('operator', v)}
          options={CONDITION_OPERATORS.map(op => ({
            value: op.value,
            label: op.label,
            description: op.description,
          }))}
        />

        {/* Variable Name */}
        {!isCustom && (
          <SelectField
            label="Variable to Check"
            value={config.variable}
            onChange={(v) => updateField('variable', v)}
            options={VARIABLE_OPTIONS.map(v => ({ value: v.value, label: v.label }))}
          />
        )}

        {/* Condition Expression */}
        <TextareaField
          label={isCustom ? 'Python Expression' : 'Condition'}
          value={config.condition}
          onChange={(v) => updateField('condition', v)}
          placeholder={selectedOperator?.description || 'Enter condition...'}
          rows={4}
          required
          icon={Code}
          hint="Python expression that returns True or False. Available: input, context"
          mono
        />

        {/* Examples Info Box */}
        <InfoBox title="Examples:">
          <div className="space-y-1 font-mono">
            <div>• <code>input.get("status") == "success"</code></div>
            <div>• <code>len(input.get("items", [])) &gt; 0</code></div>
            <div>• <code>context.user_id in ["admin", "user1"]</code></div>
          </div>
        </InfoBox>

        {/* Output Info */}
        <InfoBox title="Outputs:" variant="info">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">True</Badge>
              <span>→ Connects to "true" output</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-xs">False</Badge>
              <span>→ Connects to "false" output</span>
            </div>
          </div>
        </InfoBox>
      </div>
    </TooltipProvider>
  );
}
