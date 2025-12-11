'use client';

/**
 * ParallelConfig - Parallel Execution Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { GitBranch } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  NumberField,
  SelectField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const RESULT_ORDERS = [
  { value: 'completion', label: 'Completion Order' },
  { value: 'definition', label: 'Definition Order' },
] as const;

// ============================================
// Types
// ============================================

interface ParallelConfigData {
  max_concurrency: number;
  wait_for_all: boolean;
  timeout: number;
  fail_fast: boolean;
  collect_results: boolean;
  result_order: string;
}

const DEFAULTS: ParallelConfigData = {
  max_concurrency: 5,
  wait_for_all: true,
  timeout: 60,
  fail_fast: false,
  collect_results: true,
  result_order: 'completion',
};

// ============================================
// Component
// ============================================

export default function ParallelConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<ParallelConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });


  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={GitBranch}
          iconBgColor="bg-purple-100 dark:bg-purple-950"
          iconColor="text-purple-600 dark:text-purple-400"
          title="Parallel"
          description="분기를 병렬로 실행"
        />

        {/* Max Concurrency */}
        <NumberField
          label="최대 동시 실행 수"
          value={config.max_concurrency}
          onChange={(v) => updateField('max_concurrency', v)}
          min={1}
          max={20}
          hint="동시에 실행할 최대 분기 수"
        />

        {/* Timeout */}
        <NumberField
          label="타임아웃 (초)"
          value={config.timeout}
          onChange={(v) => updateField('timeout', v)}
          min={1}
          max={3600}
          hint="모든 분기 완료를 기다리는 최대 시간"
        />

        {/* Result Order */}
        <SelectField
          label="결과 순서"
          value={config.result_order}
          onChange={(v) => updateField('result_order', v)}
          options={RESULT_ORDERS.map(r => ({ value: r.value, label: r.label }))}
          hint="병렬 분기 결과의 정렬 방식"
        />

        {/* Options */}
        <SwitchField
          label="모두 대기"
          description="모든 분기가 완료될 때까지 대기"
          checked={config.wait_for_all}
          onChange={(v) => updateField('wait_for_all', v)}
        />

        <SwitchField
          label="빠른 실패"
          description="하나라도 실패하면 모든 분기 중단"
          checked={config.fail_fast}
          onChange={(v) => updateField('fail_fast', v)}
        />

        <SwitchField
          label="결과 수집"
          description="모든 분기의 결과를 결합"
          checked={config.collect_results}
          onChange={(v) => updateField('collect_results', v)}
        />
      </div>
    </TooltipProvider>
  );
}
