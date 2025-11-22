'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Wrench, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

interface ToolNodeData {
  label?: string;
  name?: string;
  description?: string;
  tool_id?: string;
  tool_name?: string;
  category?: string;
  parameters?: Record<string, any>;
  environment?: Record<string, any>;
  disabled?: boolean;
  executionStatus?: 'idle' | 'pending' | 'running' | 'success' | 'failed' | 'skipped';
  executionError?: string;
  executionOutput?: any;
}

export const ToolNode = memo(({ data, selected }: NodeProps<ToolNodeData>) => {
  const paramCount = data.parameters ? Object.keys(data.parameters).length : 0;
  const envCount = data.environment ? Object.keys(data.environment).length : 0;
  
  const getStatusClass = () => {
    switch (data.executionStatus) {
      case 'running':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/20';
      case 'success':
        return 'border-green-500 bg-green-50 dark:bg-green-950/20';
      case 'failed':
        return 'border-red-500 bg-red-50 dark:bg-red-950/20';
      case 'pending':
        return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20';
      case 'skipped':
        return 'border-gray-400 bg-gray-50 dark:bg-gray-950/20';
      default:
        return 'border-gray-300 dark:border-gray-700';
    }
  };

  return (
    <>
      <Handle type="target" position={Position.Top} className="w-3 h-3" />
      
      <Card
        className={cn(
          'min-w-[200px] max-w-[300px] transition-all',
          getStatusClass(),
          selected && 'ring-2 ring-primary',
          data.disabled && 'opacity-50 grayscale'
        )}
      >
        <div className="p-3 space-y-2">
          {/* Header */}
          <div className="flex items-start gap-2">
            <div className="p-2 rounded-lg bg-orange-100 dark:bg-orange-900/20">
              <Wrench className="h-4 w-4 text-orange-600 dark:text-orange-400" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-sm truncate">
                {data.label || data.name || 'Tool'}
              </h3>
              {data.tool_name && (
                <p className="text-xs text-muted-foreground truncate">
                  {data.tool_name}
                </p>
              )}
            </div>
            {data.executionStatus && data.executionStatus !== 'idle' && (
              <Badge
                variant={
                  data.executionStatus === 'success' ? 'default' :
                  data.executionStatus === 'failed' ? 'destructive' :
                  data.executionStatus === 'running' ? 'secondary' :
                  'outline'
                }
                className="text-xs"
              >
                {data.executionStatus}
              </Badge>
            )}
          </div>

          {/* Description */}
          {data.description && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {data.description}
            </p>
          )}

          {/* Metadata */}
          <div className="flex items-center gap-2 flex-wrap">
            {data.category && (
              <Badge variant="outline" className="text-xs">
                {data.category}
              </Badge>
            )}
            {paramCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                {paramCount} params
              </Badge>
            )}
            {envCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                {envCount} env
              </Badge>
            )}
          </div>

          {/* Error Message */}
          {data.executionError && (
            <div className="text-xs text-red-600 dark:text-red-400 line-clamp-2">
              {data.executionError}
            </div>
          )}

          {/* Disabled Badge */}
          {data.disabled && (
            <Badge variant="destructive" className="text-xs">
              Disabled
            </Badge>
          )}
        </div>
      </Card>

      <Handle type="source" position={Position.Bottom} className="w-3 h-3" />
    </>
  );
});

ToolNode.displayName = 'ToolNode';
