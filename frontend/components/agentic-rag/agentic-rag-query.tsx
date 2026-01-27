'use client';

import React, { useState } from 'react';
import { Send, Loader2, Sparkles, Brain, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { useToast } from '@/hooks/use-toast';
import { QueryComplexityIndicator } from './query-complexity-indicator';
import { SubQueryVisualization } from './sub-query-visualization';
import { SourceRelevanceDisplay } from './source-relevance-display';
import { ReflectionHistory } from './reflection-history';

interface AgenticRAGResult {
  answer: string;
  sources: Array<{
    content: string;
    metadata: Record<string, any>;
    source_type: string;
    relevance_score: number;
    url?: string;
  }>;
  metadata: {
    query_complexity: string;
    retrieval_strategy: string;
    sub_queries: Array<{
      id: string;
      query: string;
      num_results: number;
    }>;
    retrieval_iterations: number;
    confidence_score: number;
    reflection_applied: boolean;
    execution_time: number;
    total_sources: number;
  };
}

export function AgenticRAGQuery() {
  const [query, setQuery] = useState('');
  const [strategy, setStrategy] = useState('adaptive');
  const [topK, setTopK] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AgenticRAGResult | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      toast({
        title: 'Query required',
        description: 'Please enter a query',
        variant: 'destructive',
      });
      return;
    }

    setIsLoading(true);
    setResult(null);

    try {
      const response = await fetch('/api/agentic-rag/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          strategy,
          top_k: topK,
        }),
      });

      if (!response.ok) {
        throw new Error('Query failed');
      }

      const data = await response.json();
      setResult(data);

      toast({
        title: 'Query completed',
        description: `Found ${data.metadata.total_sources} sources in ${data.metadata.execution_time.toFixed(2)}s`,
      });
    } catch (error) {
      toast({
        title: 'Query failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStrategyIcon = (strat: string) => {
    switch (strat) {
      case 'adaptive':
        return <Brain className="h-4 w-4" />;
      case 'hybrid':
        return <Zap className="h-4 w-4" />;
      default:
        return <Sparkles className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Query Input Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            Agentic RAG Query
          </CardTitle>
          <CardDescription>
            Intelligent retrieval with query decomposition, multi-source search, and reflection
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Query Input */}
            <div className="space-y-2">
              <Label htmlFor="query">Your Question</Label>
              <Textarea
                id="query"
                placeholder="Ask a complex question... (e.g., 'Compare GPT-4 and Claude 3 for code generation tasks')"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={4}
                className="resize-none"
              />
            </div>

            {/* Strategy Selection */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="strategy">Retrieval Strategy</Label>
                <Select value={strategy} onValueChange={setStrategy}>
                  <SelectTrigger id="strategy">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="adaptive">
                      <div className="flex items-center gap-2">
                        <Brain className="h-4 w-4" />
                        Adaptive (Recommended)
                      </div>
                    </SelectItem>
                    <SelectItem value="hybrid">
                      <div className="flex items-center gap-2">
                        <Zap className="h-4 w-4" />
                        Hybrid (Vector + Web)
                      </div>
                    </SelectItem>
                    <SelectItem value="vector_only">Vector Only</SelectItem>
                    <SelectItem value="web_only">Web Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="topK">Number of Sources: {topK}</Label>
                <Slider
                  id="topK"
                  min={5}
                  max={20}
                  step={5}
                  value={[topK]}
                  onValueChange={(value) => setTopK(value[0])}
                />
              </div>
            </div>

            {/* Submit Button */}
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Execute Query
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Metadata Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Query Analysis</span>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {getStrategyIcon(result.metadata.retrieval_strategy)}
                    <span className="ml-1">{result.metadata.retrieval_strategy}</span>
                  </Badge>
                  <Badge variant="outline">
                    {result.metadata.execution_time.toFixed(2)}s
                  </Badge>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <QueryComplexityIndicator complexity={result.metadata.query_complexity} />
                
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {result.metadata.total_sources}
                  </div>
                  <div className="text-sm text-muted-foreground">Sources Found</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {(result.metadata.confidence_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-muted-foreground">Confidence</div>
                </div>

                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {result.metadata.retrieval_iterations}
                  </div>
                  <div className="text-sm text-muted-foreground">Iterations</div>
                </div>
              </div>

              {result.metadata.reflection_applied && (
                <div className="mt-4 p-3 bg-purple-50 dark:bg-purple-950 rounded-lg">
                  <div className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                    <Sparkles className="h-4 w-4" />
                    <span className="text-sm font-medium">
                      Answer improved through reflection
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Sub-Query Visualization */}
          {result.metadata.sub_queries.length > 1 && (
            <SubQueryVisualization subQueries={result.metadata.sub_queries} />
          )}

          {/* Answer */}
          <Card>
            <CardHeader>
              <CardTitle>Answer</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="prose dark:prose-invert max-w-none">
                {result.answer}
              </div>
            </CardContent>
          </Card>

          {/* Sources */}
          <SourceRelevanceDisplay sources={result.sources} />
        </div>
      )}
    </div>
  );
}
