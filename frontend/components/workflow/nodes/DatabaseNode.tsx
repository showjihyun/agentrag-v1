'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Database } from 'lucide-react';

interface DatabaseNodeData {
  label: string;
  dbType?: 'postgresql' | 'mysql' | 'mongodb' | 'redis';
  operation?: 'query' | 'insert' | 'update' | 'delete';
}

export default function DatabaseNode({ data, selected }: NodeProps<DatabaseNodeData>) {
  const dbType = data.dbType || 'postgresql';
  const operation = data.operation || 'query';

  const dbColors = {
    postgresql: 'bg-blue-100 text-blue-700',
    mysql: 'bg-orange-100 text-orange-700',
    mongodb: 'bg-green-100 text-green-700',
    redis: 'bg-red-100 text-red-700',
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
          <Database className="w-5 h-5 text-cyan-600" />
          <span className="font-semibold text-gray-800">Database</span>
        </div>
        
        <div className={`text-xs px-2 py-1 rounded font-medium capitalize ${dbColors[dbType]}`}>
          {dbType}
        </div>

        <div className="text-xs text-gray-500 mt-2 capitalize">
          {operation}
        </div>
      </div>

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
