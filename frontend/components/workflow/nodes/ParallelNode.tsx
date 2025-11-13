'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { GitBranch } from 'lucide-react';

export interface ParallelNodeData {
  label?: string;
  branches?: number;
  isValid?: boolean;
  validationErrors?: string[];
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
}

export const ParallelNode = memo(({ data, selected }: NodeProps<ParallelNodeData>) => {
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || false;
  const executionStatus = data.executionStatus;
  const branches = data.branches || 2;

  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-lg min-w-[180px] transition-all',
        'bg-gradient-to-br from-cyan-50 to-blue-100',
        selected ? 'border-cyan-500 ring-4 ring-cyan-500/30 scale-105' : 'border-cyan-300',
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
        className="!w-8 !h-8 !bg-cyan-500 !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-cyan-300 transition-all cursor-pointer shadow-lg"
        style={{ top: -16 }}
      />

      {/* Node Content */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-white flex-shrink-0">
          <GitBranch className="h-5 w-5" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm text-cyan-900">
            {data.label || 'Parallel'}
          </div>
          <div className="text-xs text-cyan-600 mt-0.5">
            {branches} branches
          </div>
        </div>
      </div>

      {/* Validation Errors */}
      {hasErrors && (
        <div className="mt-2 text-xs text-destructive">
          {data.validationErrors![0]}
        </div>
      )}

      {/* Output Handles - Multiple for parallel branches */}
      {Array.from({ length: branches }).map((_, index) => (
        <Handle
          key={index}
          type="source"
          position={Position.Bottom}
          id={`branch-${index}`}
          isConnectable={true}
          className="!w-6 !h-6 !bg-cyan-500 !border-3 !border-white hover:!w-8 hover:!h-8 hover:!border-cyan-300 transition-all cursor-pointer shadow-lg"
          style={{ 
            bottom: -12, 
            left: `${(100 / (branches + 1)) * (index + 1)}%`,
            transform: 'translateX(-50%)'
          }}
        />
      ))}
    </div>
  );
});

ParallelNode.displayName = 'ParallelNode';
