'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { GitBranch } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function ParallelConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    max_concurrency: data.max_concurrency || 5,
    wait_for_all: data.wait_for_all !== false,
    timeout: data.timeout || 60,
    fail_fast: data.fail_fast || false,
    collect_results: data.collect_results !== false,
    result_order: data.result_order || 'completion',
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
        <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950">
          <GitBranch className="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h3 className="font-semibold">Parallel</h3>
          <p className="text-sm text-muted-foreground">Execute branches in parallel</p>
        </div>
      </div>

      {/* Max Concurrency */}
      <div className="space-y-2">
        <Label>Max Concurrency</Label>
        <Input
          type="number"
          min="1"
          max="20"
          value={config.max_concurrency}
          onChange={(e) => updateConfig('max_concurrency', parseInt(e.target.value) || 5)}
        />
        <p className="text-xs text-muted-foreground">
          Maximum number of branches to execute simultaneously
        </p>
      </div>

      {/* Timeout */}
      <div className="space-y-2">
        <Label>Timeout (seconds)</Label>
        <Input
          type="number"
          min="1"
          max="3600"
          value={config.timeout}
          onChange={(e) => updateConfig('timeout', parseInt(e.target.value) || 60)}
        />
        <p className="text-xs text-muted-foreground">
          Maximum time to wait for all branches to complete
        </p>
      </div>

      {/* Result Order */}
      <div className="space-y-2">
        <Label>Result Order</Label>
        <Select value={config.result_order} onValueChange={(v) => updateConfig('result_order', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="completion">Completion Order</SelectItem>
            <SelectItem value="definition">Definition Order</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          How to order results from parallel branches
        </p>
      </div>

      {/* Options */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Wait for All</Label>
            <p className="text-xs text-muted-foreground">Wait for all branches to complete</p>
          </div>
          <Switch
            checked={config.wait_for_all}
            onCheckedChange={(checked) => updateConfig('wait_for_all', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Fail Fast</Label>
            <p className="text-xs text-muted-foreground">Stop all branches if one fails</p>
          </div>
          <Switch
            checked={config.fail_fast}
            onCheckedChange={(checked) => updateConfig('fail_fast', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Collect Results</Label>
            <p className="text-xs text-muted-foreground">Combine results from all branches</p>
          </div>
          <Switch
            checked={config.collect_results}
            onCheckedChange={(checked) => updateConfig('collect_results', checked)}
          />
        </div>
      </div>
    </div>
  );
}
