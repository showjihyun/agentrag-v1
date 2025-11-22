'use client';

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
  Send,
  Loader2,
} from 'lucide-react';
import { useAIAssistant } from '@/hooks/useAIAssistant';
import { Node, Edge } from 'reactflow';

interface ImprovedAIAssistantPanelProps {
  workflowId: string;
  nodes: Node[];
  edges: Edge[];
  selectedNodes: Node[];
  onApplySuggestion?: (suggestion: any) => void;
}

export function ImprovedAIAssistantPanel({
  workflowId,
  nodes,
  edges,
  selectedNodes,
  onApplySuggestion,
}: ImprovedAIAssistantPanelProps) {
  const {
    chatHistory,
    query,
    setQuery,
    sendQuery,
    clearChat,
    breakpointSuggestions,
    isLoadingBreakpoints,
    fetchBreakpoints,
    optimizationSuggestions,
    isLoadingOptimizations,
    fetchOptimizations,
    isLoading,
  } = useAIAssistant(workflowId);

  const handleSendQuery = async () => {
    if (!query.trim()) return;
    await sendQuery(query);
    setQuery('');
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'destructive';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
      default:
        return 'default';
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'easy':
        return 'default';
      case 'medium':
        return 'secondary';
      case 'hard':
        return 'destructive';
      default:
        return 'outline';
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
            <TabsTrigger value="breakpoints">
              <AlertCircle className="h-4 w-4 mr-2" />
              Breakpoints
            </TabsTrigger>
            <TabsTrigger value="optimize">
              <Lightbulb className="h-4 w-4 mr-2" />
              Optimize
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat" className="flex-1 flex flex-col space-y-4">
            <ScrollArea className="flex-1 pr-4">
              <div className="space-y-4">
                {chatHistory.length === 0 ? (
                  <div className="text-center text-muted-foreground py-8">
                    <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Ask me anything about your workflow!</p>
                  </div>
                ) : (
                  chatHistory.map((message, index) => (
                    <div
                      key={index}
                      className={`flex ${
                        message.role === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${
                          message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                        }`}
                      >
                        <p className="text-sm">{message.content}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>

            <div className="flex gap-2">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendQuery();
                  }
                }}
                placeholder="Ask about your workflow..."
                disabled={isLoading}
              />
              <Button
                onClick={handleSendQuery}
                disabled={isLoading || !query.trim()}
                size="icon"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </TabsContent>

          {/* Breakpoints Tab */}
          <TabsContent value="breakpoints" className="flex-1 flex flex-col space-y-4">
            <Button
              onClick={fetchBreakpoints}
              disabled={isLoadingBreakpoints}
              className="w-full"
            >
              {isLoadingBreakpoints ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Suggest Breakpoints'
              )}
            </Button>

            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {breakpointSuggestions?.map((suggestion, index) => (
                  <Card key={index}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <Badge variant={getPriorityColor(suggestion.priority)}>
                          {suggestion.priority}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium mb-2">
                        Node: {suggestion.node_id}
                      </p>
                      <p className="text-sm text-muted-foreground mb-3">
                        {suggestion.reason}
                      </p>
                      {suggestion.condition && (
                        <code className="text-xs bg-muted p-2 rounded block mb-3">
                          {suggestion.condition}
                        </code>
                      )}
                      <Button
                        size="sm"
                        onClick={() => onApplySuggestion?.(suggestion)}
                        className="w-full"
                      >
                        Apply Breakpoint
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Optimize Tab */}
          <TabsContent value="optimize" className="flex-1 flex flex-col space-y-4">
            <Button
              onClick={fetchOptimizations}
              disabled={isLoadingOptimizations}
              className="w-full"
            >
              {isLoadingOptimizations ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Analyze Performance'
              )}
            </Button>

            <ScrollArea className="flex-1">
              <div className="space-y-3">
                {optimizationSuggestions?.map((suggestion, index) => (
                  <Card key={index}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <Badge
                          variant={getDifficultyColor(
                            suggestion.implementation_difficulty
                          )}
                        >
                          {suggestion.implementation_difficulty}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium mb-2">
                        Node: {suggestion.node_id}
                      </p>
                      <p className="text-sm text-red-600 mb-2">
                        Issue: {suggestion.issue}
                      </p>
                      <p className="text-sm text-muted-foreground mb-2">
                        {suggestion.suggestion}
                      </p>
                      <p className="text-sm text-green-600 mb-3">
                        Expected: {suggestion.expected_improvement}
                      </p>
                      {suggestion.code_example && (
                        <pre className="text-xs bg-muted p-2 rounded overflow-x-auto mb-3">
                          {suggestion.code_example}
                        </pre>
                      )}
                      <Button
                        size="sm"
                        onClick={() => onApplySuggestion?.(suggestion)}
                        className="w-full"
                      >
                        Apply Optimization
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
