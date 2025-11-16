'use client';

import React, { useState } from 'react';
import { Command, CommandInput, CommandList, CommandItem, CommandEmpty, CommandGroup } from '@/components/ui/command';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import type { Node } from 'reactflow';
import { Search } from 'lucide-react';

interface NodeSearchProps {
  nodes: Node[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectNode: (nodeId: string) => void;
}

export function NodeSearch({ nodes, open, onOpenChange, onSelectNode }: NodeSearchProps) {
  const [query, setQuery] = useState('');
  
  const filteredNodes = nodes.filter(node => {
    const name = node.data?.name?.toLowerCase() || '';
    const type = node.type?.toLowerCase() || '';
    const label = node.data?.label?.toLowerCase() || '';
    const q = query.toLowerCase();
    
    return name.includes(q) || type.includes(q) || label.includes(q);
  });

  // 노드 타입별로 그룹화
  const nodesByType = filteredNodes.reduce((acc, node) => {
    const type = node.type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(node);
    return acc;
  }, {} as Record<string, Node[]>);

  const typeLabels: Record<string, string> = {
    start: 'Start Nodes',
    end: 'End Nodes',
    agent: 'Agent Nodes',
    block: 'Block Nodes',
    condition: 'Condition Nodes',
    trigger: 'Trigger Nodes',
    http_request: 'HTTP Request Nodes',
    slack: 'Slack Nodes',
    discord: 'Discord Nodes',
    email: 'Email Nodes',
    other: 'Other Nodes'
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 max-w-2xl">
        <Command>
          <div className="flex items-center border-b px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
            <CommandInput 
              placeholder="Search nodes by name or type..." 
              value={query}
              onValueChange={setQuery}
              className="border-0 focus:ring-0"
            />
          </div>
          <CommandList className="max-h-[400px]">
            <CommandEmpty>No nodes found.</CommandEmpty>
            {Object.entries(nodesByType).map(([type, typeNodes]) => (
              <CommandGroup key={type} heading={typeLabels[type] || type}>
                {typeNodes.map(node => (
                  <CommandItem
                    key={node.id}
                    onSelect={() => {
                      onSelectNode(node.id);
                      onOpenChange(false);
                      setQuery('');
                    }}
                    className="cursor-pointer"
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div className={`w-2 h-2 rounded-full ${
                        node.type === 'start' ? 'bg-green-500' :
                        node.type === 'end' ? 'bg-red-500' :
                        node.type === 'agent' ? 'bg-blue-500' :
                        node.type === 'condition' ? 'bg-yellow-500' :
                        'bg-gray-500'
                      }`} />
                      <div className="flex-1">
                        <div className="font-medium">
                          {node.data?.name || node.data?.label || 'Unnamed'}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {node.type} • ID: {node.id.slice(0, 8)}
                        </div>
                      </div>
                    </div>
                  </CommandItem>
                ))}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
