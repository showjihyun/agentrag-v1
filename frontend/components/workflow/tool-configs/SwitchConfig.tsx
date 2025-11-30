'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { GitBranch, Plus, Trash } from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

export default function SwitchConfig({ data, onChange }: ToolConfigProps) {
  const [config, setConfig] = useState({
    switch_on: data.switch_on || '{{input.value}}',
    match_type: data.match_type || 'exact',
    cases: data.cases || [{ value: '', output: 'case_1' }],
    default_output: data.default_output || 'default',
    case_sensitive: data.case_sensitive !== false,
    ...data
  });

  useEffect(() => {
    onChange(config);
  }, [config]);

  const updateConfig = (key: string, value: any) => {
    setConfig((prev: typeof config) => ({ ...prev, [key]: value }));
  };

  const addCase = () => {
    const newCases = [...config.cases, { value: '', output: `case_${config.cases.length + 1}` }];
    updateConfig('cases', newCases);
  };

  const updateCase = (index: number, field: 'value' | 'output', value: string) => {
    const newCases = [...config.cases];
    newCases[index][field] = value;
    updateConfig('cases', newCases);
  };

  const removeCase = (index: number) => {
    updateConfig('cases', config.cases.filter((_: any, i: number) => i !== index));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-cyan-100 dark:bg-cyan-950">
          <GitBranch className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
        </div>
        <div>
          <h3 className="font-semibold">Switch</h3>
          <p className="text-sm text-muted-foreground">Multi-way branching based on value</p>
        </div>
      </div>

      {/* Switch On */}
      <div className="space-y-2">
        <Label>Switch On Value</Label>
        <Input
          placeholder="{{input.status}} or {{previous.type}}"
          value={config.switch_on}
          onChange={(e) => updateConfig('switch_on', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          The value to match against cases
        </p>
      </div>

      {/* Match Type */}
      <div className="space-y-2">
        <Label>Match Type</Label>
        <Select value={config.match_type} onValueChange={(v) => updateConfig('match_type', v)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="exact">Exact Match</SelectItem>
            <SelectItem value="contains">Contains</SelectItem>
            <SelectItem value="startswith">Starts With</SelectItem>
            <SelectItem value="endswith">Ends With</SelectItem>
            <SelectItem value="regex">Regular Expression</SelectItem>
            <SelectItem value="range">Numeric Range</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Cases */}
      <div className="space-y-3">
        <Label>Cases</Label>
        {config.cases.map((caseItem: any, index: number) => (
          <div key={index} className="flex gap-2 items-center p-3 border rounded-lg bg-muted/30">
            <div className="flex-1 space-y-2">
              <Input
                placeholder={config.match_type === 'range' ? 'e.g., 0-100' : 'Match value'}
                value={caseItem.value}
                onChange={(e) => updateCase(index, 'value', e.target.value)}
              />
            </div>
            <span className="text-muted-foreground">→</span>
            <div className="w-32">
              <Input
                placeholder="Output"
                value={caseItem.output}
                onChange={(e) => updateCase(index, 'output', e.target.value)}
              />
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => removeCase(index)}
              disabled={config.cases.length <= 1}
            >
              <Trash className="h-4 w-4" />
            </Button>
          </div>
        ))}
        <Button variant="outline" size="sm" onClick={addCase} className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Add Case
        </Button>
      </div>

      {/* Default Output */}
      <div className="space-y-2">
        <Label>Default Output (No Match)</Label>
        <Input
          placeholder="default"
          value={config.default_output}
          onChange={(e) => updateConfig('default_output', e.target.value)}
        />
        <p className="text-xs text-muted-foreground">
          Output when no cases match
        </p>
      </div>
    </div>
  );
}
