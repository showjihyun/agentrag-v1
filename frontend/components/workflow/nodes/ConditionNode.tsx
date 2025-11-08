'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { GitBranch } from 'lucide-react';

export interface ConditionNodeData {
  condition?: string;
  label?: string;
}

export const ConditionNode = memo(({ data, selected }: NodeProps<ConditionNodeData>) => {
  return (
    <div
      className={cn(
        'relative px-4 py-3 rounded-lg border-2 shadow-md min-w-[160px] transition-all',
        'bg-gradient-to-br from-amber-50 to-orange-50',
        selected ? 'border-amber-500 ring-2 ring-amber-500/20' : 'border-amber-300'
      )}
      style={{
        clipPath: 'polygon(10% 0%, 90% 0%, 100% 50%, 90% 100%, 10% 100%, 0% 50%)',
      }}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-amber-500"
        style={{ top: -6 }}
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

      {/* Output Handles - True and False */}
      <Handle
        type="source"
        position={Position.Right}
        id="true"
        className="w-3 h-3 !bg-green-500"
        style={{ right: -6, top: '30%' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="false"
        className="w-3 h-3 !bg-red-500"
        style={{ right: -6, top: '70%' }}
      />
    </div>
  );
});

ConditionNode.displayName = 'ConditionNode';
