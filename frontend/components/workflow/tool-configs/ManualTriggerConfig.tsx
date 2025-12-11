'use client';

/**
 * ManualTriggerConfig - Manual Trigger Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Zap, Plus, Trash } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  TextareaField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Types
// ============================================

interface InputField {
  name: string;
  type: string;
  required: boolean;
  default: string;
}

interface ManualTriggerConfigData {
  name: string;
  description: string;
  input_schema: InputField[];
  require_confirmation: boolean;
  confirmation_message: string;
  allowed_users: string;
}

const DEFAULTS: ManualTriggerConfigData = {
  name: 'Manual Trigger',
  description: '',
  input_schema: [],
  require_confirmation: false,
  confirmation_message: 'Are you sure you want to run this workflow?',
  allowed_users: '',
};

const FIELD_TYPES = ['string', 'number', 'boolean', 'file', 'json'] as const;


// ============================================
// Component
// ============================================

export default function ManualTriggerConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<ManualTriggerConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const addInputField = useCallback(() => {
    updateField('input_schema', [
      ...config.input_schema,
      { name: '', type: 'string', required: false, default: '' },
    ]);
  }, [config.input_schema, updateField]);

  const updateInputField = useCallback((index: number, field: keyof InputField, value: string | boolean) => {
    const newSchema = [...config.input_schema];
    newSchema[index] = { ...newSchema[index], [field]: value };
    updateField('input_schema', newSchema);
  }, [config.input_schema, updateField]);

  const removeInputField = useCallback((index: number) => {
    updateField('input_schema', config.input_schema.filter((_, i) => i !== index));
  }, [config.input_schema, updateField]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Zap}
          {...TOOL_HEADER_PRESETS.trigger}
          title="Manual Trigger"
          description="수동으로 워크플로우 실행 시작"
        />

        {/* Name & Description */}
        <TextField
          label="트리거 이름"
          value={config.name}
          onChange={(v) => updateField('name', v)}
        />

        <TextareaField
          label="설명"
          value={config.description}
          onChange={(v) => updateField('description', v)}
          placeholder="이 트리거를 사용할 때를 설명..."
          rows={2}
        />


        {/* Input Schema */}
        <div className="space-y-3">
          <Label>입력 필드</Label>
          <p className="text-xs text-muted-foreground">
            트리거 시 사용자가 입력해야 할 필드 정의
          </p>
          {config.input_schema.map((field, index) => (
            <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
              <div className="flex gap-2">
                <Input
                  placeholder="필드 이름"
                  value={field.name}
                  onChange={(e) => updateInputField(index, 'name', e.target.value)}
                  className="flex-1"
                />
                <select
                  value={field.type}
                  onChange={(e) => updateInputField(index, 'type', e.target.value)}
                  className="px-3 py-2 border rounded-md bg-background"
                >
                  {FIELD_TYPES.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
                <Button variant="ghost" size="icon" onClick={() => removeInputField(index)}>
                  <Trash className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex gap-2 items-center">
                <Input
                  placeholder="기본값"
                  value={field.default}
                  onChange={(e) => updateInputField(index, 'default', e.target.value)}
                  className="flex-1"
                />
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={field.required}
                    onChange={(e) => updateInputField(index, 'required', e.target.checked)}
                  />
                  필수
                </label>
              </div>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addInputField} className="w-full">
            <Plus className="h-4 w-4 mr-2" />
            입력 필드 추가
          </Button>
        </div>

        {/* Confirmation */}
        <SwitchField
          label="확인 필요"
          description="실행 전 확인 요청"
          checked={config.require_confirmation}
          onChange={(v) => updateField('require_confirmation', v)}
        />

        {config.require_confirmation && (
          <TextField
            label="확인 메시지"
            value={config.confirmation_message}
            onChange={(v) => updateField('confirmation_message', v)}
          />
        )}

        {/* Access Control */}
        <TextField
          label="허용된 사용자 (선택)"
          value={config.allowed_users}
          onChange={(v) => updateField('allowed_users', v)}
          placeholder="user1@example.com, user2@example.com"
          hint="비워두면 모든 사용자 허용"
        />
      </div>
    </TooltipProvider>
  );
}
