'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Mail } from 'lucide-react';

interface EmailNodeData {
  label: string;
  to?: string[];
  subject?: string;
  bodyType?: 'text' | 'html';
}

export default function EmailNode({ data, selected }: NodeProps<EmailNodeData>) {
  const hasConfig = data.to && data.to.length > 0 && data.subject;
  const recipientCount = data.to?.length || 0;

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Mail className="w-5 h-5 text-blue-600" />
          <span className="font-semibold text-gray-800">Email</span>
        </div>
        
        {hasConfig ? (
          <div className="space-y-1">
            <div className="text-xs text-gray-600">
              To: {recipientCount} recipient{recipientCount > 1 ? 's' : ''}
            </div>
            <div className="text-xs text-gray-500 bg-blue-50 px-2 py-1 rounded truncate">
              {data.subject}
            </div>
            <div className="text-xs text-gray-400">
              {data.bodyType === 'html' ? 'HTML' : 'Text'}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400">
            Not configured
          </div>
        )}
      </div>

      <Handle type="source" id="output" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
