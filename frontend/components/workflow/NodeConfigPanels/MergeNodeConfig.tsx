'use client';

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface MergeNodeConfigProps {
  data: {
    mode?: 'wait_all' | 'first' | 'any';
    inputCount?: number;
  };
  onChange: (data: any) => void;
}

export default function MergeNodeConfig({ data, onChange }: MergeNodeConfigProps) {
  const [mode, setMode] = useState(data.mode || 'wait_all');
  const [inputCount, setInputCount] = useState(data.inputCount || 2);

  const handleModeChange = (newMode: 'wait_all' | 'first' | 'any') => {
    setMode(newMode);
    onChange({ ...data, mode: newMode });
  };

  const handleInputCountChange = (value: string) => {
    const count = parseInt(value) || 2;
    const validCount = Math.max(2, Math.min(10, count));
    setInputCount(validCount);
    onChange({ ...data, inputCount: validCount });
  };

  return (
    <div className="space-y-4">
      <div>
        <Label>Merge Mode</Label>
        <div className="space-y-2 mt-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="wait_all"
              checked={mode === 'wait_all'}
              onChange={() => handleModeChange('wait_all')}
              className="text-blue-600"
            />
            <div>
              <div className="font-medium text-sm">Wait for All</div>
              <div className="text-xs text-gray-500">
                Wait until all inputs complete before proceeding
              </div>
            </div>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="first"
              checked={mode === 'first'}
              onChange={() => handleModeChange('first')}
              className="text-blue-600"
            />
            <div>
              <div className="font-medium text-sm">First Complete</div>
              <div className="text-xs text-gray-500">
                Proceed as soon as the first input completes
              </div>
            </div>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="mode"
              value="any"
              checked={mode === 'any'}
              onChange={() => handleModeChange('any')}
              className="text-blue-600"
            />
            <div>
              <div className="font-medium text-sm">Any Complete</div>
              <div className="text-xs text-gray-500">
                Proceed when any input completes (allows multiple triggers)
              </div>
            </div>
          </label>
        </div>
      </div>

      <div>
        <Label>Number of Inputs</Label>
        <Input
          type="number"
          min="2"
          max="10"
          value={inputCount}
          onChange={(e) => handleInputCountChange(e.target.value)}
          className="w-24"
        />
        <p className="text-xs text-gray-500 mt-1">
          Between 2 and 10 inputs
        </p>
      </div>

      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
        <p className="text-xs text-indigo-800">
          <strong>Tip:</strong> Use merge nodes to synchronize parallel branches
          or to implement race conditions between different execution paths.
        </p>
      </div>
    </div>
  );
}
