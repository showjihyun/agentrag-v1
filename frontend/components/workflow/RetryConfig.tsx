'use client';

import React from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Info } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface RetryConfigProps {
  data: any;
  onChange: (field: string, value: any) => void;
}

export function RetryConfig({ data, onChange }: RetryConfigProps) {
  const retryEnabled = data.retryEnabled !== false; // Default to true
  const maxRetries = data.maxRetries || 3;
  const retryDelay = data.retryDelay || 1;
  const retryBackoff = data.retryBackoff || 'exponential';

  return (
    <div className="space-y-4 pt-4 border-t">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Label htmlFor="retryEnabled">Enable Retry</Label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs text-xs">
                  Automatically retry failed node executions with configurable backoff strategy
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        <Switch
          id="retryEnabled"
          checked={retryEnabled}
          onCheckedChange={(checked) => onChange('retryEnabled', checked)}
        />
      </div>

      {retryEnabled && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label htmlFor="maxRetries">Max Retries</Label>
              <Input
                id="maxRetries"
                type="number"
                value={maxRetries}
                onChange={(e) => onChange('maxRetries', parseInt(e.target.value) || 3)}
                min={1}
                max={10}
              />
            </div>

            <div>
              <Label htmlFor="retryDelay">Initial Delay (s)</Label>
              <Input
                id="retryDelay"
                type="number"
                value={retryDelay}
                onChange={(e) => onChange('retryDelay', parseFloat(e.target.value) || 1)}
                min={0.1}
                max={60}
                step={0.1}
              />
            </div>
          </div>

          <div>
            <Label htmlFor="retryBackoff">Backoff Strategy</Label>
            <Select
              value={retryBackoff}
              onValueChange={(value) => onChange('retryBackoff', value)}
            >
              <SelectTrigger id="retryBackoff">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="exponential">
                  Exponential (1s, 2s, 4s, 8s...)
                </SelectItem>
                <SelectItem value="linear">
                  Linear (1s, 2s, 3s, 4s...)
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
            <strong>Example:</strong> With {maxRetries} retries, {retryDelay}s delay, and{' '}
            {retryBackoff} backoff:
            <br />
            {retryBackoff === 'exponential' ? (
              <>
                Attempt 1 → Wait {retryDelay}s → Attempt 2 → Wait {retryDelay * 2}s → Attempt 3
                {maxRetries > 2 && ` → Wait ${retryDelay * 4}s → ...`}
              </>
            ) : (
              <>
                Attempt 1 → Wait {retryDelay}s → Attempt 2 → Wait {retryDelay * 2}s → Attempt 3
                {maxRetries > 2 && ` → Wait ${retryDelay * 3}s → ...`}
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
