'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Crown } from 'lucide-react';

interface ManagerAgentNodeData {
  label: string;
  role?: string;
  subAgents?: string[];
  delegationStrategy?: 'sequential' | 'parallel' | 'priority';
}

export default function ManagerAgentNode({ data, selected }: NodeProps<ManagerAgentNodeData>) {
  const subAgentCount = data.subAgents?.length || 0;
  const strategy = data.delegationStrategy || 'sequential';

  const strategyColors = {
    sequential: 'bg-blue-100 text-blue-700',
    parallel: 'bg-green-100 text-green-700',
    priority: 'bg-purple-100 text-purple-700',
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[200px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Crown className="w-5 h-5 text-yellow-600" />
          <span className="font-semibold text-gray-800">Manager Agent</span>
        </div>
        
        {data.role && (
          <div className="text-sm text-gray-700 font-medium mb-2">
            {data.role}
          </div>
        )}

        <div className={`text-xs px-2 py-1 rounded font-medium capitalize ${strategyColors[strategy]}`}>
          {strategy} delegation
        </div>

        {subAgentCount > 0 && (
          <div className="text-xs text-gray-500 mt-2">
            Managing {subAgentCount} agent{subAgentCount > 1 ? 's' : ''}
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
