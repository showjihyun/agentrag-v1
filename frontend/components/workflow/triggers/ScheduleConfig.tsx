"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Clock } from 'lucide-react';

interface ScheduleConfigProps {
  workflowId: string;
  onTriggerCreated?: (trigger: any) => void;
}

const CRON_PRESETS = [
  { label: 'Every minute', value: '* * * * *' },
  { label: 'Every 5 minutes', value: '*/5 * * * *' },
  { label: 'Every 15 minutes', value: '*/15 * * * *' },
  { label: 'Every 30 minutes', value: '*/30 * * * *' },
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every day at midnight', value: '0 0 * * *' },
  { label: 'Every day at 9 AM', value: '0 9 * * *' },
  { label: 'Every Monday at 9 AM', value: '0 9 * * 1' },
  { label: 'Custom', value: 'custom' },
];

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
];

export function ScheduleConfig({ workflowId, onTriggerCreated }: ScheduleConfigProps) {
  const [preset, setPreset] = useState<string>('0 * * * *');
  const [cronExpression, setCronExpression] = useState<string>('0 * * * *');
  const [timezone, setTimezone] = useState<string>('UTC');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scheduleCreated, setScheduleCreated] = useState(false);
  const [nextExecution, setNextExecution] = useState<string | null>(null);

  const handlePresetChange = (value: string) => {
    setPreset(value);
    if (value !== 'custom') {
      setCronExpression(value);
    }
  };

  const handleCreateSchedule = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/agent-builder/workflows/${workflowId}/triggers/schedule`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          cron_expression: cronExpression,
          timezone: timezone,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create schedule');
      }

      const data = await response.json();
      setScheduleCreated(true);
      setNextExecution(data.next_execution_at);

      if (onTriggerCreated) {
        onTriggerCreated(data);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="preset">Schedule Preset</Label>
        <Select value={preset} onValueChange={handlePresetChange}>
          <SelectTrigger id="preset">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {CRON_PRESETS.map((p) => (
              <SelectItem key={p.value} value={p.value}>
                {p.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label htmlFor="cron-expression">Cron Expression</Label>
        <Input
          id="cron-expression"
          value={cronExpression}
          onChange={(e) => setCronExpression(e.target.value)}
          placeholder="0 * * * *"
          className="font-mono"
          disabled={preset !== 'custom'}
        />
        <p className="text-sm text-muted-foreground">
          Format: minute hour day month weekday
        </p>
      </div>

      <div className="space-y-2">
        <Label htmlFor="timezone">Timezone</Label>
        <Select value={timezone} onValueChange={setTimezone}>
          <SelectTrigger id="timezone">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {TIMEZONES.map((tz) => (
              <SelectItem key={tz} value={tz}>
                {tz}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!scheduleCreated ? (
        <Button
          onClick={handleCreateSchedule}
          disabled={isLoading || !cronExpression}
          className="w-full"
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Create Schedule
        </Button>
      ) : (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            Schedule created successfully!
            {nextExecution && (
              <div className="mt-2">
                Next execution: {new Date(nextExecution).toLocaleString()}
              </div>
            )}
          </AlertDescription>
        </Alert>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
