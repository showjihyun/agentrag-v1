'use client';

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Box, Zap, Code, Layers } from 'lucide-react';

const getBlockIcon = (blockType: string) => {
  switch (blockType) {
    case 'llm':
      return <Zap className="h-5 w-5 text-blue-500" />;
    case 'tool':
      return <Box className="h-5 w-5 text-green-500" />;
    case 'logic':
      return <Code className="h-5 w-5 text-orange-500" />;
    case 'composite':
      return <Layers className="h-5 w-5 text-purple-500" />;
    default:
      return <Box className="h-5 w-5 text-secondary" />;
  }
};

const getBlockColor = (blockType: string) => {
  switch (blockType) {
    case 'llm':
      return 'bg-blue-500/10';
    case 'tool':
      return 'bg-green-500/10';
    case 'logic':
      return 'bg-orange-500/10';
    case 'composite':
      return 'bg-purple-500/10';
    default:
      return 'bg-secondary/10';
  }
};

const BlockNode = ({ data, selected }: NodeProps) => {
  return (
    <Card
      className={`min-w-[200px] transition-all ${
        selected ? 'ring-2 ring-primary shadow-lg' : 'shadow-md'
      }`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className={`rounded-full p-2 ${getBlockColor(data.block_type)}`}>
            {getBlockIcon(data.block_type)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm mb-1 truncate">{data.label}</div>
            {data.description && (
              <p className="text-xs text-muted-foreground line-clamp-2">
                {data.description}
              </p>
            )}
            <div className="mt-2 flex gap-1">
              <Badge variant="outline" className="text-xs">
                Block
              </Badge>
              {data.block_type && (
                <Badge variant="secondary" className="text-xs capitalize">
                  {data.block_type}
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

export default memo(BlockNode);
