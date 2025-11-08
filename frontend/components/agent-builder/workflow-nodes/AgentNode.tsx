'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bot } from 'lucide-react';

const AgentNode = ({ data, selected }: NodeProps) => {
  return (
    <Card
      className={`min-w-[200px] transition-all ${
        selected ? 'ring-2 ring-primary shadow-lg' : 'shadow-md'
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="rounded-full bg-primary/10 p-2">
            <Bot className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm mb-1 truncate">{data.label}</div>
            {data.description && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {data.description}
              </p>
            )}
            <div className="mt-2">
              <Badge variant="outline" className="text-xs">
                Agent
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

      {/* Output Handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-primary border-2 border-background"
      />
    </Card>
  );
};

export default memo(AgentNode);
