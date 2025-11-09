'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { GitBranch } from 'lucide-react';

export interface ConditionNodeData {
  condition?: string;
  label?: string;
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
}

export const ConditionNode = memo(({ data, selected }: NodeProps<ConditionNodeData>) => {
  const isExecuting = data.isExecuting || false;
  const executionStatus = data.executionStatus;

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-md min-w-[160px] transition-all',
        'bg-gradient-to-br from-amber-50 to-orange-50',
        selected ? 'border-amber-500 ring-2 ring-amber-500/20' : 'border-amber-300',
        isExecuting && 'ring-2 ring-blue-500/50 animate-pulse'
      )}
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
        className="!w-8 !h-8 !bg-amber-500 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-amber-300 transition-all cursor-pointer shadow-lg"
        style={{ top: -16 }}
      />

      {/* Node Content */}
      <div className="flex flex-col items-center gap-2 py-2">
        <GitBranch className="h-5 w-5 text-amber-600" />
        <div className="font-semibold text-sm text-center">
          {data.label || 'Condition'}
        </div>
        {data.condition && (
          <div className="text-xs text-muted-foreground text-center line-clamp-2">
            {data.condition}
          </div>
        )}
      </div>

      {/* Output Handles - True, Default, False */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="true"
        isConnectable={true}
        className="!w-7 !h-7 !bg-green-500 !border-3 !border-white hover:!w-9 hover:!h-9 hover:!border-green-300 transition-all cursor-pointer shadow-lg"
        style={{ bottom: -14, left: '25%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="default"
        isConnectable={true}
        className="!w-7 !h-7 !bg-amber-500 !border-3 !border-white hover:!w-9 hover:!h-9 hover:!border-amber-300 transition-all cursor-pointer shadow-lg"
        style={{ bottom: -14, left: '50%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="false"
        isConnectable={true}
        className="!w-7 !h-7 !bg-red-500 !border-3 !border-white hover:!w-9 hover:!h-9 hover:!border-red-300 transition-all cursor-pointer shadow-lg"
        style={{ bottom: -14, left: '75%' }}
      />
    </div>
  );
});

ConditionNode.displayName = 'ConditionNode';
