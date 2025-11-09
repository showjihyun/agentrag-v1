'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Flag } from 'lucide-react';

export interface EndNodeData {
  label?: string;
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
}

export const EndNode = memo(({ data, selected }: NodeProps<EndNodeData>) => {
  const isExecuting = data?.isExecuting || false;
  const executionStatus = data?.executionStatus;

  return (
    <div
      className={`relative px-6 py-4 rounded-full border-2 shadow-lg transition-all bg-gradient-to-r from-red-400 to-rose-500 ${
        selected ? 'ring-4 ring-red-500/30 scale-110' : ''
      } ${isExecuting ? 'ring-4 ring-blue-500/50 animate-pulse' : ''}`}
    >
      {/* Execution Status Indicator */}
      {(isExecuting || executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-blue-500 rounded-full animate-pulse flex items-center justify-center">
              <div className="w-3 h-3 bg-white rounded-full animate-ping"></div>
            </div>
          )}
          {executionStatus === 'success' && (
            <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center text-white text-xs">
              ✓
            </div>
          )}
          {executionStatus === 'error' && (
            <div className="w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-white text-xs">
              ✕
            </div>
          )}
        </div>
      )}
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        id="input"
        isConnectable={true}
        className="!w-8 !h-8 !bg-red-600 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-red-400 transition-all cursor-pointer shadow-lg"
        style={{ top: -16 }}
      />

      <div className="flex items-center gap-2 text-white font-semibold">
        <Flag className="h-5 w-5" />
        <span>End</span>
      </div>
    </div>
  );
});

EndNode.displayName = 'EndNode';
