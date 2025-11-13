'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Brain } from 'lucide-react';

interface MemoryNodeData {
  label: string;
  memoryType?: 'short_term' | 'long_term' | 'entity' | 'contextual';
  operation?: 'store' | 'retrieve' | 'update' | 'clear';
}

export default function MemoryNode({ data, selected }: NodeProps<MemoryNodeData>) {
  const memoryType = data.memoryType || 'short_term';
  const operation = data.operation || 'store';

  const memoryColors = {
    short_term: 'bg-blue-100 text-blue-700',
    long_term: 'bg-purple-100 text-purple-700',
    entity: 'bg-green-100 text-green-700',
    contextual: 'bg-orange-100 text-orange-700',
  };

  const memoryLabels = {
    short_term: 'STM',
    long_term: 'LTM',
    entity: 'Entity',
    contextual: 'Context',
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-5 h-5 text-pink-600" />
          <span className="font-semibold text-gray-800">Memory</span>
        </div>
        
        <div className={`text-xs px-2 py-1 rounded font-medium ${memoryColors[memoryType]}`}>
          {memoryLabels[memoryType]}
        </div>

        <div className="text-xs text-gray-500 mt-2 capitalize">
          {operation}
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
