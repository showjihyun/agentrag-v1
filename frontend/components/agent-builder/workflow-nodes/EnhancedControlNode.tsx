'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, Repeat, Layers, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { NodeStatus } from './EnhancedAgentNode';

interface EnhancedControlNodeData {
  label: string;
  controlType: 'conditional' | 'loop' | 'parallel';
  condition?: string;
  status?: NodeStatus;
  branchTaken?: 'true' | 'false' | null;
}

const getControlIcon = (controlType: string) => {
  switch (controlType) {
    case 'conditional':
      return <GitBranch className="h-5 w-5 text-yellow-500" />;
    case 'loop':
      return <Repeat className="h-5 w-5 text-green-500" />;
    case 'parallel':
      return <Layers className="h-5 w-5 text-purple-500" />;
    default:
      return <GitBranch className="h-5 w-5 text-muted-foreground" />;
  }
};

const getControlColor = (controlType: string) => {
  switch (controlType) {
    case 'conditional':
      return 'bg-yellow-500/10';
    case 'loop':
      return 'bg-green-500/10';
    case 'parallel':
      return 'bg-purple-500/10';
    default:
      return 'bg-muted/10';
  }
};

const getStatusStyles = (status: NodeStatus) => {
  switch (status) {
    case 'running':
      return {
        border: 'border-blue-500 border-2',
        bg: 'bg-blue-50 dark:bg-blue-950/20',
      };
    case 'completed':
      return {
        border: 'border-green-500 border-2',
        bg: 'bg-green-50 dark:bg-green-950/20',
      };
    case 'failed':
      return {
        border: 'border-red-500 border-2',
        bg: 'bg-red-50 dark:bg-red-950/20',
      };
    default:
      return {
        border: 'border-gray-300',
        bg: 'bg-white dark:bg-gray-950',
      };
  }
};

const EnhancedControlNode = ({ data, selected }: NodeProps<EnhancedControlNodeData>) => {
  const status = data.status || 'idle';
  const styles = getStatusStyles(status);

  return (
    <div className="relative">
      {status === 'running' && (
        <div className="absolute inset-0 rounded-lg bg-blue-500/20 animate-ping" />
      )}
      
      <Card
        className={cn(
          'min-w-[200px] transition-all relative',
          styles.border,
          styles.bg,
          selected ? 'ring-2 ring-primary shadow-lg' : 'shadow-md'
        )}
      >
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className={cn('rounded-full p-2 relative', getControlColor(data.controlType))}>
              {getControlIcon(data.controlType)}
              {status === 'running' && (
                <div className="absolute -top-1 -right-1 bg-white dark:bg-gray-950 rounded-full p-0.5">
                  <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />
                </div>
              )}
              {status === 'completed' && (
                <div className="absolute -top-1 -right-1 bg-white dark:bg-gray-950 rounded-full p-0.5">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                </div>
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-sm mb-1 truncate">{data.label}</div>
              
              {data.condition && (
                <p className="text-xs text-muted-foreground font-mono line-clamp-2 mb-2">
                  {data.condition}
                </p>
              )}
              
              {/* Branch taken indicator */}
              {data.controlType === 'conditional' && data.branchTaken && (
                <p className="text-xs font-medium mb-2">
                  <span className={cn(
                    'px-2 py-0.5 rounded',
                    data.branchTaken === 'true' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                    'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  )}>
                    Branch: {data.branchTaken}
                  </span>
                </p>
              )}
              
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="outline" className="text-xs capitalize">
                  {data.controlType}
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

        {/* Output Handles */}
        {data.controlType === 'conditional' || data.controlType === 'parallel' ? (
          <>
            <Handle
              type="source"
              position={Position.Right}
              id="true"
              className={cn(
                'w-3 h-3 border-2 border-background transition-all',
                data.branchTaken === 'true' ? '!bg-green-500 scale-125' : '!bg-green-400'
              )}
              style={{ top: '40%' }}
            />
            <Handle
              type="source"
              position={Position.Right}
              id="false"
              className={cn(
                'w-3 h-3 border-2 border-background transition-all',
                data.branchTaken === 'false' ? '!bg-red-500 scale-125' : '!bg-red-400'
              )}
              style={{ top: '60%' }}
            />
          </>
        ) : (
          <Handle
            type="source"
            position={Position.Right}
            className={cn(
              'w-3 h-3 border-2 border-background transition-colors',
              status === 'completed' ? '!bg-green-500' :
              status === 'running' ? '!bg-blue-500' :
              '!bg-primary'
            )}
          />
        )}
      </Card>
    </div>
  );
};

export default memo(EnhancedControlNode);
