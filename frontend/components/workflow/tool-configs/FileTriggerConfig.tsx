'use client';

/**
 * FileTriggerConfig - File Trigger Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Label } from '@/components/ui/label';
import { FileText } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  TextField,
  NumberField,
  SwitchField,
  useToolConfig,
} from './common';

// ============================================
// Types
// ============================================

interface FileTriggerConfigData {
  watch_path: string;
  file_patterns: string;
  events: string[];
  recursive: boolean;
  debounce_ms: number;
  max_file_size: number;
  include_content: boolean;
}

const DEFAULTS: FileTriggerConfigData = {
  watch_path: '',
  file_patterns: '*.*',
  events: ['created'],
  recursive: false,
  debounce_ms: 500,
  max_file_size: 10,
  include_content: false,
};

const FILE_EVENTS = ['created', 'modified', 'deleted', 'renamed'] as const;

// ============================================
// Component
// ============================================

export default function FileTriggerConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<FileTriggerConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });


  const toggleEvent = useCallback((event: string) => {
    if (config.events.includes(event)) {
      updateField('events', config.events.filter(e => e !== event));
    } else {
      updateField('events', [...config.events, event]);
    }
  }, [config.events, updateField]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={FileText}
          {...TOOL_HEADER_PRESETS.code}
          title="File Trigger"
          description="파일 업로드 또는 변경 시 트리거"
        />

        {/* Watch Path */}
        <TextField
          label="감시 경로"
          value={config.watch_path}
          onChange={(v) => updateField('watch_path', v)}
          placeholder="/uploads or {{env.UPLOAD_DIR}}"
          hint="파일 변경을 감시할 디렉토리"
        />

        {/* File Patterns */}
        <TextField
          label="파일 패턴"
          value={config.file_patterns}
          onChange={(v) => updateField('file_patterns', v)}
          placeholder="*.pdf, *.docx, *.xlsx"
          hint="쉼표로 구분된 glob 패턴"
        />

        {/* Events */}
        <div className="space-y-2">
          <Label>트리거 이벤트</Label>
          <div className="flex flex-wrap gap-2">
            {FILE_EVENTS.map(event => (
              <label key={event} className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-muted/50">
                <input
                  type="checkbox"
                  checked={config.events.includes(event)}
                  onChange={() => toggleEvent(event)}
                />
                <span className="text-sm capitalize">{event}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Options */}
        <SwitchField
          label="재귀적"
          description="하위 디렉토리도 감시"
          checked={config.recursive}
          onChange={(v) => updateField('recursive', v)}
        />

        <SwitchField
          label="파일 내용 포함"
          description="워크플로우에 파일 내용 전달"
          checked={config.include_content}
          onChange={(v) => updateField('include_content', v)}
        />

        {/* Debounce */}
        <NumberField
          label="디바운스 (ms)"
          value={config.debounce_ms}
          onChange={(v) => updateField('debounce_ms', v)}
          min={0}
          hint="트리거 전 대기 시간 (중복 트리거 방지)"
        />

        {/* Max File Size */}
        <NumberField
          label="최대 파일 크기 (MB)"
          value={config.max_file_size}
          onChange={(v) => updateField('max_file_size', v)}
          min={1}
        />
      </div>
    </TooltipProvider>
  );
}
