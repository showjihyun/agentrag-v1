'use client';

/**
 * DelayConfig - Delay/Wait Tool Configuration
 * 
 * Refactored to use common hooks and components
 */

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Clock } from 'lucide-react';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ToolConfigProps } from './ToolConfigRegistry';
import {
  ToolConfigHeader,
  TOOL_HEADER_PRESETS,
  NumberField,
  SelectField,
  useToolConfig,
} from './common';

// ============================================
// Constants
// ============================================

const DELAY_TYPES = [
  { value: 'fixed', label: 'Fixed Duration' },
  { value: 'random', label: 'Random Duration' },
  { value: 'until_time', label: 'Until Specific Time' },
  { value: 'until_datetime', label: 'Until Date & Time' },
] as const;

const TIME_UNITS = [
  { value: 'milliseconds', label: 'Milliseconds' },
  { value: 'seconds', label: 'Seconds' },
  { value: 'minutes', label: 'Minutes' },
  { value: 'hours', label: 'Hours' },
  { value: 'days', label: 'Days' },
] as const;

const SHORT_TIME_UNITS = [
  { value: 'milliseconds', label: 'Milliseconds' },
  { value: 'seconds', label: 'Seconds' },
  { value: 'minutes', label: 'Minutes' },
] as const;

// ============================================
// Types
// ============================================

interface DelayConfigData {
  delay_type: string;
  duration: number;
  unit: string;
  until_time: string;
  until_date: string;
  random_min: number;
  random_max: number;
}

const DEFAULTS: DelayConfigData = {
  delay_type: 'fixed',
  duration: 5,
  unit: 'seconds',
  until_time: '',
  until_date: '',
  random_min: 1,
  random_max: 10,
};

// ============================================
// Component
// ============================================

export default function DelayConfig({ data, onChange }: ToolConfigProps) {
  const { config, updateField } = useToolConfig<DelayConfigData>({
    initialData: data,
    defaults: DEFAULTS,
    onChange,
  });

  return (
    <TooltipProvider>
      <div className="space-y-6">
        {/* Header */}
        <ToolConfigHeader
          icon={Clock}
          {...TOOL_HEADER_PRESETS.trigger}
          title="Delay"
          description="Wait for a specified duration"
        />

        {/* Delay Type */}
        <SelectField
          label="Delay Type"
          value={config.delay_type}
          onChange={(v) => updateField('delay_type', v)}
          options={DELAY_TYPES.map(t => ({ value: t.value, label: t.label }))}
        />

        {/* Fixed Duration */}
        {config.delay_type === 'fixed' && (
          <div className="grid grid-cols-2 gap-4">
            <NumberField
              label="Duration"
              value={config.duration}
              onChange={(v) => updateField('duration', v)}
              min={0}
            />
            <SelectField
              label="Unit"
              value={config.unit}
              onChange={(v) => updateField('unit', v)}
              options={TIME_UNITS.map(u => ({ value: u.value, label: u.label }))}
            />
          </div>
        )}

        {/* Random Duration */}
        {config.delay_type === 'random' && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <NumberField
                label="Minimum"
                value={config.random_min}
                onChange={(v) => updateField('random_min', v)}
                min={0}
              />
              <NumberField
                label="Maximum"
                value={config.random_max}
                onChange={(v) => updateField('random_max', v)}
                min={0}
              />
            </div>
            <SelectField
              label="Unit"
              value={config.unit}
              onChange={(v) => updateField('unit', v)}
              options={SHORT_TIME_UNITS.map(u => ({ value: u.value, label: u.label }))}
            />
          </>
        )}

        {/* Until Time */}
        {config.delay_type === 'until_time' && (
          <div className="space-y-2">
            <Label>Wait Until Time</Label>
            <Input
              type="time"
              value={config.until_time}
              onChange={(e) => updateField('until_time', e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Wait until this time today (or tomorrow if time has passed)
            </p>
          </div>
        )}

        {/* Until DateTime */}
        {config.delay_type === 'until_datetime' && (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Date</Label>
              <Input
                type="date"
                value={config.until_date}
                onChange={(e) => updateField('until_date', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Time</Label>
              <Input
                type="time"
                value={config.until_time}
                onChange={(e) => updateField('until_time', e.target.value)}
              />
            </div>
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
