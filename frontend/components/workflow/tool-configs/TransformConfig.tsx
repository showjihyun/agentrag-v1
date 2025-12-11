'use client';

/**
 * TransformConfig - Data Transform Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Code, Plus, Trash } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  TextareaField,
  SelectField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const TRANSFORM_TYPES = [
  { value: 'mapping', label: 'Field Mapping' },
  { value: 'template', label: 'Template' },
  { value: 'expression', label: 'Expression' },
  { value: 'rename', label: 'Rename Fields' },
  { value: 'pick', label: 'Pick Fields' },
  { value: 'omit', label: 'Omit Fields' },
] as const;

const OUTPUT_TYPES = [
  { value: 'object', label: 'Object' },
  { value: 'array', label: 'Array' },
  { value: 'string', label: 'String' },
  { value: 'preserve', label: 'Preserve Input Type' },
] as const;


// ============================================
// Types
// ============================================

interface MappingItem {
  source: string;
  target: string;
  transform: string;
}

interface TransformConfigData {
  input: string;
  transform_type: string;
  mappings: MappingItem[];
  template: string;
  expression: string;
  output_type: string;
}

const DEFAULTS: TransformConfigData = {
  input: '{{input}}',
  transform_type: 'mapping',
  mappings: [{ source: '', target: '', transform: '' }],
  template: '',
  expression: '',
  output_type: 'object',
};

// ============================================
// Component
// ============================================

export default function TransformConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<TransformConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const addMapping = useCallback(() => {
    updateField('mappings', [...config.mappings, { source: '', target: '', transform: '' }]);
  }, [config.mappings, updateField]);

  const updateMapping = useCallback((index: number, field: keyof MappingItem, value: string) => {
    const newMappings = [...config.mappings];
    newMappings[index] = { ...newMappings[index], [field]: value };
    updateField('mappings', newMappings);
  }, [config.mappings, updateField]);

  const removeMapping = useCallback((index: number) => {
    updateField('mappings', config.mappings.filter((_, i) => i !== index));
  }, [config.mappings, updateField]);


  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Code}
          {...TOOL_HEADER_PRESETS.ai}
          title="Transform"
          description="데이터 변환 및 재구성"
        />

        {/* Input */}
        <TextField
          label="입력 데이터"
          value={config.input}
          onChange={(v) => updateField('input', v)}
          placeholder="{{input}} or {{previous.output}}"
        />

        {/* Transform Type */}
        <SelectField
          label="변환 유형"
          value={config.transform_type}
          onChange={(v) => updateField('transform_type', v)}
          options={TRANSFORM_TYPES.map(t => ({ value: t.value, label: t.label }))}
        />

        {/* Field Mapping */}
        {config.transform_type === 'mapping' && (
          <div className="space-y-3">
            <Label>필드 매핑</Label>
            {config.mappings.map((mapping, index) => (
              <div key={index} className="p-3 border rounded-lg bg-muted/30 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="source.field"
                    value={mapping.source}
                    onChange={(e) => updateMapping(index, 'source', e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Input
                      placeholder="target_field"
                      value={mapping.target}
                      onChange={(e) => updateMapping(index, 'target', e.target.value)}
                      className="flex-1"
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeMapping(index)}
                      disabled={config.mappings.length <= 1}
                    >
                      <Trash className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <Input
                  placeholder="변환 표현식 (선택): toUpperCase(), parseInt(), etc."
                  value={mapping.transform}
                  onChange={(e) => updateMapping(index, 'transform', e.target.value)}
                  className="text-xs"
                />
              </div>
            ))}
            <Button variant="outline" size="sm" onClick={addMapping} className="w-full">
              <Plus className="h-4 w-4 mr-2" />
              매핑 추가
            </Button>
          </div>
        )}


        {/* Template */}
        {config.transform_type === 'template' && (
          <TextareaField
            label="출력 템플릿"
            value={config.template}
            onChange={(v) => updateField('template', v)}
            placeholder={'{\n  "fullName": "{{input.firstName}} {{input.lastName}}",\n  "email": "{{input.email}}"\n}'}
            rows={8}
            mono
          />
        )}

        {/* Expression */}
        {config.transform_type === 'expression' && (
          <TextareaField
            label="변환 표현식"
            value={config.expression}
            onChange={(v) => updateField('expression', v)}
            placeholder="input.items.map(item => ({ ...item, processed: true }))"
            rows={4}
            mono
            hint="JavaScript 표현식. 'input'으로 입력 데이터에 접근"
          />
        )}

        {/* Pick/Omit/Rename Fields */}
        {(config.transform_type === 'pick' || config.transform_type === 'omit' || config.transform_type === 'rename') && (
          <TextField
            label={
              config.transform_type === 'pick' ? '유지할 필드' : 
              config.transform_type === 'omit' ? '제거할 필드' : 
              '이름 변경 (old:new)'
            }
            value={config.expression}
            onChange={(v) => updateField('expression', v)}
            placeholder={config.transform_type === 'rename' ? 'oldName:newName, field2:renamed2' : 'field1, field2, nested.field'}
          />
        )}

        {/* Output Type */}
        <SelectField
          label="출력 유형"
          value={config.output_type}
          onChange={(v) => updateField('output_type', v)}
          options={OUTPUT_TYPES.map(t => ({ value: t.value, label: t.label }))}
        />
      </div>
    </TooltipProvider>
  );
}
