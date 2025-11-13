'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Cloud } from 'lucide-react';

interface S3NodeData {
  label: string;
  action?: 'upload' | 'download' | 'list' | 'delete';
  bucket?: string;
}

export default function S3Node({ data, selected }: NodeProps<S3NodeData>) {
  const action = data.action || 'upload';

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Cloud className="w-5 h-5 text-orange-600" />
          <span className="font-semibold text-gray-800">AWS S3</span>
        </div>
        
        <div className="text-xs px-2 py-1 rounded bg-orange-100 text-orange-700 capitalize">
          {action}
        </div>

        {data.bucket && (
          <div className="text-xs text-gray-500 mt-2 truncate">
            {data.bucket}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
