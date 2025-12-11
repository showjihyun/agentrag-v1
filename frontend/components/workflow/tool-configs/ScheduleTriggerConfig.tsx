'use client';

/**
 * ScheduleTriggerConfig - Schedule Trigger Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { useCallback } from 'react';
import { Clock, Calendar } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TextField,
  SelectField,
  InfoBox,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const SCHEDULE_PRESETS = [
  { value: 'every_minute', label: 'Every Minute', cron: '* * * * *' },
  { value: 'every_5_minutes', label: 'Every 5 Minutes', cron: '*/5 * * * *' },
  { value: 'every_15_minutes', label: 'Every 15 Minutes', cron: '*/15 * * * *' },
  { value: 'every_30_minutes', label: 'Every 30 Minutes', cron: '*/30 * * * *' },
  { value: 'every_hour', label: 'Every Hour', cron: '0 * * * *' },
  { value: 'every_day', label: 'Every Day at Midnight', cron: '0 0 * * *' },
  { value: 'every_week', label: 'Every Monday at 9 AM', cron: '0 9 * * 1' },
  { value: 'every_month', label: 'First Day of Month', cron: '0 0 1 * *' },
  { value: 'custom', label: 'Custom Cron Expression', cron: '' },
] as const;

const TIMEZONES = [
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'America/New_York (EST)' },
  { value: 'America/Los_Angeles', label: 'America/Los_Angeles (PST)' },
  { value: 'Europe/London', label: 'Europe/London (GMT)' },
  { value: 'Asia/Tokyo', label: 'Asia/Tokyo (JST)' },
  { value: 'Asia/Seoul', label: 'Asia/Seoul (KST)' },
] as const;

// ============================================
// Types
// ============================================

interface ScheduleTriggerConfigData {
  preset: string;
  cron: string;
  timezone: string;
}

const DEFAULTS: ScheduleTriggerConfigData = {
  preset: 'every_hour',
  cron: '0 * * * *',
  timezone: 'UTC',
};


// ============================================
// Component
// ============================================

export default function ScheduleTriggerConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField, updateFields } = useToolConfig<ScheduleTriggerConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  const handlePresetChange = useCallback((presetId: string) => {
    const preset = SCHEDULE_PRESETS.find(p => p.value === presetId);
    if (preset) {
      updateFields({
        preset: presetId,
        cron: preset.cron || config.cron,
      });
    }
  }, [config.cron, updateFields]);

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Clock}
          iconBgColor="bg-green-100 dark:bg-green-950"
          iconColor="text-green-600 dark:text-green-400"
          title="Schedule Trigger"
          description="스케줄에 따라 워크플로우 실행"
          badge="Popular"
        />

        {/* Schedule Preset */}
        <SelectField
          label="스케줄"
          value={config.preset}
          onChange={handlePresetChange}
          options={SCHEDULE_PRESETS.map(p => ({ value: p.value, label: p.label }))}
          icon={Calendar}
        />

        {/* Cron Expression */}
        <TextField
          label="Cron 표현식"
          value={config.cron}
          onChange={(v) => updateField('cron', v)}
          placeholder="* * * * *"
          mono
          hint="형식: 분 시 일 월 요일"
        />

        {/* Timezone */}
        <SelectField
          label="타임존"
          value={config.timezone}
          onChange={(v) => updateField('timezone', v)}
          options={TIMEZONES.map(t => ({ value: t.value, label: t.label }))}
        />

        {/* Cron Helper */}
        <div className="p-3 bg-muted rounded-lg space-y-2">
          <p className="text-xs font-medium">Cron 형식:</p>
          <div className="grid grid-cols-5 gap-2 text-xs">
            {['분 (0-59)', '시 (0-23)', '일 (1-31)', '월 (1-12)', '요일 (0-6)'].map((label, i) => (
              <div key={i} className="text-center">
                <div className="font-mono font-bold">*</div>
                <div className="text-muted-foreground">{label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Examples */}
        <InfoBox variant="info" title="예시:">
          <div className="space-y-1 font-mono">
            <div>• <code>0 9 * * 1-5</code> - 평일 오전 9시</div>
            <div>• <code>*/10 * * * *</code> - 10분마다</div>
            <div>• <code>0 0 1,15 * *</code> - 매월 1일, 15일</div>
          </div>
        </InfoBox>
      </div>
    </TooltipProvider>
  );
}
