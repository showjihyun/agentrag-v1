'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Sparkles,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Loader2,
  Copy,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import { PromptMetrics } from './PromptMetrics';
import { ABTestManager } from './ABTestManager';
import { PromptComparison } from './PromptComparison';

interface PromptOptimizerProps {
  agentId: string;
  currentPrompt: string;
  onPromptUpdate: (newPrompt: string) => void;
}

interface OptimizationSuggestion {
  id: string;
  optimizedPrompt: string;
  improvements: string[];
  estimatedScore: number;
  reasoning: string;
}

export function PromptOptimizer({ agentId, currentPrompt, onPromptUpdate }: PromptOptimizerProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<OptimizationSuggestion[]>([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState<OptimizationSuggestion | null>(null);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const response = await agentBuilderAPI.optimizePrompt(agentId, {
        current_prompt: currentPrompt,
        optimization_goals: ['clarity', 'specificity', 'performance'],
      });

      setSuggestions(response.suggestions || []);
      
      toast({
        title: 'Optimization Complete',
        description: `Generated ${response.suggestions?.length || 0} suggestions`,
      });
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to optimize prompt',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApplySuggestion = (suggestion: OptimizationSuggestion) => {
    onPromptUpdate(suggestion.optimizedPrompt);
    toast({
      title: 'Prompt Updated',
      description: 'The optimized prompt has been applied',
    });
  };

  const handleCopySuggestion = async (prompt: string) => {
    try {
      await navigator.clipboard.writeText(prompt);
      toast({
        title: 'Copied',
        description: 'Prompt copied to clipboard',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to copy to clipboard',
        variant: 'destructive',
      });
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                AI-Powered Prompt Optimization
              </CardTitle>
              <CardDescription>
                Improve your prompt for better performance and clarity
              </CardDescription>
            </div>
            <Button onClick={handleOptimize} disabled={loading || !currentPrompt}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Optimize Prompt
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="suggestions" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
              <TabsTrigger value="metrics">Metrics</TabsTrigger>
              <TabsTrigger value="ab-test">A/B Testing</TabsTrigger>
              <TabsTrigger value="comparison">Comparison</TabsTrigger>
            </TabsList>

            <TabsContent value="suggestions" className="space-y-4">
              {suggestions.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Click "Optimize Prompt" to get AI-powered suggestions</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {suggestions.map((suggestion) => (
                    <Card key={suggestion.id} className="border-2 hover:border-primary transition-colors">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <CardTitle className="text-lg">Optimized Version</CardTitle>
                              <Badge variant="outline" className={getScoreColor(suggestion.estimatedScore)}>
                                Score: {suggestion.estimatedScore}/100
                              </Badge>
                            </div>
                            <CardDescription>{suggestion.reasoning}</CardDescription>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <label className="text-sm font-medium mb-2 block">Optimized Prompt</label>
                          <Textarea
                            value={suggestion.optimizedPrompt}
                            readOnly
                            rows={6}
                            className="font-mono text-sm"
                          />
                        </div>

                        <div>
                          <label className="text-sm font-medium mb-2 block">Key Improvements</label>
                          <ul className="space-y-2">
                            {suggestion.improvements.map((improvement, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm">
                                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                                <span>{improvement}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div className="flex gap-2">
                          <Button
                            onClick={() => handleApplySuggestion(suggestion)}
                            className="flex-1"
                          >
                            <CheckCircle className="mr-2 h-4 w-4" />
                            Apply This Prompt
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => handleCopySuggestion(suggestion.optimizedPrompt)}
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setSelectedSuggestion(suggestion)}
                          >
                            <TrendingUp className="h-4 w-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="metrics">
              <PromptMetrics agentId={agentId} currentPrompt={currentPrompt} />
            </TabsContent>

            <TabsContent value="ab-test">
              <ABTestManager agentId={agentId} />
            </TabsContent>

            <TabsContent value="comparison">
              <PromptComparison
                agentId={agentId}
                prompts={[
                  { id: 'current', label: 'Current', prompt: currentPrompt },
                  ...suggestions.map((s) => ({
                    id: s.id,
                    label: `Suggestion ${s.estimatedScore}`,
                    prompt: s.optimizedPrompt,
                  })),
                ]}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
