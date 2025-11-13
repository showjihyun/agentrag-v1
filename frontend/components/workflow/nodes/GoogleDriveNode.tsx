'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { HardDrive } from 'lucide-react';

interface GoogleDriveNodeData {
  label: string;
  action?: 'upload' | 'download' | 'list' | 'delete' | 'share';
  fileName?: string;
}

export default function GoogleDriveNode({ data, selected }: NodeProps<GoogleDriveNodeData>) {
  const action = data.action || 'upload';
  const actionLabels = {
    upload: 'Upload',
    download: 'Download',
    list: 'List Files',
    delete: 'Delete',
    share: 'Share',
  };

  const actionColors = {
    upload: 'bg-green-100 text-green-700',
    download: 'bg-blue-100 text-blue-700',
    list: 'bg-purple-100 text-purple-700',
    delete: 'bg-red-100 text-red-700',
    share: 'bg-yellow-100 text-yellow-700',
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
          <HardDrive className="w-5 h-5 text-red-600" />
          <span className="font-semibold text-gray-800">Google Drive</span>
        </div>
        
        <div className={`text-xs px-2 py-1 rounded font-medium ${actionColors[action]}`}>
          {actionLabels[action]}
        </div>

        {data.fileName && (
          <div className="text-xs text-gray-500 mt-2 truncate">
            {data.fileName}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
