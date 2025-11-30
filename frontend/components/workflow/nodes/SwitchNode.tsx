'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch } from 'lucide-react';

interface SwitchNodeData {
  label: string;
  variable?: string;
  cases?: Array<{
    id: string;
    condition: string;
    label: string;
  }>;
  defaultCase?: boolean;
}

export default function SwitchNode({ data, selected }: NodeProps<SwitchNodeData>) {
  const cases = data.cases || [];
  const hasDefault = data.defaultCase !== false;
  const totalOutputs = cases.length + (hasDefault ? 1 : 0);

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[200px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <GitBranch className="w-5 h-5 text-purple-600" />
          <span className="font-semibold text-gray-800">Switch</span>
        </div>
        
        <div className="text-sm text-gray-600">
          {data.variable ? (
            <div className="font-mono bg-gray-100 px-2 py-1 rounded">
              {data.variable}
            </div>
          ) : (
            <span className="text-gray-400">No variable set</span>
          )}
        </div>

        {cases.length > 0 && (
          <div className="mt-2 space-y-1">
            {cases.map((c, idx) => (
              <div key={c.id} className="text-xs text-gray-500 flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-purple-400" />
                {c.label || c.condition}
              </div>
            ))}
            {hasDefault && (
              <div className="text-xs text-gray-500 flex items-center gap-1">
                <div className="w-2 h-2 rounded-full bg-gray-400" />
                Default
              </div>
            )}
          </div>
        )}
      </div>

      {/* Dynamic output handles based on cases */}
      {cases.map((c, idx) => (
        <Handle
          key={c.id}
          type="source"
          position={Position.Right}
          id={c.id}
          style={{
            top: `${((idx + 1) / (totalOutputs + 1)) * 100}%`,
            background: '#a855f7',
          }}
          className="w-3 h-3"
        />
      ))}
      
      {hasDefault && (
        <Handle
          type="source"
          position={Position.Right}
          id="default"
          style={{
            top: `${((cases.length + 1) / (totalOutputs + 1)) * 100}%`,
            background: '#9ca3af',
          }}
          className="w-3 h-3"
        />
      )}
    </div>
  );
}
