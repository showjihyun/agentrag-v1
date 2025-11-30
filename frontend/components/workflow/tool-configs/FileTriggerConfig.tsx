'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { FileText } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function FileTriggerConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    watch_path: data.watch_path || '',
    file_patterns: data.file_patterns || '*.*',
    events: data.events || ['created'],
    recursive: data.recursive || false,
    debounce_ms: data.debounce_ms || 500,
    max_file_size: data.max_file_size || 10,
    include_content: data.include_content || false,
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
        <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-950">
          <FileText className="h-5 w-5 text-orange-600 dark:text-orange-400" />
        </div>
        <div>
          <h3 className="font-semibold">File Trigger</h3>
          <p className="text-sm text-muted-foreground">Trigger on file upload or change</p>
        </div>
      </div>

      {/* Watch Path */}
      <div className="space-y-2">
        <Label>Watch Path</Label>
        <Input
          placeholder="/uploads or {{env.UPLOAD_DIR}}"
          value={config.watch_path}
          onChange={(e) => updateConfig('watch_path', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Directory to watch for file changes
        </p>
      </div>

      {/* File Patterns */}
      <div className="space-y-2">
        <Label>File Patterns</Label>
        <Input
          placeholder="*.pdf, *.docx, *.xlsx"
          value={config.file_patterns}
          onChange={(e) => updateConfig('file_patterns', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Comma-separated glob patterns
        </p>
      </div>

      {/* Events */}
      <div className="space-y-2">
        <Label>Trigger Events</Label>
        <div className="flex flex-wrap gap-2">
          {['created', 'modified', 'deleted', 'renamed'].map(event => (
            <label key={event} className="flex items-center gap-2 px-3 py-2 border rounded-lg cursor-pointer hover:bg-muted/50">
              <input
                type="checkbox"
                checked={config.events.includes(event)}
                onChange={(e) => {
                  if (e.target.checked) {
                    updateConfig('events', [...config.events, event]);
                  } else {
                    updateConfig('events', config.events.filter((ev: string) => ev !== event));
                  }
                }}
              />
              <span className="text-sm capitalize">{event}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Options */}
      <div className="flex items-center justify-between">
        <div>
          <Label>Recursive</Label>
          <p className="text-xs text-muted-foreground">Watch subdirectories</p>
        </div>
        <Switch
          checked={config.recursive}
          onCheckedChange={(checked) => updateConfig('recursive', checked)}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label>Include File Content</Label>
          <p className="text-xs text-muted-foreground">Pass file content to workflow</p>
        </div>
        <Switch
          checked={config.include_content}
          onCheckedChange={(checked) => updateConfig('include_content', checked)}
        />
      </div>

      {/* Debounce */}
      <div className="space-y-2">
        <Label>Debounce (ms)</Label>
        <Input
          type="number"
          min="0"
          value={config.debounce_ms}
          onChange={(e) => updateConfig('debounce_ms', parseInt(e.target.value) || 0)}
        />
        <p className="text-xs text-muted-foreground">
          Wait time before triggering (prevents duplicate triggers)
        </p>
      </div>

      {/* Max File Size */}
      <div className="space-y-2">
        <Label>Max File Size (MB)</Label>
        <Input
          type="number"
          min="1"
          value={config.max_file_size}
          onChange={(e) => updateConfig('max_file_size', parseInt(e.target.value) || 10)}
        />
      </div>
    </div>
  );
}
