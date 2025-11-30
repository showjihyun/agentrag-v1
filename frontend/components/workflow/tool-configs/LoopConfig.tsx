'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { RefreshCw } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function LoopConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    loop_type: data.loop_type || 'foreach',
    items: data.items || '{{input.items}}',
    count: data.count || 10,
    start: data.start || 0,
    end: data.end || 10,
    step: data.step || 1,
    condition: data.condition || '',
    max_iterations: data.max_iterations || 100,
    batch_size: data.batch_size || 1,
    parallel: data.parallel || false,
    continue_on_error: data.continue_on_error || false,
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
        <div className="p-2 rounded-lg bg-indigo-100 dark:bg-indigo-950">
          <RefreshCw className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
        </div>
        <div>
          <h3 className="font-semibold">Loop</h3>
          <p className="text-sm text-muted-foreground">Iterate over items or count</p>
        </div>
      </div>

      {/* Loop Type */}
      <div className="space-y-2">
        <Label>Loop Type</Label>
        <Select value={config.loop_type} onValueChange={(v) => updateConfig('loop_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="foreach">For Each (iterate items)</SelectItem>
            <SelectItem value="count">Count (fixed iterations)</SelectItem>
            <SelectItem value="range">Range (start to end)</SelectItem>
            <SelectItem value="while">While (condition-based)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* For Each */}
      {config.loop_type === 'foreach' && (
        <div className="space-y-2">
          <Label>Items to Iterate</Label>
          <Input
            placeholder="{{input.items}} or {{previous.data}}"
            value={config.items}
            onChange={(e) => updateConfig('items', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Array or object to iterate over. Current item available as {'{{item}}'} and index as {'{{index}}'}
          </p>
        </div>
      )}

      {/* Count */}
      {config.loop_type === 'count' && (
        <div className="space-y-2">
          <Label>Number of Iterations</Label>
          <Input
            type="number"
            min="1"
            value={config.count}
            onChange={(e) => updateConfig('count', parseInt(e.target.value) || 1)}
          />
        </div>
      )}

      {/* Range */}
      {config.loop_type === 'range' && (
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>Start</Label>
            <Input
              type="number"
              value={config.start}
              onChange={(e) => updateConfig('start', parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="space-y-2">
            <Label>End</Label>
            <Input
              type="number"
              value={config.end}
              onChange={(e) => updateConfig('end', parseInt(e.target.value) || 10)}
            />
          </div>
          <div className="space-y-2">
            <Label>Step</Label>
            <Input
              type="number"
              min="1"
              value={config.step}
              onChange={(e) => updateConfig('step', parseInt(e.target.value) || 1)}
            />
          </div>
        </div>
      )}

      {/* While */}
      {config.loop_type === 'while' && (
        <div className="space-y-2">
          <Label>Condition</Label>
          <Input
            placeholder="{{item.status}} !== 'complete'"
            value={config.condition}
            onChange={(e) => updateConfig('condition', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Loop continues while this condition is true
          </p>
        </div>
      )}

      {/* Max Iterations (safety) */}
      <div className="space-y-2">
        <Label>Max Iterations (Safety Limit)</Label>
        <Input
          type="number"
          min="1"
          max="1000"
          value={config.max_iterations}
          onChange={(e) => updateConfig('max_iterations', parseInt(e.target.value) || 100)}
        />
      </div>

      {/* Batch Size */}
      <div className="space-y-2">
        <Label>Batch Size</Label>
        <Input
          type="number"
          min="1"
          value={config.batch_size}
          onChange={(e) => updateConfig('batch_size', parseInt(e.target.value) || 1)}
        />
        <p className="text-xs text-muted-foreground">
          Process items in batches (1 = one at a time)
        </p>
      </div>

      {/* Options */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label>Parallel Execution</Label>
            <p className="text-xs text-muted-foreground">Execute iterations in parallel</p>
          </div>
          <Switch
            checked={config.parallel}
            onCheckedChange={(checked) => updateConfig('parallel', checked)}
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label>Continue on Error</Label>
            <p className="text-xs text-muted-foreground">Continue loop if an iteration fails</p>
          </div>
          <Switch
            checked={config.continue_on_error}
            onCheckedChange={(checked) => updateConfig('continue_on_error', checked)}
          />
        </div>
      </div>
    </div>
  );
}
