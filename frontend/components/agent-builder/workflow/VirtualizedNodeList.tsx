'use client';

import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';
import { Node } from 'reactflow';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Bot, GitBranch, Zap, Clock } from 'lucide-react';

interface VirtualizedNodeListProps {
  nodes: Node[];
  onNodeClick: (node: Node) => void;
  selectedNodeId?: string;
}

export function VirtualizedNodeList({
  nodes,
  onNodeClick,
  selectedNodeId,
}: VirtualizedNodeListProps) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: nodes.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 5,
  });

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'agent':
        return <Bot className="h-4 w-4" />;
      case 'control':
        return <GitBranch className="h-4 w-4" />;
      case 'tool':
        return <Zap className="h-4 w-4" />;
      default:
        return <Bot className="h-4 w-4" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
      case 'success':
        return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
      case 'error':
        return 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300';
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  return (
    <div
      ref={parentRef}
      className="h-full overflow-auto"
      style={{ contain: 'strict' }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const node = nodes[virtualItem.index];
          const isSelected = node.id === selectedNodeId;

          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <Card
                className={`mx-2 my-1 cursor-pointer transition-all hover:shadow-md ${
                  isSelected ? 'ring-2 ring-primary' : ''
                }`}
                onClick={() => onNodeClick(node)}
              >
                <CardContent className="p-3">
                  <div className="flex items-start gap-3">
                    <div className="rounded-full bg-primary/10 p-2">
                      {getNodeIcon(node.type || 'agent')}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {node.data.label}
                      </div>
                      {node.data.description && (
                        <p className="text-xs text-muted-foreground truncate">
                          {node.data.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {node.type || 'agent'}
                        </Badge>
                        {node.data.status && (
                          <Badge
                            variant="secondary"
                            className={`text-xs ${getStatusColor(node.data.status)}`}
                          >
                            {node.data.status}
                          </Badge>
                        )}
                        {node.data.executionTime && (
                          <span className="text-xs text-muted-foreground flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {node.data.executionTime}ms
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          );
        })}
      </div>
    </div>
  );
}
