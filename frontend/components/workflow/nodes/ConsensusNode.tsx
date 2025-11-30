'use client';

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Users } from 'lucide-react';

interface ConsensusNodeData {
  label: string;
  consensusType?: 'majority' | 'unanimous' | 'weighted' | 'best';
  agentCount?: number;
}

export default function ConsensusNode({ data, selected }: NodeProps<ConsensusNodeData>) {
  const consensusType = data.consensusType || 'majority';
  const agentCount = data.agentCount || 3;

  const consensusColors = {
    majority: 'bg-blue-100 text-blue-700',
    unanimous: 'bg-green-100 text-green-700',
    weighted: 'bg-purple-100 text-purple-700',
    best: 'bg-orange-100 text-orange-700',
  };

  const consensusLabels = {
    majority: 'Majority Vote',
    unanimous: 'Unanimous',
    weighted: 'Weighted',
    best: 'Best Result',
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-md border-2 min-w-[180px] ${
        selected ? 'border-blue-500' : 'border-gray-300'
      }`}
    >
      <Handle type="target" position={Position.Left} className="w-3 h-3" id="input" />
      
      <div className="p-4">
        <div className="flex items-center gap-2 mb-2">
          <Users className="w-5 h-5 text-teal-600" />
          <span className="font-semibold text-gray-800">Consensus</span>
        </div>
        
        <div className={`text-xs px-2 py-1 rounded font-medium ${consensusColors[consensusType]}`}>
          {consensusLabels[consensusType]}
        </div>

        <div className="text-xs text-gray-500 mt-2">
          {agentCount} agents
        </div>
      </div>

      <Handle type="source" id="output" position={Position.Right} className="w-3 h-3" />
    </div>
  );
}
