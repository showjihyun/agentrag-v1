'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { RotateCw } from 'lucide-react';

export interface LoopNodeData {
  label?: string;
  loopType?: 'forEach' | 'while' | 'count';
  iterations?: number;
  condition?: string;
  isValid?: boolean;
  validationErrors?: string[];
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
}

export const LoopNode = memo(({ data, selected }: NodeProps<LoopNodeData>) => {
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || false;
  const executionStatus = data.executionStatus;

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-lg min-w-[180px] transition-all',
        'bg-gradient-to-br from-purple-50 to-violet-100',
        selected ? 'border-purple-500 ring-4 ring-purple-500/30 scale-105' : 'border-purple-300',
        hasErrors && 'border-destructive ring-2 ring-destructive/20',
        isExecuting && 'ring-4 ring-blue-500/50 animate-pulse'
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
        className="!w-8 !h-8 !bg-purple-500 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-purple-300 transition-all cursor-pointer shadow-lg"
        style={{ top: -16 }}
      />

      {/* Node Content */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-violet-600 flex items-center justify-center text-white flex-shrink-0">
          <RotateCw className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm text-purple-900">
            {data.label || 'Loop'}
          </div>
          <div className="text-xs text-purple-600 mt-0.5">
            {data.loopType === 'forEach' && 'For Each'}
            {data.loopType === 'while' && 'While'}
            {data.loopType === 'count' && `${data.iterations || 0}x`}
            {!data.loopType && 'Iterate'}
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {hasErrors && (
        <div className="mt-2 text-xs text-destructive">
          {data.validationErrors![0]}
        </div>
      )}

      {/* Output Handles */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="loop"
        isConnectable={true}
        className="!w-8 !h-8 !bg-purple-500 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-purple-300 transition-all cursor-pointer shadow-lg"
        style={{ bottom: -16, left: '30%' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="output"
        isConnectable={true}
        className="!w-8 !h-8 !bg-purple-500 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-purple-300 transition-all cursor-pointer shadow-lg"
        style={{ bottom: -16, left: '70%' }}
      />
    </div>
  );
});

LoopNode.displayName = 'LoopNode';
