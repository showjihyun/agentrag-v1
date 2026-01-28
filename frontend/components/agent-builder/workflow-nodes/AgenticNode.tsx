'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Sparkles, 
  Brain, 
  ListTree, 
  Wrench,
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Icon mapping
const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  sparkles: Sparkles,
  brain: Brain,
  'list-tree': ListTree,
  wrench: Wrench,
};

// Status icons
const STATUS_ICONS = {
  idle: Play,
  running: Loader2,
  success: CheckCircle2,
  error: AlertCircle,
};

export interface AgenticNodeData {
  label: string;
  blockType: 'agentic_reflection' | 'agentic_planning' | 'agentic_tool_selector' | 'agentic_rag';
  config?: Record<string, any>;
  status?: 'idle' | 'running' | 'success' | 'error';
  icon?: string;
  bgColor?: string;
  
  // Execution metadata
  iterationCount?: number;
  qualityScore?: number;
  subQueriesCount?: number;
  confidenceScore?: number;
}

function AgenticNode({ data, selected }: NodeProps<AgenticNodeData>) {
  const Icon = ICON_MAP[data.icon || 'sparkles'] || Sparkles;
  const StatusIcon = STATUS_ICONS[data.status || 'idle'];
  
  // Get block-specific colors
  const getBlockColors = () => {
    switch (data.blockType) {
      case 'agentic_reflection':
        return {
          bg: 'from-purple-500 to-violet-500',
          border: 'border-purple-500',
          badge: 'bg-purple-500/20 text-purple-700',
        };
      case 'agentic_planning':
        return {
          bg: 'from-green-500 to-emerald-500',
          border: 'border-green-500',
          badge: 'bg-green-500/20 text-green-700',
        };
      case 'agentic_tool_selector':
        return {
          bg: 'from-amber-500 to-orange-500',
          border: 'border-amber-500',
          badge: 'bg-amber-500/20 text-amber-700',
        };
      case 'agentic_rag':
        return {
          bg: 'from-pink-500 to-rose-500',
          border: 'border-pink-500',
          badge: 'bg-pink-500/20 text-pink-700',
        };
      default:
        return {
          bg: 'from-purple-500 to-pink-500',
          border: 'border-purple-500',
          badge: 'bg-purple-500/20 text-purple-700',
        };
    }
  };

  const colors = getBlockColors();

  return (
    <Card
      className={cn(
        'min-w-[280px] transition-all duration-200',
        selected && 'ring-2 ring-primary ring-offset-2',
        data.status === 'running' && 'ring-1 ring-primary/30'
      )}
    >
      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-primary transition-all duration-200 hover:scale-110"
      />

      <CardHeader className="p-3 pb-2">
        {/* Header with gradient background */}
        <div
          className={cn(
            'flex items-center gap-2 p-2 rounded-lg bg-gradient-to-r transition-all duration-300',
            colors.bg,
            data.status === 'running' && 'shadow-md'
          )}
        >
          <div className="p-1.5 rounded-md bg-white/20 backdrop-blur-sm">
            <Icon className={cn(
              'h-4 w-4 text-white transition-all duration-300',
              data.status === 'running' && 'animate-pulse'
            )} />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-semibold text-white truncate">
              {data.label}
            </h3>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="secondary" className="text-xs bg-white/20 text-white border-0">
              Agentic
            </Badge>
            <StatusIcon 
              className={cn(
                'h-4 w-4 transition-all duration-200',
                data.status === 'running' && 'animate-spin',
                data.status === 'success' && 'text-green-500',
                data.status === 'error' && 'text-red-500',
                data.status === 'idle' && 'text-white'
              )}
            />
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-3 pt-2 space-y-2">
        {/* Configuration Summary */}
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="text-xs space-y-1">
            {Object.entries(data.config).slice(0, 2).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-muted-foreground capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="font-medium truncate max-w-[120px]">
                  {String(value)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Execution Metadata */}
        {data.status !== 'idle' && (
          <div className="flex flex-wrap gap-2 pt-2 border-t">
            {data.iterationCount !== undefined && (
              <Badge variant="outline" className="text-xs">
                Iter: {data.iterationCount}
              </Badge>
            )}
            {data.qualityScore !== undefined && (
              <Badge variant="outline" className="text-xs">
                Quality: {(data.qualityScore * 100).toFixed(0)}%
              </Badge>
            )}
            {data.subQueriesCount !== undefined && (
              <Badge variant="outline" className="text-xs">
                Queries: {data.subQueriesCount}
              </Badge>
            )}
            {data.confidenceScore !== undefined && (
              <Badge variant="outline" className="text-xs">
                Conf: {(data.confidenceScore * 100).toFixed(0)}%
              </Badge>
            )}
          </div>
        )}

        {/* Block Type Badge */}
        <div className="flex items-center justify-between pt-1">
          <Badge variant="outline" className={cn('text-xs', colors.badge)}>
            {data.blockType.replace('agentic_', '')}
          </Badge>
          {data.status === 'running' && (
            <span className="text-xs text-muted-foreground animate-pulse">
              Processing...
            </span>
          )}
        </div>
      </CardContent>

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-primary transition-all duration-200 hover:scale-110"
      />
    </Card>
  );
}

export default memo(AgenticNode);
