'use client';

/**
 * CSVParserConfig - CSV Parser Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { FileText, TestTube } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TextField,
  NumberField,
  SelectField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const INPUT_SOURCES = [
  { value: 'file', label: 'File Path' },
  { value: 'content', label: 'Raw CSV Content' },
  { value: 'variable', label: 'From Variable' },
] as const;

const DELIMITERS = [
  { value: ',', label: 'Comma (,)' },
  { value: ';', label: 'Semicolon (;)' },
  { value: '\t', label: 'Tab' },
  { value: '|', label: 'Pipe (|)' },
] as const;

const QUOTE_CHARS = [
  { value: '"', label: 'Double Quote (")' },
  { value: "'", label: "Single Quote (')" },
  { value: '', label: 'None' },
] as const;

const ENCODINGS = [
  { value: 'utf-8', label: 'UTF-8' },
  { value: 'utf-16', label: 'UTF-16' },
  { value: 'ascii', label: 'ASCII' },
  { value: 'euc-kr', label: 'EUC-KR (Korean)' },
  { value: 'iso-8859-1', label: 'ISO-8859-1' },
] as const;

const OUTPUT_FORMATS = [
  { value: 'array', label: 'Array of Objects' },
  { value: 'dict', label: 'Dictionary (by column)' },
  { value: 'raw', label: 'Raw 2D Array' },
] as const;

// ============================================
// Types
// ============================================

interface CSVParserConfigData {
  input_source: string;
  file_path: string;
  csv_content: string;
  delimiter: string;
  quote_char: string;
  has_header: boolean;
  skip_rows: number;
  encoding: string;
  output_format: string;
  columns: string;
}

const DEFAULTS: CSVParserConfigData = {
  input_source: 'file',
  file_path: '',
  csv_content: '',
  delimiter: ',',
  quote_char: '"',
  has_header: true,
  skip_rows: 0,
  encoding: 'utf-8',
  output_format: 'array',
  columns: '',
};

// ============================================
// Component
// ============================================

export default function CSVParserConfig({ data, onChange, onTest }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<CSVParserConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const handleTest = useCallback(() => {
    onTest?.();
  }, [onTest]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={FileText}
          iconBgColor="bg-green-100 dark:bg-green-950"
          iconColor="text-green-600 dark:text-green-400"
          title="CSV Parser"
          description="CSV 파일 및 데이터 파싱"
        />

        {/* Input Source */}
        <SelectField
          label="입력 소스"
          value={config.input_source}
          onChange={(v) => updateField('input_source', v)}
          options={INPUT_SOURCES.map(s => ({ value: s.value, label: s.label }))}
        />

        {config.input_source === 'file' && (
          <TextField
            label="파일 경로"
            value={config.file_path}
            onChange={(v) => updateField('file_path', v)}
            placeholder="/path/to/file.csv or {{input.file_path}}"
          />
        )}

        {config.input_source === 'content' && (
          <TextField
            label="CSV 내용"
            value={config.csv_content}
            onChange={(v) => updateField('csv_content', v)}
            placeholder="{{input.csv_data}}"
          />
        )}

        {/* Delimiter & Quote */}
        <div className="grid grid-cols-2 gap-4">
          <SelectField
            label="구분자"
            value={config.delimiter}
            onChange={(v) => updateField('delimiter', v)}
            options={DELIMITERS.map(d => ({ value: d.value, label: d.label }))}
          />
          <SelectField
            label="인용 문자"
            value={config.quote_char}
            onChange={(v) => updateField('quote_char', v)}
            options={QUOTE_CHARS.map(q => ({ value: q.value, label: q.label }))}
          />
        </div>

        {/* Options */}
        <SwitchField
          label="헤더 행 포함"
          description="첫 번째 행이 컬럼명을 포함"
          checked={config.has_header}
          onChange={(v) => updateField('has_header', v)}
        />

        <NumberField
          label="건너뛸 행 수"
          value={config.skip_rows}
          onChange={(v) => updateField('skip_rows', v)}
          min={0}
          hint="시작 부분에서 건너뛸 행 수"
        />

        {/* Encoding */}
        <SelectField
          label="인코딩"
          value={config.encoding}
          onChange={(v) => updateField('encoding', v)}
          options={ENCODINGS.map(e => ({ value: e.value, label: e.label }))}
        />

        {/* Output Format */}
        <SelectField
          label="출력 형식"
          value={config.output_format}
          onChange={(v) => updateField('output_format', v)}
          options={OUTPUT_FORMATS.map(f => ({ value: f.value, label: f.label }))}
        />

        {/* Specific Columns */}
        <TextField
          label="선택 컬럼 (선택사항)"
          value={config.columns}
          onChange={(v) => updateField('columns', v)}
          placeholder="col1, col2, col3 (비워두면 전체)"
        />

        {/* Test Button */}
        {onTest && (
          <Button onClick={handleTest} variant="outline" className="w-full">
            <TestTube className="h-4 w-4 mr-2" />
            파서 테스트
          </Button>
        )}
      </div>
    </TooltipProvider>
  );
}
