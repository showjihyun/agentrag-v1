'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ArrowRight, Check, X, Minus } from 'lucide-react';

interface PromptComparisonProps {
  agentId: string;
  prompts: Array<{
    id: string;
    label: string;
    prompt: string;
    metrics?: {
      clarity: number;
      specificity: number;
      token_count: number;
      estimated_cost: number;
    };
  }>;
}

export function PromptComparison({ agentId, prompts }: PromptComparisonProps) {
  const [selectedPrompts, setSelectedPrompts] = useState<string[]>(
    prompts.slice(0, 2).map((p) => p.id)
  );

  const togglePromptSelection = (id: string) => {
    if (selectedPrompts.includes(id)) {
      if (selectedPrompts.length > 1) {
        setSelectedPrompts(selectedPrompts.filter((p) => p !== id));
      }
    } else {
      if (selectedPrompts.length < 3) {
        setSelectedPrompts([...selectedPrompts, id]);
      }
    }
  };

  const selectedPromptData = prompts.filter((p) => selectedPrompts.includes(p.id));

  const getDiffHighlight = (text: string, compareText: string) => {
    // Simple word-level diff
    const words1 = text.split(/\s+/);
    const words2 = compareText.split(/\s+/);
    
    return words1.map((word, idx) => {
      const isInOther = words2.includes(word);
      return (
        <span
          key={idx}
          className={!isInOther ? 'bg-yellow-200 dark:bg-yellow-900' : ''}
        >
          {word}{' '}
        </span>
      );
    });
  };

  const getMetricComparison = (metric: number, others: number[]) => {
    const avg = others.reduce((a, b) => a + b, 0) / others.length;
    if (metric > avg) return <Check className="h-4 w-4 text-green-500" />;
    if (metric < avg) return <X className="h-4 w-4 text-red-500" />;
    return <Minus className="h-4 w-4 text-gray-500" />;
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Select Prompts to Compare</CardTitle>
          <CardDescription>Choose 2-3 prompts to compare side by side</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {prompts.map((prompt) => (
              <Button
                key={prompt.id}
                variant={selectedPrompts.includes(prompt.id) ? 'default' : 'outline'}
                size="sm"
                onClick={() => togglePromptSelection(prompt.id)}
                disabled={
                  !selectedPrompts.includes(prompt.id) && selectedPrompts.length >= 3
                }
              >
                {prompt.label}
                {selectedPrompts.includes(prompt.id) && (
                  <Check className="ml-2 h-4 w-4" />
                )}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {selectedPromptData.length >= 2 && (
        <Tabs defaultValue="side-by-side" className="w-full">
          <TabsList>
            <TabsTrigger value="side-by-side">Side by Side</TabsTrigger>
            <TabsTrigger value="diff">Diff View</TabsTrigger>
            <TabsTrigger value="metrics">Metrics</TabsTrigger>
          </TabsList>

          <TabsContent value="side-by-side">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {selectedPromptData.map((prompt) => (
                <Card key={prompt.id}>
                  <CardHeader>
                    <CardTitle className="text-lg">{prompt.label}</CardTitle>
                    {prompt.metrics && (
                      <div className="flex gap-2 mt-2">
                        <Badge variant="outline">
                          {prompt.metrics.token_count} tokens
                        </Badge>
                        <Badge variant="outline">
                          ${prompt.metrics.estimated_cost.toFixed(4)}
                        </Badge>
                      </div>
                    )}
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[400px]">
                      <pre className="text-sm whitespace-pre-wrap font-mono">
                        {prompt.prompt}
                      </pre>
                    </ScrollArea>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="diff">
            <Card>
              <CardHeader>
                <CardTitle>Differences Highlighted</CardTitle>
                <CardDescription>
                  Unique words in each prompt are highlighted
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {selectedPromptData.map((prompt, idx) => (
                    <div key={prompt.id}>
                      <h4 className="font-semibold mb-2">{prompt.label}</h4>
                      <div className="p-4 bg-muted rounded-md">
                        <div className="text-sm font-mono">
                          {idx === 0
                            ? prompt.prompt
                            : getDiffHighlight(
                                prompt.prompt,
                                selectedPromptData[0].prompt
                              )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metrics">
            {selectedPromptData.every((p) => p.metrics) ? (
              <Card>
                <CardHeader>
                  <CardTitle>Metrics Comparison</CardTitle>
                  <CardDescription>
                    Compare quality and efficiency metrics
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left p-2">Metric</th>
                          {selectedPromptData.map((prompt) => (
                            <th key={prompt.id} className="text-center p-2">
                              {prompt.label}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        <tr className="border-b">
                          <td className="p-2 font-medium">Clarity Score</td>
                          {selectedPromptData.map((prompt) => (
                            <td key={prompt.id} className="text-center p-2">
                              <div className="flex items-center justify-center gap-2">
                                <span>{prompt.metrics?.clarity || 0}</span>
                                {getMetricComparison(
                                  prompt.metrics?.clarity || 0,
                                  selectedPromptData
                                    .filter((p) => p.id !== prompt.id)
                                    .map((p) => p.metrics?.clarity || 0)
                                )}
                              </div>
                            </td>
                          ))}
                        </tr>
                        <tr className="border-b">
                          <td className="p-2 font-medium">Specificity Score</td>
                          {selectedPromptData.map((prompt) => (
                            <td key={prompt.id} className="text-center p-2">
                              <div className="flex items-center justify-center gap-2">
                                <span>{prompt.metrics?.specificity || 0}</span>
                                {getMetricComparison(
                                  prompt.metrics?.specificity || 0,
                                  selectedPromptData
                                    .filter((p) => p.id !== prompt.id)
                                    .map((p) => p.metrics?.specificity || 0)
                                )}
                              </div>
                            </td>
                          ))}
                        </tr>
                        <tr className="border-b">
                          <td className="p-2 font-medium">Token Count</td>
                          {selectedPromptData.map((prompt) => (
                            <td key={prompt.id} className="text-center p-2">
                              <div className="flex items-center justify-center gap-2">
                                <span>{prompt.metrics?.token_count || 0}</span>
                                {getMetricComparison(
                                  -(prompt.metrics?.token_count || 0), // Lower is better
                                  selectedPromptData
                                    .filter((p) => p.id !== prompt.id)
                                    .map((p) => -(p.metrics?.token_count || 0))
                                )}
                              </div>
                            </td>
                          ))}
                        </tr>
                        <tr>
                          <td className="p-2 font-medium">Estimated Cost</td>
                          {selectedPromptData.map((prompt) => (
                            <td key={prompt.id} className="text-center p-2">
                              <div className="flex items-center justify-center gap-2">
                                <span>${(prompt.metrics?.estimated_cost || 0).toFixed(4)}</span>
                                {getMetricComparison(
                                  -(prompt.metrics?.estimated_cost || 0), // Lower is better
                                  selectedPromptData
                                    .filter((p) => p.id !== prompt.id)
                                    .map((p) => -(p.metrics?.estimated_cost || 0))
                                )}
                              </div>
                            </td>
                          ))}
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardContent className="p-12 text-center text-muted-foreground">
                  Metrics not available for all selected prompts
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
