'use client';

import { useState, useMemo } from 'react';
import { Search, Loader2, FileText, Filter, BookOpen, Hash, File, AlignLeft, FileType, Calendar } from 'lucide-react';
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
import { cn } from '@/lib/utils';

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

  // Get file type from filename
  const getFileType = (filename: string | undefined): string => {
    if (!filename) return 'unknown';
    const ext = filename.split('.').pop()?.toLowerCase();
    return ext || 'unknown';
  };

  // Get file icon based on type
  const getFileIcon = (filename: string | undefined) => {
    const type = getFileType(filename);
    const iconClass = 'h-4 w-4 flex-shrink-0';
    
    switch (type) {
      case 'pdf':
        return <FileText className={iconClass} />;
      case 'doc':
      case 'docx':
        return <FileType className={iconClass} />;
      case 'txt':
      case 'md':
        return <AlignLeft className={iconClass} />;
      default:
        return <File className={iconClass} />;
    }
  };

  // Format upload date
  const formatDate = (timestamp: number | undefined): string => {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('ko-KR', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  // Highlight matching terms in text
  const highlightText = (text: string, query: string) => {
    if (!text || !query || !query.trim()) return text;
    
    const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);
    if (terms.length === 0) return text;

    const parts: { text: string; highlight: boolean }[] = [];
    let lastIndex = 0;
    const lowerText = text.toLowerCase();

    terms.forEach(term => {
      let index = lowerText.indexOf(term, lastIndex);
      while (index !== -1) {
        if (index > lastIndex) {
          parts.push({ text: text.substring(lastIndex, index), highlight: false });
        }
        parts.push({ text: text.substring(index, index + term.length), highlight: true });
        lastIndex = index + term.length;
        index = lowerText.indexOf(term, lastIndex);
      }
    });

    if (lastIndex < text.length) {
      parts.push({ text: text.substring(lastIndex), highlight: false });
    }

    return parts;
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
                {results.map((result, index) => {
                  const content = result.content || result.text || '';
                  const highlightedParts = highlightText(content, query);
                  const chunkIndex = result.metadata?.chunk_index;
                  
                  // Estimate page number from chunk index if not available
                  // Assuming ~2-3 chunks per page on average
                  const pageNumber = result.metadata?.page_number || 
                    (chunkIndex !== undefined ? Math.floor(chunkIndex / 2.5) + 1 : undefined);
                  
                  const isHighRelevance = result.score >= 0.8;

                  return (
                    <Card 
                      key={`${result.document_id}-${index}`} 
                      className={cn(
                        'hover:shadow-md transition-all',
                        isHighRelevance && 'border-blue-300 bg-blue-50/30 dark:bg-blue-950/20'
                      )}
                    >
                      <CardHeader className="pb-3">
                        {/* Header with filename and score */}
                        <div className="flex items-center justify-between gap-4 mb-3">
                          <div className="flex items-center gap-2 flex-1 min-w-0">
                            <span className={cn(isHighRelevance ? 'text-blue-600' : 'text-muted-foreground')}>
                              {getFileIcon(result.metadata?.filename || result.metadata?.document_name)}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-semibold truncate">
                                {result.metadata?.filename || result.metadata?.document_name || `Document ${result.document_id.substring(0, 8)}...`}
                              </p>
                              {result.metadata?.upload_date && (
                                <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                                  <Calendar className="w-3 h-3" />
                                  {formatDate(result.metadata.upload_date)}
                                </p>
                              )}
                            </div>
                          </div>
                          <Badge variant={getScoreBadgeVariant(result.score)} className="flex-shrink-0">
                            {(result.score * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        
                        {/* Location badges */}
                        {(pageNumber !== undefined || result.metadata?.line_number !== undefined || chunkIndex !== undefined) && (
                          <div className="flex flex-wrap items-center gap-2">
                            {pageNumber !== undefined && pageNumber > 0 && (
                              <Badge variant="secondary" className="text-xs">
                                <BookOpen className="w-3 h-3 mr-1" />
                                Page ~{pageNumber}
                                {!result.metadata?.page_number && <span className="ml-1 opacity-60">(est.)</span>}
                              </Badge>
                            )}
                            {result.metadata?.line_number !== undefined && result.metadata.line_number > 0 && (
                              <Badge variant="secondary" className="text-xs">
                                <AlignLeft className="w-3 h-3 mr-1" />
                                Line {result.metadata.line_number}
                              </Badge>
                            )}
                            {chunkIndex !== undefined && (
                              <Badge variant="outline" className="text-xs">
                                <Hash className="w-3 h-3 mr-1" />
                                Chunk {chunkIndex + 1}
                              </Badge>
                            )}
                          </div>
                        )}
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          {/* Highlighted Content */}
                          <div className="text-sm leading-relaxed bg-white dark:bg-gray-900 p-3 rounded-md border">
                            {Array.isArray(highlightedParts) ? (
                              highlightedParts.map((part, i) => (
                                <span
                                  key={i}
                                  className={cn(
                                    part.highlight && 'bg-yellow-200 dark:bg-yellow-900/50 font-semibold px-0.5 rounded'
                                  )}
                                >
                                  {part.text}
                                </span>
                              ))
                            ) : (
                              <span>{content}</span>
                            )}
                          </div>
                          
                          {/* Additional Metadata */}
                          {result.metadata && (() => {
                            const excludeKeys = ['filename', 'document_name', 'chunk_index', 'page_number', 'line_number', 'upload_date'];
                            const additionalMetadata = Object.entries(result.metadata)
                              .filter(([key, value]) => !excludeKeys.includes(key) && value !== null && value !== undefined);
                            
                            return additionalMetadata.length > 0 && (
                              <>
                                <Separator />
                                <div className="flex flex-wrap gap-2">
                                  {additionalMetadata.map(([key, value]) => (
                                    <Badge key={key} variant="secondary" className="text-xs">
                                      {key.replace(/_/g, ' ')}: {String(value)}
                                    </Badge>
                                  ))}
                                </div>
                              </>
                            );
                          })()}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
