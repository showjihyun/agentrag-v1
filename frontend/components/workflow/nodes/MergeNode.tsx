'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Merge } from 'lucide-react';

interface MergeNodeData {
  label: string;
  mode?: 'wait_all' | 'first' | 'any';
  inputCount?: number;
}

export default function MergeNode({ data, selected }: NodeProps<MergeNodeData>) {
  const mode = data.mode || 'wait_all';
  const inputCount = data.inputCount || 2;

  const modeLabels = {
    wait_all: 'Wait for All',
    first: 'First Complete',
    any: 'Any Complete',
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      {/* Dynamic input handles */}
      {Array.from({ length: inputCount }).map((_, idx) => (
        <Handle
          key={`input-${idx}`}
          type="target"
          position={Position.Left}
          id={`input-${idx}`}
          style={{
            top: `${((idx + 1) / (inputCount + 1)) * 100}%`,
          }}
          className="w-3 h-3"
        />
      ))}
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Merge className="w-5 h-5 text-indigo-600" />
          <span className="font-semibold text-gray-800">Merge</span>
        </div>
        
        <div className="text-xs text-gray-600 bg-indigo-50 px-2 py-1 rounded">
          {modeLabels[mode]}
        </div>

        <div className="text-xs text-gray-400 mt-1">
          {inputCount} inputs
        </div>
      </div>

      <Handle type="source" id="output" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
