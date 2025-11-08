'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { cn } from '@/lib/utils';
import { Bot, Settings } from 'lucide-react';

export interface AgentNodeData {
  agentId: string;
  name: string;
  description?: string;
  type: string;
  icon?: string;
  config?: Record<string, any>;
  isValid?: boolean;
  validationErrors?: string[];
}

export const AgentNode = memo(({ data, selected }: NodeProps<AgentNodeData>) => {
  const hasErrors = data.validationErrors && data.validationErrors.length > 0;

  return (
    <div
      className={cn(
        'px-4 py-3 rounded-lg border-2 shadow-md min-w-[200px] transition-all bg-gradient-to-br from-purple-50 to-pink-50',
        selected ? 'border-purple-500 ring-2 ring-purple-500/20' : 'border-purple-300',
        hasErrors && 'border-destructive ring-2 ring-destructive/20'
      )}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 !bg-purple-500"
        style={{ top: -6 }}
      />

      {/* Node Content */}
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white flex-shrink-0">
          <Bot className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <div className="font-semibold text-sm truncate" title={data.name}>
              {data.name}
            </div>
            <Settings className="h-3 w-3 text-muted-foreground" />
          </div>
          {data.description && (
            <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
              {data.description}
            </div>
          )}
          <div className="text-xs text-purple-600 mt-1 font-medium">
            Agent
          </div>
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
        className="w-3 h-3 !bg-purple-500"
        style={{ bottom: -6 }}
      />
    </div>
  );
});

AgentNode.displayName = 'AgentNode';
