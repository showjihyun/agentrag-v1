'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Clock, Calendar } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

const SCHEDULE_PRESETS = [
  { id: 'every_minute', name: 'Every Minute', cron: '* * * * *' },
  { id: 'every_5_minutes', name: 'Every 5 Minutes', cron: '*/5 * * * *' },
  { id: 'every_15_minutes', name: 'Every 15 Minutes', cron: '*/15 * * * *' },
  { id: 'every_30_minutes', name: 'Every 30 Minutes', cron: '*/30 * * * *' },
  { id: 'every_hour', name: 'Every Hour', cron: '0 * * * *' },
  { id: 'every_day', name: 'Every Day at Midnight', cron: '0 0 * * *' },
  { id: 'every_week', name: 'Every Monday at 9 AM', cron: '0 9 * * 1' },
  { id: 'every_month', name: 'First Day of Month', cron: '0 0 1 * *' },
  { id: 'custom', name: 'Custom Cron Expression', cron: '' },
];

export default function ScheduleTriggerConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    preset: data.preset || 'every_hour',
    cron: data.cron || '0 * * * *',
    timezone: data.timezone || 'UTC',
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const handlePresetChange = (presetId: string) => {
    const preset = SCHEDULE_PRESETS.find(p => p.id === presetId);
    if (preset) {
      setConfig(prev => ({
        ...prev,
        preset: presetId,
        cron: preset.cron || prev.cron
      }));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-green-100 dark:bg-green-950">
          <Clock className="h-5 w-5 text-green-600 dark:text-green-400" />
        </div>
        <div>
          <h3 className="font-semibold">Schedule Trigger</h3>
          <p className="text-sm text-muted-foreground">Run workflow on schedule</p>
        </div>
        <Badge variant="secondary" className="ml-auto">Popular</Badge>
      </div>

      {/* Schedule Preset */}
      <div className="space-y-2">
        <Label className="flex items-center gap-2">
          <Calendar className="h-4 w-4" />
          Schedule
        </Label>
        <Select value={config.preset} onValueChange={handlePresetChange}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {SCHEDULE_PRESETS.map(preset => (
              <SelectItem key={preset.id} value={preset.id}>
                <div className="flex flex-col">
                  <span className="font-medium">{preset.name}</span>
                  {preset.cron && (
                    <span className="text-xs text-muted-foreground font-mono">{preset.cron}</span>
                  )}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Cron Expression */}
      <div className="space-y-2">
        <Label>Cron Expression</Label>
        <Input
          value={config.cron}
          onChange={(e) => updateConfig('cron', e.target.value)}
          placeholder="* * * * *"
          className="font-mono text-sm"
          disabled={config.preset !== 'custom'}
        />
        <p className="text-xs text-muted-foreground">
          Format: minute hour day month weekday
        </p>
      </div>

      {/* Timezone */}
      <div className="space-y-2">
        <Label>Timezone</Label>
        <Select value={config.timezone} onValueChange={(v) => updateConfig('timezone', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="UTC">UTC</SelectItem>
            <SelectItem value="America/New_York">America/New_York (EST)</SelectItem>
            <SelectItem value="America/Los_Angeles">America/Los_Angeles (PST)</SelectItem>
            <SelectItem value="Europe/London">Europe/London (GMT)</SelectItem>
            <SelectItem value="Asia/Tokyo">Asia/Tokyo (JST)</SelectItem>
            <SelectItem value="Asia/Seoul">Asia/Seoul (KST)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Cron Helper */}
      <div className="p-3 bg-muted rounded-lg space-y-2">
        <p className="text-xs font-medium">Cron Format:</p>
        <div className="grid grid-cols-5 gap-2 text-xs">
          <div className="text-center">
            <div className="font-mono font-bold">*</div>
            <div className="text-muted-foreground">Minute</div>
            <div className="text-muted-foreground">(0-59)</div>
          </div>
          <div className="text-center">
            <div className="font-mono font-bold">*</div>
            <div className="text-muted-foreground">Hour</div>
            <div className="text-muted-foreground">(0-23)</div>
          </div>
          <div className="text-center">
            <div className="font-mono font-bold">*</div>
            <div className="text-muted-foreground">Day</div>
            <div className="text-muted-foreground">(1-31)</div>
          </div>
          <div className="text-center">
            <div className="font-mono font-bold">*</div>
            <div className="text-muted-foreground">Month</div>
            <div className="text-muted-foreground">(1-12)</div>
          </div>
          <div className="text-center">
            <div className="font-mono font-bold">*</div>
            <div className="text-muted-foreground">Weekday</div>
            <div className="text-muted-foreground">(0-6)</div>
          </div>
        </div>
      </div>

      {/* Examples */}
      <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className="text-xs font-medium text-blue-900 dark:text-blue-100 mb-2">Examples:</p>
        <div className="space-y-1 text-xs text-blue-700 dark:text-blue-300 font-mono">
          <div>• <code>0 9 * * 1-5</code> - Weekdays at 9 AM</div>
          <div>• <code>*/10 * * * *</code> - Every 10 minutes</div>
          <div>• <code>0 0 1,15 * *</code> - 1st and 15th of month</div>
        </div>
      </div>
    </div>
  );
}
