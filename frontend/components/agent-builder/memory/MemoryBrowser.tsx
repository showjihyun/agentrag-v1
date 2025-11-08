'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useToast } from '@/hooks/use-toast';
import { Trash2, Eye, Filter } from 'lucide-react';

interface MemoryBrowserProps {
  agentId: string;
}

interface Memory {
  id: string;
  type: 'short_term' | 'long_term' | 'episodic' | 'semantic';
  content: string;
  metadata: Record<string, any>;
  created_at: string;
  accessed_count: number;
  importance_score: number;
}

export function MemoryBrowser({ agentId }: MemoryBrowserProps) {
  const { toast } = useToast();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  useEffect(() => {
    loadMemories();
  }, [agentId, filter]);

  const loadMemories = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getMemories(agentId, {
        type: filter === 'all' ? undefined : filter,
        limit: 50,
      });
      setMemories(data.memories || []);
    } catch (error) {
      console.error('Failed to load memories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (memoryId: string) => {
    try {
      await agentBuilderAPI.deleteMemory(agentId, memoryId);
      toast({
        title: 'Memory Deleted',
        description: 'Memory has been removed',
      });
      loadMemories();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to delete memory',
        variant: 'destructive',
      });
    }
  };

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      short_term: 'bg-blue-500',
      long_term: 'bg-green-500',
      episodic: 'bg-purple-500',
      semantic: 'bg-orange-500',
    };
    return colors[type] || 'bg-gray-500';
  };

  const getImportanceBadge = (score: number) => {
    if (score >= 0.8) return <Badge variant="destructive">High</Badge>;
    if (score >= 0.5) return <Badge variant="default">Medium</Badge>;
    return <Badge variant="secondary">Low</Badge>;
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Select value={filter} onValueChange={setFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="short_term">Short-term</SelectItem>
            <SelectItem value="long_term">Long-term</SelectItem>
            <SelectItem value="episodic">Episodic</SelectItem>
            <SelectItem value="semantic">Semantic</SelectItem>
          </SelectContent>
        </Select>
        <div className="text-sm text-muted-foreground">
          {memories.length} memories
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ScrollArea className="h-[500px]">
          <div className="space-y-2 pr-4">
            {memories.map((memory) => (
              <Card
                key={memory.id}
                className={`cursor-pointer transition-colors ${
                  selectedMemory?.id === memory.id ? 'border-primary' : ''
                }`}
                onClick={() => setSelectedMemory(memory)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${getTypeColor(memory.type)}`} />
                      <Badge variant="outline" className="text-xs">
                        {memory.type.replace('_', '-')}
                      </Badge>
                      {getImportanceBadge(memory.importance_score)}
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(memory.id);
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                  <p className="text-sm line-clamp-2">{memory.content}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span>{new Date(memory.created_at).toLocaleDateString()}</span>
                    <span>•</span>
                    <span>Accessed {memory.accessed_count}x</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>

        <Card>
          <CardContent className="p-6">
            {selectedMemory ? (
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Memory Details</h3>
                  <div className="flex items-center gap-2 mb-4">
                    <Badge variant="outline">{selectedMemory.type.replace('_', '-')}</Badge>
                    {getImportanceBadge(selectedMemory.importance_score)}
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium">Content</label>
                  <p className="text-sm mt-1 p-3 bg-muted rounded-md">
                    {selectedMemory.content}
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium">Metadata</label>
                  <pre className="text-xs mt-1 p-3 bg-muted rounded-md overflow-auto">
                    {JSON.stringify(selectedMemory.metadata, null, 2)}
                  </pre>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <label className="text-muted-foreground">Created</label>
                    <p>{new Date(selectedMemory.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="text-muted-foreground">Access Count</label>
                    <p>{selectedMemory.accessed_count}</p>
                  </div>
                  <div>
                    <label className="text-muted-foreground">Importance</label>
                    <p>{(selectedMemory.importance_score * 100).toFixed(0)}%</p>
                  </div>
                </div>

                <Button
                  variant="destructive"
                  className="w-full"
                  onClick={() => handleDelete(selectedMemory.id)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Memory
                </Button>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a memory to view details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
