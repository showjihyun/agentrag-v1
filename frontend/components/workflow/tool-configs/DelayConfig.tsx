'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Clock } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function DelayConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    delay_type: data.delay_type || 'fixed',
    duration: data.duration || 5,
    unit: data.unit || 'seconds',
    until_time: data.until_time || '',
    until_date: data.until_date || '',
    random_min: data.random_min || 1,
    random_max: data.random_max || 10,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-950">
          <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
        </div>
        <div>
          <h3 className="font-semibold">Delay</h3>
          <p className="text-sm text-muted-foreground">Wait for a specified duration</p>
        </div>
      </div>

      {/* Delay Type */}
      <div className="space-y-2">
        <Label>Delay Type</Label>
        <Select value={config.delay_type} onValueChange={(v) => updateConfig('delay_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="fixed">Fixed Duration</SelectItem>
            <SelectItem value="random">Random Duration</SelectItem>
            <SelectItem value="until_time">Until Specific Time</SelectItem>
            <SelectItem value="until_datetime">Until Date & Time</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Fixed Duration */}
      {config.delay_type === 'fixed' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Duration</Label>
            <Input
              type="number"
              min="0"
              value={config.duration}
              onChange={(e) => updateConfig('duration', parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="space-y-2">
            <Label>Unit</Label>
            <Select value={config.unit} onValueChange={(v) => updateConfig('unit', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="milliseconds">Milliseconds</SelectItem>
                <SelectItem value="seconds">Seconds</SelectItem>
                <SelectItem value="minutes">Minutes</SelectItem>
                <SelectItem value="hours">Hours</SelectItem>
                <SelectItem value="days">Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}

      {/* Random Duration */}
      {config.delay_type === 'random' && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Minimum</Label>
              <Input
                type="number"
                min="0"
                value={config.random_min}
                onChange={(e) => updateConfig('random_min', parseInt(e.target.value) || 0)}
              />
            </div>
            <div className="space-y-2">
              <Label>Maximum</Label>
              <Input
                type="number"
                min="0"
                value={config.random_max}
                onChange={(e) => updateConfig('random_max', parseInt(e.target.value) || 10)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Unit</Label>
            <Select value={config.unit} onValueChange={(v) => updateConfig('unit', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="milliseconds">Milliseconds</SelectItem>
                <SelectItem value="seconds">Seconds</SelectItem>
                <SelectItem value="minutes">Minutes</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </>
      )}

      {/* Until Time */}
      {config.delay_type === 'until_time' && (
        <div className="space-y-2">
          <Label>Wait Until Time</Label>
          <Input
            type="time"
            value={config.until_time}
            onChange={(e) => updateConfig('until_time', e.target.value)}
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
              onChange={(e) => updateConfig('until_date', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Time</Label>
            <Input
              type="time"
              value={config.until_time}
              onChange={(e) => updateConfig('until_time', e.target.value)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
