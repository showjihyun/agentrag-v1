'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { MessageCircle } from 'lucide-react';

interface DiscordNodeData {
  label: string;
  webhookUrl?: string;
  message?: string;
}

export default function DiscordNode({ data, selected }: NodeProps<DiscordNodeData>) {
  const hasConfig = data.webhookUrl && data.message;

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <MessageCircle className="w-5 h-5 text-indigo-600" />
          <span className="font-semibold text-gray-800">Discord</span>
        </div>
        
        {data.webhookUrl && (
          <div className="text-xs text-gray-600 bg-indigo-50 px-2 py-1 rounded">
            Webhook configured
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
