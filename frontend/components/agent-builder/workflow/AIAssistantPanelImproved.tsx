'use client';

import { useState, useCallback } from 'react';
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
} from 'lucide-react';
import { useGET, usePOST } from '@/hooks/useAPI';
import type { 
  BreakpointSuggestion, 
  OptimizationSuggestion,
  ChatMessage 
} from '@/types/workflow';

interface AIAssistantPanelImprovedProps {
  workflowId: string;
  onApplyBreakpoint?: (nodeId: string, condition?: string) => void;
}

export function AIAssistantPanelImproved({ 
  workflowId, 
  onApplyBreakpoint 
}: AIAssistantPanelImprovedProps) {
  const [query, setQuery] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  // API hooks
  const debugQuery = usePOST<{ answer: string }>(
    '/api/agent-builder/ai-assistant/debug-query',
    { showErrorToast: true }
  );

  const breakpointSuggestions = useGET<BreakpointSuggestion[]>(
    `/api/agent-builder/ai-assistant/${workflowId}/suggest-breakpoints`
  );

  const optimizations = useGET<OptimizationSuggestion[]>(
    `/api/agent-builder/ai-assistant/${workflowId}/suggest-optimizations`
  );

  const handleSendQuery = useCallback(async () => {
    if (!query.trim()) return;

    const userMessage: ChatMessage = { role: 'user', content: query };
    setChatHistory(prev => [...prev, userMessage]);
    setQuery('');

    const result = await debugQuery.execute({
      workflow_id: workflowId,
      query,
      workflow_context: {}
    });

    if (result) {
      const assistantMessage: ChatMessage = { 
        role: 'assistant', 
        content: result.answer 
      };
      setChatHistory(prev => [...prev, assistantMessage]);
    }
  }, [query, workflowId, debugQuery]);

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
          <Sparkles className="h-4 w-4 text-purple-500" aria-hidden="true" />
          AI Assistant
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col overflow-hidden">
        <Tabs defaultValue="chat" className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3" role="tablist">
            <TabsTrigger value="chat" role="tab">
              <MessageSquare className="h-4 w-4 mr-2" aria-hidden="true" />
              Chat
            </TabsTrigger>
            <TabsTrigger value="suggestions" role="tab">
              <Lightbulb className="h-4 w-4 mr-2" aria-hidden="true" />
              Suggestions
            </TabsTrigger>
            <TabsTrigger value="optimizations" role="tab">
              <TrendingUp className="h-4 w-4 mr-2" aria-hidden="true" />
              Optimize
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat" className="flex-1 flex flex-col overflow-hidden mt-4" role="tabpanel">
            <ScrollArea className="flex-1 mb-4">
              <div className="space-y-4" role="log" aria-live="polite">
                {chatHistory.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Sparkles className="h-12 w-12 mx-auto mb-2 text-purple-500" aria-hidden="true" />
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
                        role="article"
                        aria-label={`${message.role} message`}
                      >
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                      </div>
                    </div>
                  ))
                )}
                {debugQuery.isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-lg p-3">
                      <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading" />
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
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendQuery()}
                disabled={debugQuery.isLoading}
                aria-label="Chat input"
              />
              <Button 
                onClick={handleSendQuery} 
                disabled={debugQuery.isLoading || !query.trim()}
                aria-label="Send message"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </TabsContent>

          {/* Breakpoint Suggestions Tab */}
          <TabsContent value="suggestions" className="flex-1 overflow-hidden mt-4" role="tabpanel">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                AI-suggested breakpoints for debugging
              </p>
              <Button 
                size="sm" 
                onClick={() => breakpointSuggestions.execute()} 
                disabled={breakpointSuggestions.isLoading}
                aria-label="Refresh breakpoint suggestions"
              >
                {breakpointSuggestions.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading" />
                ) : (
                  'Refresh'
                )}
              </Button>
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {!breakpointSuggestions.data || breakpointSuggestions.data.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Lightbulb className="h-12 w-12 mx-auto mb-2 text-yellow-500" aria-hidden="true" />
                    <p className="text-sm">No suggestions yet</p>
                    <p className="text-xs mt-2">Click Refresh to get AI suggestions</p>
                  </div>
                ) : (
                  breakpointSuggestions.data.map((suggestion, index) => (
                    <Card key={index}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="h-4 w-4 text-blue-500" aria-hidden="true" />
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
                          aria-label={`Apply breakpoint to ${suggestion.node_id}`}
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
          <TabsContent value="optimizations" className="flex-1 overflow-hidden mt-4" role="tabpanel">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-muted-foreground">
                AI-suggested performance optimizations
              </p>
              <Button 
                size="sm" 
                onClick={() => optimizations.execute()} 
                disabled={optimizations.isLoading}
                aria-label="Analyze for optimizations"
              >
                {optimizations.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading" />
                ) : (
                  'Analyze'
                )}
              </Button>
            </div>

            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {!optimizations.data || optimizations.data.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <TrendingUp className="h-12 w-12 mx-auto mb-2 text-green-500" aria-hidden="true" />
                    <p className="text-sm">No optimizations yet</p>
                    <p className="text-xs mt-2">Click Analyze to get AI suggestions</p>
                  </div>
                ) : (
                  optimizations.data.map((opt, index) => (
                    <Card key={index}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <TrendingUp className="h-4 w-4 text-green-500" aria-hidden="true" />
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
