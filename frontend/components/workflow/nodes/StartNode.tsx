'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Play } from 'lucide-react';

export interface StartNodeData {
  label?: string;
}

export const StartNode = memo(({ selected }: NodeProps<StartNodeData>) => {
  return (
    <div
      className={`px-6 py-4 rounded-full border-2 shadow-lg transition-all bg-gradient-to-r from-green-400 to-emerald-500 ${
        selected ? 'ring-4 ring-green-500/30 scale-110' : ''
      }`}
    >
      <div className="flex items-center gap-2 text-white font-semibold">
        <Play className="h-5 w-5 fill-white" />
        <span>Start</span>
      </div>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 !bg-green-600"
        style={{ bottom: -6 }}
      />
    </div>
  );
});

StartNode.displayName = 'StartNode';
