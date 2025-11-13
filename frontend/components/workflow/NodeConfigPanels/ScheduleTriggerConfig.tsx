'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface ScheduleTriggerConfigProps {
  data: {
    cronExpression?: string;
    timezone?: string;
    enabled?: boolean;
  };
  onChange: (data: any) => void;
}

const CRON_PRESETS = [
  { label: 'Every minute', value: '* * * * *' },
  { label: 'Every 5 minutes', value: '*/5 * * * *' },
  { label: 'Every 15 minutes', value: '*/15 * * * *' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every day at midnight', value: '0 0 * * *' },
  { label: 'Every day at 9 AM', value: '0 9 * * *' },
  { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
  { label: 'First day of month', value: '0 0 1 * *' },
];

export default function ScheduleTriggerConfig({ data, onChange }: ScheduleTriggerConfigProps) {
  const [cronExpression, setCronExpression] = useState(data.cronExpression || '0 * * * *');
  const [timezone, setTimezone] = useState(data.timezone || 'UTC');
  const [enabled, setEnabled] = useState(data.enabled !== false);

  const handleCronChange = (value: string) => {
    setCronExpression(value);
    onChange({ ...data, cronExpression: value });
  };

  const handleTimezoneChange = (value: string) => {
    setTimezone(value);
    onChange({ ...data, timezone: value });
  };

  const handleEnabledChange = (value: boolean) => {
    setEnabled(value);
    onChange({ ...data, enabled: value });
  };

  const applyPreset = (preset: string) => {
    setCronExpression(preset);
    onChange({ ...data, cronExpression: preset });
  };

  const parseCron = (cron: string) => {
    const parts = cron.split(' ');
    if (parts.length !== 5) return 'Invalid cron expression';

    const [minute, hour, dayOfMonth, month, dayOfWeek] = parts;
    
    let description = 'Runs ';
    
    if (minute === '*' && hour === '*') {
      description += 'every minute';
    } else if (minute.startsWith('*/')) {
      description += `every ${minute.slice(2)} minutes`;
    } else if (hour === '*') {
      description += `at minute ${minute} of every hour`;
    } else if (dayOfMonth === '*' && month === '*' && dayOfWeek === '*') {
      description += `daily at ${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;
    } else if (dayOfWeek !== '*') {
      const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
      description += `every ${days[parseInt(dayOfWeek)] || dayOfWeek} at ${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;
    } else if (dayOfMonth !== '*') {
      description += `on day ${dayOfMonth} at ${hour.padStart(2, '0')}:${minute.padStart(2, '0')}`;
    } else {
      description += 'with custom schedule';
    }

    return description;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="enabled"
          checked={enabled}
          onChange={(e) => handleEnabledChange(e.target.checked)}
          className="rounded"
        />
        <Label htmlFor="enabled" className="cursor-pointer">
          Schedule Enabled
        </Label>
      </div>

      <div>
        <Label>Cron Expression</Label>
        <Input
          value={cronExpression}
          onChange={(e) => handleCronChange(e.target.value)}
          placeholder="0 * * * *"
          className="font-mono"
        />
        <p className="text-xs text-gray-500 mt-1">
          Format: minute hour day month weekday
        </p>
        <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
          {parseCron(cronExpression)}
        </div>
      </div>

      <div>
        <Label>Quick Presets</Label>
        <div className="grid grid-cols-2 gap-2 mt-2">
          {CRON_PRESETS.map((preset) => (
            <Button
              key={preset.value}
              onClick={() => applyPreset(preset.value)}
              variant="outline"
              size="sm"
              className="text-xs justify-start"
            >
              {preset.label}
            </Button>
          ))}
        </div>
      </div>

      <div>
        <Label>Timezone</Label>
        <select
          value={timezone}
          onChange={(e) => handleTimezoneChange(e.target.value)}
          className="w-full p-2 border rounded-lg text-sm"
        >
          <option value="UTC">UTC</option>
          <option value="Asia/Seoul">Asia/Seoul (KST)</option>
          <option value="America/New_York">America/New_York (EST)</option>
          <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
          <option value="Europe/London">Europe/London (GMT)</option>
          <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
        </select>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <p className="text-xs text-purple-800 font-medium mb-2">
          Cron Expression Guide:
        </p>
        <div className="text-xs text-purple-700 space-y-1 font-mono">
          <div>* * * * * = minute hour day month weekday</div>
          <div>* = any value</div>
          <div>*/5 = every 5 units</div>
          <div>1,2,3 = specific values</div>
          <div>1-5 = range of values</div>
        </div>
      </div>
    </div>
  );
}
