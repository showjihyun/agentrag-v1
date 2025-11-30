'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Merge } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function MergeConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    merge_mode: data.merge_mode || 'wait_all',
    combine_strategy: data.combine_strategy || 'array',
    timeout: data.timeout || 60,
    min_inputs: data.min_inputs || 1,
    key_field: data.key_field || '',
    deduplicate: data.deduplicate || false,
    sort_by: data.sort_by || '',
    sort_order: data.sort_order || 'asc',
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
        <div className="p-2 rounded-lg bg-teal-100 dark:bg-teal-950">
          <Merge className="h-5 w-5 text-teal-600 dark:text-teal-400" />
        </div>
        <div>
          <h3 className="font-semibold">Merge</h3>
          <p className="text-sm text-muted-foreground">Merge multiple branches into one</p>
        </div>
      </div>

      {/* Merge Mode */}
      <div className="space-y-2">
        <Label>Merge Mode</Label>
        <Select value={config.merge_mode} onValueChange={(v) => updateConfig('merge_mode', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="wait_all">Wait for All Inputs</SelectItem>
            <SelectItem value="wait_any">Wait for Any Input</SelectItem>
            <SelectItem value="wait_n">Wait for N Inputs</SelectItem>
            <SelectItem value="pass_through">Pass Through (No Wait)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Min Inputs (for wait_n) */}
      {config.merge_mode === 'wait_n' && (
        <div className="space-y-2">
          <Label>Minimum Inputs Required</Label>
          <Input
            type="number"
            min="1"
            value={config.min_inputs}
            onChange={(e) => updateConfig('min_inputs', parseInt(e.target.value) || 1)}
          />
        </div>
      )}

      {/* Timeout */}
      {config.merge_mode !== 'pass_through' && (
        <div className="space-y-2">
          <Label>Timeout (seconds)</Label>
          <Input
            type="number"
            min="1"
            value={config.timeout}
            onChange={(e) => updateConfig('timeout', parseInt(e.target.value) || 60)}
          />
          <p className="text-xs text-muted-foreground">
            Maximum time to wait for inputs
          </p>
        </div>
      )}

      {/* Combine Strategy */}
      <div className="space-y-2">
        <Label>Combine Strategy</Label>
        <Select value={config.combine_strategy} onValueChange={(v) => updateConfig('combine_strategy', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="array">Array (collect all)</SelectItem>
            <SelectItem value="object">Object (merge by key)</SelectItem>
            <SelectItem value="concat">Concatenate Arrays</SelectItem>
            <SelectItem value="first">First Input Only</SelectItem>
            <SelectItem value="last">Last Input Only</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Key Field (for object merge) */}
      {config.combine_strategy === 'object' && (
        <div className="space-y-2">
          <Label>Key Field</Label>
          <Input
            placeholder="id or name"
            value={config.key_field}
            onChange={(e) => updateConfig('key_field', e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Field to use as key when merging objects
          </p>
        </div>
      )}

      {/* Sort */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Sort By (optional)</Label>
          <Input
            placeholder="timestamp or priority"
            value={config.sort_by}
            onChange={(e) => updateConfig('sort_by', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Sort Order</Label>
          <Select value={config.sort_order} onValueChange={(v) => updateConfig('sort_order', v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="asc">Ascending</SelectItem>
              <SelectItem value="desc">Descending</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Deduplicate */}
      <div className="flex items-center justify-between">
        <div>
          <Label>Deduplicate</Label>
          <p className="text-xs text-muted-foreground">Remove duplicate items</p>
        </div>
        <Switch
          checked={config.deduplicate}
          onCheckedChange={(checked) => updateConfig('deduplicate', checked)}
        />
      </div>
    </div>
  );
}
