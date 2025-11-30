'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { MessageSquare } from 'lucide-react';

interface SlackNodeData {
  label: string;
  channel?: string;
  message?: string;
}

export default function SlackNode({ data, selected }: NodeProps<SlackNodeData>) {
  const hasConfig = data.channel && data.message;

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <MessageSquare className="w-5 h-5 text-purple-600" />
          <span className="font-semibold text-gray-800">Slack</span>
        </div>
        
        {data.channel && (
          <div className="text-sm text-gray-600 bg-purple-50 px-2 py-1 rounded font-mono">
            #{data.channel}
          </div>
        )}

        {!hasConfig && (
          <div className="text-xs text-gray-400 mt-2">
            Not configured
          </div>
        )}
      </div>

      <Handle type="source" id="output" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
