'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bot, CheckCircle, XCircle, Loader2, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

export type NodeStatus = 'idle' | 'running' | 'completed' | 'failed' | 'waiting';

interface EnhancedAgentNodeData {
  label: string;
  description?: string;
  status?: NodeStatus;
  progress?: number;
  duration?: number;
  error?: string;
}

const getStatusStyles = (status: NodeStatus) => {
  switch (status) {
    case 'running':
      return {
        border: 'border-blue-500 border-2',
        bg: 'bg-blue-50 dark:bg-blue-950/20',
        icon: <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />,
        badge: 'bg-blue-500',
      };
    case 'completed':
      return {
        border: 'border-green-500 border-2',
        bg: 'bg-green-50 dark:bg-green-950/20',
        icon: <CheckCircle className="h-4 w-4 text-green-500" />,
        badge: 'bg-green-500',
      };
    case 'failed':
      return {
        border: 'border-red-500 border-2',
        bg: 'bg-red-50 dark:bg-red-950/20',
        icon: <XCircle className="h-4 w-4 text-red-500" />,
        badge: 'bg-red-500',
      };
    case 'waiting':
      return {
        border: 'border-yellow-500 border-2',
        bg: 'bg-yellow-50 dark:bg-yellow-950/20',
        icon: <Clock className="h-4 w-4 text-yellow-500" />,
        badge: 'bg-yellow-500',
      };
    default:
      return {
        border: 'border-gray-300',
        bg: 'bg-white dark:bg-gray-950',
        icon: null,
        badge: 'bg-gray-500',
      };
  }
};

const EnhancedAgentNode = ({ data, selected }: NodeProps<EnhancedAgentNodeData>) => {
  const status = data.status || 'idle';
  const styles = getStatusStyles(status);

  return (
    <div className="relative">
      {/* Status indicator pulse effect */}
      {status === 'running' && (
        <div className="absolute inset-0 rounded-lg bg-blue-500/20 animate-ping" />
      )}
      
      <Card
        className={cn(
          'min-w-[200px] transition-all relative',
          styles.border,
          styles.bg,
          selected ? 'ring-2 ring-primary shadow-lg' : 'shadow-md',
          status === 'running' && 'animate-pulse-subtle'
        )}
      >
        {/* Progress bar */}
        {status === 'running' && data.progress !== undefined && (
          <div className="absolute top-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-800 rounded-t-lg overflow-hidden">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${data.progress}%` }}
            />
          </div>
        )}

        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-primary/10 p-2 relative">
              <Bot className="h-5 w-5 text-primary" />
              {/* Status badge overlay */}
              {styles.icon && (
                <div className="absolute -top-1 -right-1 bg-white dark:bg-gray-950 rounded-full p-0.5">
                  {styles.icon}
                </div>
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <div className="font-semibold text-sm truncate">{data.label}</div>
                {status !== 'idle' && (
                  <div className={cn('w-2 h-2 rounded-full', styles.badge)} />
                )}
              </div>
              
              {data.description && (
                <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                  {data.description}
                </p>
              )}
              
              {/* Status message */}
              {status === 'running' && (
                <p className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                  Executing...
                </p>
              )}
              {status === 'completed' && data.duration && (
                <p className="text-xs text-green-600 dark:text-green-400">
                  Completed in {(data.duration / 1000).toFixed(2)}s
                </p>
              )}
              {status === 'failed' && data.error && (
                <p className="text-xs text-red-600 dark:text-red-400 line-clamp-1" title={data.error}>
                  Error: {data.error}
                </p>
              )}
              
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  Agent
                </Badge>
                {status !== 'idle' && (
                  <Badge variant="secondary" className="text-xs capitalize">
                    {status}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </CardContent>

        {/* Input Handle */}
        <Handle
          type="target"
          position={Position.Left}
          className={cn(
            'w-3 h-3 border-2 border-background transition-colors',
            status === 'running' ? '!bg-blue-500' : '!bg-primary'
          )}
        />

        {/* Output Handle */}
        <Handle
          type="source"
          position={Position.Right}
          className={cn(
            'w-3 h-3 border-2 border-background transition-colors',
            status === 'completed' ? '!bg-green-500' :
            status === 'failed' ? '!bg-red-500' :
            status === 'running' ? '!bg-blue-500' :
            '!bg-primary'
          )}
        />
      </Card>
    </div>
  );
};

export default memo(EnhancedAgentNode);
