'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Code2 } from 'lucide-react';

interface CodeNodeData {
  label: string;
  language?: 'python' | 'javascript';
  code?: string;
}

export default function CodeNode({ data, selected }: NodeProps<CodeNodeData>) {
  const language = data.language || 'javascript';
  const hasCode = data.code && data.code.trim().length > 0;

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Code2 className="w-5 h-5 text-green-600" />
          <span className="font-semibold text-gray-800">Code</span>
        </div>
        
        <div className="flex items-center gap-2">
          <div className={`text-xs px-2 py-1 rounded font-mono ${
            language === 'python' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-yellow-100 text-yellow-700'
          }`}>
            {language === 'python' ? 'Python' : 'JavaScript'}
          </div>
          
          {hasCode && (
            <div className="text-xs text-green-600">
              ✓ Code set
            </div>
          )}
        </div>

        {!hasCode && (
          <div className="text-xs text-gray-400 mt-2">
            No code configured
          </div>
        )}
      </div>

      <Handle type="source" id="output" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
