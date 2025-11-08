'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, Repeat, Layers } from 'lucide-react';

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

const ControlNode = ({ data, selected }: NodeProps) => {
  return (
    <Card
      className={`min-w-[200px] transition-all ${
        selected ? 'ring-2 ring-primary shadow-lg' : 'shadow-md'
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={`rounded-full p-2 ${getControlColor(data.controlType)}`}>
            {getControlIcon(data.controlType)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm mb-1 truncate">{data.label}</div>
            {data.condition && (
              <p className="text-xs text-muted-foreground font-mono line-clamp-2">
                {data.condition}
              </p>
            )}
            <div className="mt-2">
              <Badge variant="outline" className="text-xs capitalize">
                {data.controlType || 'Control'}
              </Badge>
            </div>
          </div>
        </div>
      </CardContent>

      {/* Input Handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-primary border-2 border-background"
      />

      {/* Output Handles - Multiple for conditional/parallel */}
      {data.controlType === 'conditional' || data.controlType === 'parallel' ? (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="true"
            className="w-3 h-3 !bg-green-500 border-2 border-background"
            style={{ top: '40%' }}
          />
          <Handle
            type="source"
            position={Position.Right}
            id="false"
            className="w-3 h-3 !bg-red-500 border-2 border-background"
            style={{ top: '60%' }}
          />
        </>
      ) : (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 !bg-primary border-2 border-background"
        />
      )}
    </Card>
  );
};

export default memo(ControlNode);
