'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Flag } from 'lucide-react';

export interface EndNodeData {
  label?: string;
}

export const EndNode = memo(({ selected }: NodeProps<EndNodeData>) => {
  return (
    <div
      className={`px-6 py-4 rounded-full border-2 shadow-lg transition-all bg-gradient-to-r from-red-400 to-rose-500 ${
        selected ? 'ring-4 ring-red-500/30 scale-110' : ''
      }`}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-red-600"
        style={{ top: -6 }}
      />

      <div className="flex items-center gap-2 text-white font-semibold">
        <Flag className="h-5 w-5" />
        <span>End</span>
      </div>
    </div>
  );
});

EndNode.displayName = 'EndNode';
