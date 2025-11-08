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
}

export const BlockNode = memo(({ data, selected }: NodeProps<BlockNodeData>) => {
  const bgColor = data.bg_color || '#6366f1';
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[180px] transition-all',
        selected ? 'border-primary ring-2 ring-primary/20' : 'border-border',
        hasErrors && 'border-destructive ring-2 ring-destructive/20'
      )}
      style={{
        backgroundColor: `${bgColor}15`,
        borderColor: selected ? bgColor : hasErrors ? 'rgb(239 68 68)' : undefined,
      }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-primary"
        style={{ top: -6 }}
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
        className="w-3 h-3 !bg-primary"
        style={{ bottom: -6 }}
      />
    </div>
  );
});

BlockNode.displayName = 'BlockNode';
