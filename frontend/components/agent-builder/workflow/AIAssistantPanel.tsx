'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Sparkles,
  MessageSquare,
  Lightbulb,
  AlertCircle,
  TrendingUp,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

interface ErrorDiagnosis {
  error_type: string;
  root_cause: string;
  explanation: string;
  suggested_fixes: string[];
  related_nodes: string[];
  confidence: number;
}

interface BreakpointSuggestion {
  node_id: string;
  reason: string;
  priority: 'high' | 'medium' | 'low';
  condition?: string;
}

interface OptimizationSuggestion {
  node_id: string;
  issue: string;
  suggestion: string;
  expected_improvement: string;
  implementation_difficulty: 'easy' | 'medium' | 'hard';
  code_example?: string;
}

interface AIAssistantPanelProps {
  workflowId: string;
  onApplyBreakpoint?: (nodeId: string, condition?: string) => void;
}

export function AIAssistantPanel({ workflowId, onApplyBreakpoint }: AIAssistantPanelProps) {
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorDiagnosis, setErrorDiagnosis] = useState<ErrorDiagnosis | null>(null);
  const [breakpointSuggestions, setBreakpointSuggestions] = useState<BreakpointSuggestion[]>([]);
  const [optimizations, setOptimizations] = useState<OptimizationSuggestion[]>([]);

  const handleSendQuery = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setChatHistory(prev => [...prev, { role: 'user', content: query }]);

    try {
      const response = await fetch('/api/agent-builder/ai-assistant/debug-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: workflowId,
          query,
          workflow_context: {}
        })
      });

      const data = await response.json();
      setChatHistory(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (error) {
      console.error('Failed to send query:', error);
      setChatHistory(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }]);
    } finally {
      setIsLoading(false);
      setQuery('');
    }
  };

  const fetchBreakpointSuggestions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/ai-assistant/${workflowId}/suggest-breakpoints`);
      const data = await response.json();
      setBreakpointSuggestions(data);
    } catch (error) {
      console.error('Failed to fetch breakpoint suggestions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchOptimizations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/agent-builder/ai-assistant/${workflowId}/suggest-optimizations`);
      const data = await response.json();
      setOptimizations(data);
    } catch (error) {
      console.error('Failed to fetch optimizations:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'default';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy': return 'default';
      case 'medium': return 'secondary';
      case 'hard': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-purple-500" />
          AI Assistant
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col overflow-hidden">
        <Tabs defaultValue="chat" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="chat">
              <MessageSquare className="h-4 w-4 mr-2" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="suggestions">
              <Lightbulb className="h-4 w-4 mr-2" />
              Suggestions
            </TabsTrigger>
            <TabsTrigger value="optimizations">
              <TrendingUp className="h-4 w-4 mr-2" />
              Optimize
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden mt-4">
            <ScrollArea className="flex-1 mb-4">
              <div className="space-y-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Sparkles className="h-12 w-12 mx-auto mb-2 text-purple-500" />
                    <p className="text-sm">Ask me anything about your workflow!</p>
                    <p className="text-xs mt-2">Try: "Why did node-3 fail?" or "How can I optimize this?"</p>
                  </div>
                ) : (
                  chatHistory.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-lg p-3">
                      <Loader2 className="h-4 w-4 animate-spin" />
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            <div className="flex gap-2">
              <Input
                placeholder="Ask a question..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSendQuery()}
                disabled={isLoading}
              />
              <Button onClick={handleSendQuery} disabled={isLoading || !query.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </TabsContent>

          {/* Breakpoint Suggestions Tab */}
          <TabsContent value="suggestions" className="flex-1 overflow-hidden mt-4">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                AI-suggested breakpoints for debugging
              </p>
              <Button size="sm" onClick={fetchBreakpointSuggestions} disabled={isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Refresh'}
              </Button>
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {breakpointSuggestions.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Lightbulb className="h-12 w-12 mx-auto mb-2 text-yellow-500" />
                    <p className="text-sm">No suggestions yet</p>
                    <p className="text-xs mt-2">Click Refresh to get AI suggestions</p>
                  </div>
                ) : (
                  breakpointSuggestions.map((suggestion, index) => (
                    <Card key={index}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-blue-500" />
                            <span className="font-medium text-sm">{suggestion.node_id}</span>
                          </div>
                          <Badge variant={getPriorityColor(suggestion.priority) as any}>
                            {suggestion.priority}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          {suggestion.reason}
                        </p>
                        {suggestion.condition && (
                          <div className="bg-muted p-2 rounded text-xs mb-3">
                            <span className="text-muted-foreground">Condition:</span>{' '}
                            <code>{suggestion.condition}</code>
                          </div>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onApplyBreakpoint?.(suggestion.node_id, suggestion.condition)}
                        >
                          Apply Breakpoint
                        </Button>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Optimizations Tab */}
          <TabsContent value="optimizations" className="flex-1 overflow-hidden mt-4">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                AI-suggested performance optimizations
              </p>
              <Button size="sm" onClick={fetchOptimizations} disabled={isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Analyze'}
              </Button>
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {optimizations.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <TrendingUp className="h-12 w-12 mx-auto mb-2 text-green-500" />
                    <p className="text-sm">No optimizations yet</p>
                    <p className="text-xs mt-2">Click Analyze to get AI suggestions</p>
                  </div>
                ) : (
                  optimizations.map((opt, index) => (
                    <Card key={index}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-green-500" />
                            <span className="font-medium text-sm">{opt.node_id}</span>
                          </div>
                          <Badge variant={getDifficultyColor(opt.implementation_difficulty) as any}>
                            {opt.implementation_difficulty}
                          </Badge>
                        </div>

                        <div className="space-y-2 mb-3">
                          <div>
                            <span className="text-xs font-semibold text-muted-foreground">Issue:</span>
                            <p className="text-sm">{opt.issue}</p>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-muted-foreground">Suggestion:</span>
                            <p className="text-sm">{opt.suggestion}</p>
                          </div>
                          <div>
                            <span className="text-xs font-semibold text-muted-foreground">Expected Improvement:</span>
                            <p className="text-sm text-green-600">{opt.expected_improvement}</p>
                          </div>
                        </div>

                        {opt.code_example && (
                          <div className="bg-muted p-3 rounded text-xs">
                            <div className="text-muted-foreground mb-1">Code Example:</div>
                            <pre className="overflow-auto">{opt.code_example}</pre>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
