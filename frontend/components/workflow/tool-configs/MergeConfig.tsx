'use client';

/**
 * MergeConfig - Merge Branches Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { Merge } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  NumberField,
  SelectField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const MERGE_MODES = [
  { value: 'wait_all', label: 'Wait for All Inputs' },
  { value: 'wait_any', label: 'Wait for Any Input' },
  { value: 'wait_n', label: 'Wait for N Inputs' },
  { value: 'pass_through', label: 'Pass Through (No Wait)' },
] as const;

const COMBINE_STRATEGIES = [
  { value: 'array', label: 'Array (collect all)' },
  { value: 'object', label: 'Object (merge by key)' },
  { value: 'concat', label: 'Concatenate Arrays' },
  { value: 'first', label: 'First Input Only' },
  { value: 'last', label: 'Last Input Only' },
] as const;

const SORT_ORDERS = [
  { value: 'asc', label: 'Ascending' },
  { value: 'desc', label: 'Descending' },
] as const;

// ============================================
// Types
// ============================================

interface MergeConfigData {
  merge_mode: string;
  combine_strategy: string;
  timeout: number;
  min_inputs: number;
  key_field: string;
  deduplicate: boolean;
  sort_by: string;
  sort_order: string;
}


const DEFAULTS: MergeConfigData = {
  merge_mode: 'wait_all',
  combine_strategy: 'array',
  timeout: 60,
  min_inputs: 1,
  key_field: '',
  deduplicate: false,
  sort_by: '',
  sort_order: 'asc',
};

// ============================================
// Component
// ============================================

export default function MergeConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<MergeConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Merge}
          {...TOOL_HEADER_PRESETS.storage}
          title="Merge"
          description="여러 분기를 하나로 병합"
        />

        {/* Merge Mode */}
        <SelectField
          label="병합 모드"
          value={config.merge_mode}
          onChange={(v) => updateField('merge_mode', v)}
          options={MERGE_MODES.map(m => ({ value: m.value, label: m.label }))}
        />

        {/* Min Inputs (for wait_n) */}
        {config.merge_mode === 'wait_n' && (
          <NumberField
            label="최소 입력 수"
            value={config.min_inputs}
            onChange={(v) => updateField('min_inputs', v)}
            min={1}
          />
        )}

        {/* Timeout */}
        {config.merge_mode !== 'pass_through' && (
          <NumberField
            label="타임아웃 (초)"
            value={config.timeout}
            onChange={(v) => updateField('timeout', v)}
            min={1}
            hint="입력을 기다리는 최대 시간"
          />
        )}


        {/* Combine Strategy */}
        <SelectField
          label="결합 전략"
          value={config.combine_strategy}
          onChange={(v) => updateField('combine_strategy', v)}
          options={COMBINE_STRATEGIES.map(c => ({ value: c.value, label: c.label }))}
        />

        {/* Key Field (for object merge) */}
        {config.combine_strategy === 'object' && (
          <TextField
            label="키 필드"
            value={config.key_field}
            onChange={(v) => updateField('key_field', v)}
            placeholder="id or name"
            hint="객체 병합 시 키로 사용할 필드"
          />
        )}

        {/* Sort */}
        <div className="grid grid-cols-2 gap-4">
          <TextField
            label="정렬 기준 (선택)"
            value={config.sort_by}
            onChange={(v) => updateField('sort_by', v)}
            placeholder="timestamp or priority"
          />
          <SelectField
            label="정렬 순서"
            value={config.sort_order}
            onChange={(v) => updateField('sort_order', v)}
            options={SORT_ORDERS.map(s => ({ value: s.value, label: s.label }))}
          />
        </div>

        {/* Deduplicate */}
        <SwitchField
          label="중복 제거"
          description="중복 항목 제거"
          checked={config.deduplicate}
          onChange={(v) => updateField('deduplicate', v)}
        />
      </div>
    </TooltipProvider>
  );
}
