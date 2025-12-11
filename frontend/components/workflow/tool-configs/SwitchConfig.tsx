'use client';

/**
 * SwitchConfig - Multi-way Branching Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { GitBranch, Plus, Trash } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  SelectField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const MATCH_TYPES = [
  { value: 'exact', label: 'Exact Match' },
  { value: 'contains', label: 'Contains' },
  { value: 'startswith', label: 'Starts With' },
  { value: 'endswith', label: 'Ends With' },
  { value: 'regex', label: 'Regular Expression' },
  { value: 'range', label: 'Numeric Range' },
] as const;

// ============================================
// Types
// ============================================

interface CaseItem {
  value: string;
  output: string;
}

interface SwitchConfigData {
  switch_on: string;
  match_type: string;
  cases: CaseItem[];
  default_output: string;
  case_sensitive: boolean;
}


const DEFAULTS: SwitchConfigData = {
  switch_on: '{{input.value}}',
  match_type: 'exact',
  cases: [{ value: '', output: 'case_1' }],
  default_output: 'default',
  case_sensitive: true,
};

// ============================================
// Component
// ============================================

export default function SwitchConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<SwitchConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const addCase = useCallback(() => {
    updateField('cases', [...config.cases, { value: '', output: `case_${config.cases.length + 1}` }]);
  }, [config.cases, updateField]);

  const updateCase = useCallback((index: number, field: keyof CaseItem, value: string) => {
    const newCases = [...config.cases];
    newCases[index] = { ...newCases[index], [field]: value };
    updateField('cases', newCases);
  }, [config.cases, updateField]);

  const removeCase = useCallback((index: number) => {
    updateField('cases', config.cases.filter((_, i) => i !== index));
  }, [config.cases, updateField]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={GitBranch}
          {...TOOL_HEADER_PRESETS.control}
          title="Switch"
          description="값에 따른 다중 분기"
        />

        {/* Switch On */}
        <TextField
          label="분기 기준 값"
          value={config.switch_on}
          onChange={(v) => updateField('switch_on', v)}
          placeholder="{{input.status}} or {{previous.type}}"
          hint="케이스와 비교할 값"
        />

        {/* Match Type */}
        <SelectField
          label="매칭 유형"
          value={config.match_type}
          onChange={(v) => updateField('match_type', v)}
          options={MATCH_TYPES.map(m => ({ value: m.value, label: m.label }))}
        />


        {/* Cases */}
        <div className="space-y-3">
          <Label>케이스</Label>
          {config.cases.map((caseItem, index) => (
            <div key={index} className="flex gap-2 items-center p-3 border rounded-lg bg-muted/30">
              <div className="flex-1">
                <Input
                  placeholder={config.match_type === 'range' ? 'e.g., 0-100' : '매칭 값'}
                  value={caseItem.value}
                  onChange={(e) => updateCase(index, 'value', e.target.value)}
                />
              </div>
              <span className="text-muted-foreground">→</span>
              <div className="w-32">
                <Input
                  placeholder="출력"
                  value={caseItem.output}
                  onChange={(e) => updateCase(index, 'output', e.target.value)}
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => removeCase(index)}
                disabled={config.cases.length <= 1}
              >
                <Trash className="h-4 w-4" />
              </Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addCase} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            케이스 추가
          </Button>
        </div>

        {/* Default Output */}
        <TextField
          label="기본 출력 (매칭 없음)"
          value={config.default_output}
          onChange={(v) => updateField('default_output', v)}
          placeholder="default"
          hint="어떤 케이스도 매칭되지 않을 때의 출력"
        />
      </div>
    </TooltipProvider>
  );
}
