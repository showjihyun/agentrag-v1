'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Send } from 'lucide-react';

interface WebhookResponseNodeData {
  label: string;
  statusCode?: number;
  headers?: Record<string, string>;
}

export default function WebhookResponseNode({
  data,
  selected,
}: NodeProps<WebhookResponseNodeData>) {
  const statusCode = data.statusCode || 200;

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />

      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Send className="w-5 h-5 text-purple-600" />
          <span className="font-semibold text-gray-800">Webhook Response</span>
        </div>

        <div className="text-sm">
          <div
            className={`inline-block px-2 py-1 rounded text-xs font-mono ${
              statusCode >= 200 && statusCode < 300
                ? 'bg-green-100 text-green-700'
                : statusCode >= 400
                ? 'bg-red-100 text-red-700'
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            {statusCode}
          </div>
        </div>

        {data.headers && Object.keys(data.headers).length > 0 && (
          <div className="text-xs text-gray-500 mt-2">
            {Object.keys(data.headers).length} header(s)
          </div>
        )}
      </div>
    </div>
  );
}
