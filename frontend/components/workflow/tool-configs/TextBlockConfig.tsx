'use client';

/**
 * TextBlockConfig - Text Block Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { FileText } from 'lucide-react';
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

const CONTENT_TYPES = [
  { value: 'text', label: 'Plain Text' },
  { value: 'json', label: 'JSON' },
  { value: 'html', label: 'HTML' },
  { value: 'markdown', label: 'Markdown' },
  { value: 'xml', label: 'XML' },
] as const;

const TEMPLATE_ENGINES = [
  { value: 'simple', label: 'Simple {{variable}}' },
  { value: 'jinja', label: 'Jinja2' },
  { value: 'handlebars', label: 'Handlebars' },
  { value: 'none', label: 'None (Static)' },
] as const;

// ============================================
// Types
// ============================================

interface TextBlockConfigData {
  content: string;
  content_type: string;
  template_engine: string;
  output_name: string;
  trim_whitespace: boolean;
}

const DEFAULTS: TextBlockConfigData = {
  content: '',
  content_type: 'text',
  template_engine: 'simple',
  output_name: 'text',
  trim_whitespace: true,
};


// ============================================
// Component
// ============================================

export default function TextBlockConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<TextBlockConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={FileText}
          iconBgColor="bg-gray-100 dark:bg-gray-950"
          iconColor="text-gray-600 dark:text-gray-400"
          title="Text Block"
          description="정적 텍스트 또는 템플릿"
        />

        {/* Content Type */}
        <SelectField
          label="콘텐츠 유형"
          value={config.content_type}
          onChange={(v) => updateField('content_type', v)}
          options={CONTENT_TYPES.map(c => ({ value: c.value, label: c.label }))}
        />

        {/* Template Engine */}
        <SelectField
          label="템플릿 엔진"
          value={config.template_engine}
          onChange={(v) => updateField('template_engine', v)}
          options={TEMPLATE_ENGINES.map(t => ({ value: t.value, label: t.label }))}
        />

        {/* Content */}
        <TextareaField
          label="콘텐츠"
          value={config.content}
          onChange={(v) => updateField('content', v)}
          placeholder={
            config.content_type === 'json'
              ? '{\n  "message": "Hello {{input.name}}"\n}'
              : 'Hello {{input.name}}, welcome to our service!'
          }
          rows={10}
          mono
          hint="{{variable}} 문법으로 동적 값 포함 가능"
        />

        {/* Output Name */}
        <TextField
          label="출력 변수명"
          value={config.output_name}
          onChange={(v) => updateField('output_name', v)}
          placeholder="text"
        />
      </div>
    </TooltipProvider>
  );
}
