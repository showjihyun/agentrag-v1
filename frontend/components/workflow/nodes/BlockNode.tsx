'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';

export interface BlockNodeData {
  type: string;
  name: string;
  description?: string;
  category: string;
  bg_color?: string;
  icon?: string;
  label?: string;
  config?: Record<string, any>;
  isValid?: boolean;
  validationErrors?: string[];
  isExecuting?: boolean;
  executionStatus?: 'success' | 'error' | 'running';
}

export const BlockNode = memo(({ data, selected }: NodeProps<BlockNodeData>) => {
  const bgColor = data.bg_color || '#6366f1';
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;
  const isExecuting = data.isExecuting || false;
  const executionStatus = data.executionStatus;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[180px] transition-all relative',
        selected ? 'border-primary ring-2 ring-primary/20' : 'border-border',
        hasErrors && 'border-destructive ring-2 ring-destructive/20',
        isExecuting && 'ring-2 ring-blue-500/50 animate-pulse'
      )}
      style={{
        backgroundColor: `${bgColor}15`,
        borderColor: selected ? bgColor : hasErrors ? 'rgb(239 68 68)' : undefined,
      }}
    >
      {/* Execution Status Indicator */}
      {(isExecuting || executionStatus) && (
        <div className="absolute -top-2 -right-2 z-10">
          {isExecuting && (
            <div className="w-5 h-5 bg-blue-500 rounded-full animate-pulse"></div>
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
        className="!w-8 !h-8 !bg-primary !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-blue-300 transition-all cursor-pointer shadow-lg"
        style={{ top: -16 }}
      />

      {/* Node Content */}
      <div className="flex items-start gap-2">
        {data.icon && (
          <div
            className="w-8 h-8 rounded flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
            style={{ backgroundColor: bgColor }}
          >
            {data.icon}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-sm truncate" title={data.label || data.name}>
            {data.label || data.name}
          </div>
          {data.description && (
            <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {data.description}
            </div>
          )}
          {data.category && (
            <div className="text-xs text-muted-foreground mt-1 capitalize">
              {data.category}
            </div>
          )}
        </div>
      </div>

      {/* Validation Errors */}
      {hasErrors && (
        <div className="mt-2 text-xs text-destructive">
          {data.validationErrors![0]}
        </div>
      )}

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        id="output"
        isConnectable={true}
        className="!w-8 !h-8 !bg-primary !border-4 !border-white hover:!w-10 hover:!h-10 hover:!border-blue-300 transition-all cursor-pointer shadow-lg"
        style={{ bottom: -16 }}
      />
    </div>
  );
});

BlockNode.displayName = 'BlockNode';
