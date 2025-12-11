'use client';

/**
 * LoopConfig - Loop/Iteration Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { RefreshCw } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TextField,
  NumberField,
  SelectField,
  SwitchField,
  InfoBox,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const LOOP_TYPES = [
  { value: 'foreach', label: 'For Each (iterate items)' },
  { value: 'count', label: 'Count (fixed iterations)' },
  { value: 'range', label: 'Range (start to end)' },
  { value: 'while', label: 'While (condition-based)' },
] as const;

// ============================================
// Types
// ============================================

interface LoopConfigData {
  loop_type: string;
  items: string;
  count: number;
  start: number;
  end: number;
  step: number;
  condition: string;
  max_iterations: number;
  batch_size: number;
  parallel: boolean;
  continue_on_error: boolean;
}

const DEFAULTS: LoopConfigData = {
  loop_type: 'foreach',
  items: '{{input.items}}',
  count: 10,
  start: 0,
  end: 10,
  step: 1,
  condition: '',
  max_iterations: 100,
  batch_size: 1,
  parallel: false,
  continue_on_error: false,
};

// ============================================
// Component
// ============================================

export default function LoopConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<LoopConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={RefreshCw}
          iconBgColor="bg-indigo-100 dark:bg-indigo-950"
          iconColor="text-indigo-600 dark:text-indigo-400"
          title="Loop"
          description="Iterate over items or count"
        />

        {/* Loop Type */}
        <SelectField
          label="Loop Type"
          value={config.loop_type}
          onChange={(v) => updateField('loop_type', v)}
          options={LOOP_TYPES.map(t => ({ value: t.value, label: t.label }))}
        />

        {/* For Each */}
        {config.loop_type === 'foreach' && (
          <TextField
            label="Items to Iterate"
            value={config.items}
            onChange={(v) => updateField('items', v)}
            placeholder="{{input.items}} or {{previous.data}}"
            hint="Array or object to iterate. Current item: {{item}}, index: {{index}}"
            tooltip="배열이나 객체를 순회합니다. 현재 항목은 {{item}}, 인덱스는 {{index}}로 접근 가능합니다."
          />
        )}

        {/* Count */}
        {config.loop_type === 'count' && (
          <NumberField
            label="Number of Iterations"
            value={config.count}
            onChange={(v) => updateField('count', v)}
            min={1}
          />
        )}

        {/* Range */}
        {config.loop_type === 'range' && (
          <div className="grid grid-cols-3 gap-4">
            <NumberField
              label="Start"
              value={config.start}
              onChange={(v) => updateField('start', v)}
            />
            <NumberField
              label="End"
              value={config.end}
              onChange={(v) => updateField('end', v)}
            />
            <NumberField
              label="Step"
              value={config.step}
              onChange={(v) => updateField('step', v)}
              min={1}
            />
          </div>
        )}

        {/* While */}
        {config.loop_type === 'while' && (
          <TextField
            label="Condition"
            value={config.condition}
            onChange={(v) => updateField('condition', v)}
            placeholder="{{item.status}} !== 'complete'"
            hint="Loop continues while this condition is true"
            tooltip="조건이 참인 동안 반복합니다. 무한 루프 방지를 위해 max_iterations를 설정하세요."
          />
        )}

        {/* Max Iterations */}
        <NumberField
          label="Max Iterations (Safety Limit)"
          value={config.max_iterations}
          onChange={(v) => updateField('max_iterations', v)}
          min={1}
          max={1000}
          tooltip="무한 루프 방지를 위한 최대 반복 횟수"
        />

        {/* Batch Size */}
        <NumberField
          label="Batch Size"
          value={config.batch_size}
          onChange={(v) => updateField('batch_size', v)}
          min={1}
          hint="Process items in batches (1 = one at a time)"
        />

        {/* Options */}
        <div className="space-y-2 pt-2 border-t">
          <SwitchField
            label="Parallel Execution"
            description="Execute iterations in parallel"
            checked={config.parallel}
            onChange={(v) => updateField('parallel', v)}
          />

          <SwitchField
            label="Continue on Error"
            description="Continue loop if an iteration fails"
            checked={config.continue_on_error}
            onChange={(v) => updateField('continue_on_error', v)}
          />
        </div>

        {/* Info */}
        <InfoBox title="Available Variables:" variant="info">
          <div className="space-y-1 font-mono text-xs">
            <div>• <code>{'{{item}}'}</code> - Current item</div>
            <div>• <code>{'{{index}}'}</code> - Current index (0-based)</div>
            <div>• <code>{'{{loop.total}}'}</code> - Total iterations</div>
          </div>
        </InfoBox>
      </div>
    </TooltipProvider>
  );
}
