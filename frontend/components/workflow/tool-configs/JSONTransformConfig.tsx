'use client';

/**
 * JSONTransformConfig - JSON Transform Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Code, TestTube, Plus, Trash } from 'lucide-react';
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
  { value: 'jmespath', label: 'JMESPath Query' },
  { value: 'jsonpath', label: 'JSONPath Query' },
  { value: 'mapping', label: 'Field Mapping' },
  { value: 'template', label: 'Template' },
  { value: 'filter', label: 'Filter' },
  { value: 'flatten', label: 'Flatten' },
  { value: 'group', label: 'Group By' },
] as const;

const OUTPUT_FORMATS = [
  { value: 'object', label: 'Object' },
  { value: 'array', label: 'Array' },
  { value: 'string', label: 'JSON String' },
] as const;

// ============================================
// Types
// ============================================

interface MappingItem {
  source: string;
  target: string;
}

interface JSONTransformConfigData {
  transform_type: string;
  input: string;
  query: string;
  mappings: MappingItem[];
  template: string;
  filter_expression: string;
  group_by_field: string;
  output_format: string;
}

const DEFAULTS: JSONTransformConfigData = {
  transform_type: 'mapping',
  input: '{{input}}',
  query: '',
  mappings: [{ source: '', target: '' }],
  template: '',
  filter_expression: '',
  group_by_field: '',
  output_format: 'object',
};

// ============================================
// Component
// ============================================

export default function JSONTransformConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<JSONTransformConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const handleTest = useCallback(() => {
    onTest?.();
  }, [onTest]);

  const addMapping = useCallback(() => {
    updateField('mappings', [...config.mappings, { source: '', target: '' }]);
  }, [config.mappings, updateField]);

  const updateMapping = useCallback((index: number, field: 'source' | 'target', value: string) => {
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
          {...TOOL_HEADER_PRESETS.code}
          title="JSON Transform"
          description="JSON 데이터 변환 및 조작"
        />

        {/* Input */}
        <TextField
          label="입력 데이터"
          value={config.input}
          onChange={(v) => updateField('input', v)}
          placeholder="{{input}} or {{previous_node.output}}"
        />

        {/* Transform Type */}
        <SelectField
          label="변환 유형"
          value={config.transform_type}
          onChange={(v) => updateField('transform_type', v)}
          options={TRANSFORM_TYPES.map(t => ({ value: t.value, label: t.label }))}
        />

        {/* JMESPath / JSONPath Query */}
        {(config.transform_type === 'jmespath' || config.transform_type === 'jsonpath') && (
          <TextareaField
            label={config.transform_type === 'jmespath' ? 'JMESPath 쿼리' : 'JSONPath 쿼리'}
            value={config.query}
            onChange={(v) => updateField('query', v)}
            placeholder={config.transform_type === 'jmespath' ? 'data.items[*].name' : '$.data.items[*].name'}
            rows={3}
            mono
            hint={config.transform_type === 'jmespath' 
              ? 'JMESPath 문법으로 JSON 쿼리' 
              : 'JSONPath 문법으로 JSON 쿼리'}
          />
        )}

        {/* Field Mapping */}
        {config.transform_type === 'mapping' && (
          <div className="space-y-3">
            <Label>필드 매핑</Label>
            {config.mappings.map((mapping, index) => (
              <div key={index} className="flex gap-2 items-center">
                <Input
                  placeholder="source.field"
                  value={mapping.source}
                  onChange={(e) => updateMapping(index, 'source', e.target.value)}
                  className="flex-1"
                />
                <span className="text-muted-foreground">→</span>
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
            placeholder={'{\n  "name": "{{input.first_name}} {{input.last_name}}",\n  "email": "{{input.email}}"\n}'}
            rows={6}
            mono
          />
        )}

        {/* Filter */}
        {config.transform_type === 'filter' && (
          <TextField
            label="필터 표현식"
            value={config.filter_expression}
            onChange={(v) => updateField('filter_expression', v)}
            placeholder="item.status === 'active'"
            hint="배열 항목을 필터링하는 JavaScript 표현식"
          />
        )}

        {/* Group By */}
        {config.transform_type === 'group' && (
          <TextField
            label="그룹화 필드"
            value={config.group_by_field}
            onChange={(v) => updateField('group_by_field', v)}
            placeholder="category"
          />
        )}

        {/* Output Format */}
        <SelectField
          label="출력 형식"
          value={config.output_format}
          onChange={(v) => updateField('output_format', v)}
          options={OUTPUT_FORMATS.map(f => ({ value: f.value, label: f.label }))}
        />

        {/* Test Button */}
        {onTest && (
          <Button onClick={handleTest} variant="outline" className="w-full">
            <TestTube className="h-4 w-4 mr-2" />
            변환 테스트
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}
