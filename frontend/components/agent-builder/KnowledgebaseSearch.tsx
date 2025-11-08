'use client';

import { useState } from 'react';
import { Search, Loader2, FileText, Filter } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, KnowledgebaseSearchResult } from '@/lib/api/agent-builder';

interface KnowledgebaseSearchProps {
  knowledgebaseId: string;
}

export default function KnowledgebaseSearch({ knowledgebaseId }: KnowledgebaseSearchProps) {
  const { toast } = useToast();
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(10);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<KnowledgebaseSearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a search query',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSearching(true);
      setHasSearched(true);
      const searchResults = await agentBuilderAPI.searchKnowledgebase(
        knowledgebaseId,
        query,
        topK
      );
      setResults(searchResults);

      if (searchResults.length === 0) {
        toast({
          title: 'No Results',
          description: 'No documents found matching your query',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to search knowledgebase',
        variant: 'destructive',
      });
    } finally {
      setSearching(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !searching) {
      handleSearch();
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500';
    if (score >= 0.6) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const getScoreBadgeVariant = (score: number): 'default' | 'secondary' | 'outline' => {
    if (score >= 0.8) return 'default';
    if (score >= 0.6) return 'secondary';
    return 'outline';
  };

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <Card>
        <CardHeader>
          <CardTitle>Search Knowledgebase</CardTitle>
          <CardDescription>
            Find relevant documents using semantic search
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Label htmlFor="search-query" className="sr-only">
                Search Query
              </Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="search-query"
                  placeholder="Enter your search query..."
                  className="pl-10"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={searching}
                />
              </div>
            </div>
            <Button onClick={handleSearch} disabled={searching || !query.trim()}>
              {searching ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Searching...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search
                </>
              )}
            </Button>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Label htmlFor="top-k" className="text-sm">
                Results:
              </Label>
              <Select
                value={topK.toString()}
                onValueChange={(value) => setTopK(parseInt(value))}
              >
                <SelectTrigger id="top-k" className="w-24">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5</SelectItem>
                  <SelectItem value="10">10</SelectItem>
                  <SelectItem value="20">20</SelectItem>
                  <SelectItem value="50">50</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Search Results</CardTitle>
              <CardDescription>
                {hasSearched && `Found ${results.length} result(s)`}
              </CardDescription>
            </div>
            {results.length > 0 && (
              <Badge variant="outline">
                {results.length} / {topK}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!hasSearched ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Search className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Start Searching</h3>
              <p className="text-sm text-muted-foreground">
                Enter a query to search through your documents
              </p>
            </div>
          ) : results.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Results Found</h3>
              <p className="text-sm text-muted-foreground">
                Try adjusting your search query or filters
              </p>
            </div>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-4 pr-4">
                {results.map((result, index) => (
                  <Card key={`${result.document_id}-${index}`} className="hover:shadow-md transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                          <FileText className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">
                              Document {result.document_id.substring(0, 8)}...
                            </p>
                            {result.metadata?.filename && (
                              <p className="text-xs text-muted-foreground truncate">
                                {result.metadata.filename}
                              </p>
                            )}
                          </div>
                        </div>
                        <Badge variant={getScoreBadgeVariant(result.score)}>
                          <span className={getScoreColor(result.score)}>
                            {(result.score * 100).toFixed(1)}%
                          </span>
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <p className="text-sm leading-relaxed whitespace-pre-wrap">
                          {result.content}
                        </p>
                        
                        {result.metadata && Object.keys(result.metadata).length > 1 && (
                          <>
                            <Separator className="my-2" />
                            <div className="flex flex-wrap gap-2">
                              {Object.entries(result.metadata)
                                .filter(([key]) => key !== 'filename')
                                .map(([key, value]) => (
                                  <Badge key={key} variant="outline" className="text-xs">
                                    {key}: {String(value)}
                                  </Badge>
                                ))}
                            </div>
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
