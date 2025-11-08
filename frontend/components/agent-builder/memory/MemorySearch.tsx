'use client';

import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { useToast } from '@/hooks/use-toast';
import { Search, Loader2 } from 'lucide-react';

interface MemorySearchProps {
  agentId: string;
}

interface SearchResult {
  id: string;
  content: string;
  type: string;
  relevance_score: number;
  created_at: string;
  metadata: Record<string, any>;
}

export function MemorySearch({ agentId }: MemorySearchProps) {
  const { toast } = useToast();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Please enter a search query',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      const data = await agentBuilderAPI.searchMemories(agentId, {
        query,
        top_k: 20,
      });
      setResults(data.results || []);
      setSearched(true);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to search memories',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Search memories by content or metadata..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Search className="h-4 w-4" />
          )}
        </Button>
      </div>

      {searched && (
        <div className="text-sm text-muted-foreground">
          Found {results.length} results
        </div>
      )}

      <ScrollArea className="h-[500px]">
        <div className="space-y-3">
          {results.map((result) => (
            <Card key={result.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{result.type}</Badge>
                    <Badge variant="secondary">
                      {(result.relevance_score * 100).toFixed(0)}% match
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(result.created_at).toLocaleDateString()}
                  </span>
                </div>
                <p className="text-sm">{result.content}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>

      {searched && results.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            No memories found matching your query
          </CardContent>
        </Card>
      )}
    </div>
  );
}
