'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2 } from 'lucide-react';

interface SwitchCase {
  id: string;
  condition: string;
  label: string;
}

interface SwitchNodeConfigProps {
  data: {
    variable?: string;
    cases?: SwitchCase[];
    defaultCase?: boolean;
  };
  onChange: (data: any) => void;
}

export default function SwitchNodeConfig({ data, onChange }: SwitchNodeConfigProps) {
  const [variable, setVariable] = useState(data.variable || '');
  const [cases, setCases] = useState<SwitchCase[]>(data.cases || []);
  const [defaultCase, setDefaultCase] = useState(data.defaultCase !== false);

  const handleVariableChange = (value: string) => {
    setVariable(value);
    onChange({ ...data, variable: value });
  };

  const addCase = () => {
    const newCase: SwitchCase = {
      id: `case-${Date.now()}`,
      condition: '',
      label: `Case ${cases.length + 1}`,
    };
    const newCases = [...cases, newCase];
    setCases(newCases);
    onChange({ ...data, cases: newCases });
  };

  const updateCase = (id: string, field: keyof SwitchCase, value: string) => {
    const newCases = cases.map((c) =>
      c.id === id ? { ...c, [field]: value } : c
    );
    setCases(newCases);
    onChange({ ...data, cases: newCases });
  };

  const removeCase = (id: string) => {
    const newCases = cases.filter((c) => c.id !== id);
    setCases(newCases);
    onChange({ ...data, cases: newCases });
  };

  const toggleDefaultCase = () => {
    const newValue = !defaultCase;
    setDefaultCase(newValue);
    onChange({ ...data, defaultCase: newValue });
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>Variable to Switch On</Label>
        <Input
          value={variable}
          onChange={(e) => handleVariableChange(e.target.value)}
          placeholder="e.g., {{$json.status}}"
          className="font-mono text-sm"
        />
        <p className="text-xs text-gray-500 mt-1">
          Use {'{{$json.field}}'} to reference data
        </p>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <Label>Cases</Label>
          <Button onClick={addCase} size="sm" variant="outline">
            <Plus className="w-4 h-4 mr-1" />
            Add Case
          </Button>
        </div>

        <div className="space-y-3">
          {cases.map((c, idx) => (
            <div key={c.id} className="border rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  Case {idx + 1}
                </span>
                <Button
                  onClick={() => removeCase(c.id)}
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0"
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>

              <div>
                <Label className="text-xs">Label</Label>
                <Input
                  value={c.label}
                  onChange={(e) => updateCase(c.id, 'label', e.target.value)}
                  placeholder="Case label"
                  className="text-sm"
                />
              </div>

              <div>
                <Label className="text-xs">Condition</Label>
                <Input
                  value={c.condition}
                  onChange={(e) => updateCase(c.id, 'condition', e.target.value)}
                  placeholder="e.g., === 'active' or > 100"
                  className="font-mono text-sm"
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id="defaultCase"
          checked={defaultCase}
          onChange={toggleDefaultCase}
          className="rounded"
        />
        <Label htmlFor="defaultCase" className="cursor-pointer">
          Include default case (fallback)
        </Label>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
        <p className="text-xs text-blue-800">
          <strong>How it works:</strong> The switch node evaluates the variable
          against each case condition in order. The first matching case's output
          is used. If no cases match and default is enabled, the default output
          is used.
        </p>
      </div>
    </div>
  );
}
