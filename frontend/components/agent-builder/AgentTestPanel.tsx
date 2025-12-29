'use client';

import React from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { Play, Loader2, Brain, Zap, Eye, MessageSquare, Plus, X, AlertCircle } from 'lucide-react';

interface AgentTestPanelProps {
  agentId: string;
  agentName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface AgentStep {
  step_id: string;
  type: 'thought' | 'action' | 'observation' | 'response';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

interface ExecutionMetrics {
  duration: number;
  tokens: number;
  toolCalls: number;
  status: 'success' | 'error';
}

export default function AgentTestPanel({ agentId, agentName, open, onOpenChange }: AgentTestPanelProps) {
  const [testQuery, setTestQuery] = React.useState('');
  const [contextVars, setContextVars] = React.useState<Array<{ key: string; value: string }>>([]);
  const [isRunning, setIsRunning] = React.useState(false);
  const [executionSteps, setExecutionSteps] = React.useState<AgentStep[]>([]);
  const [executionMetrics, setExecutionMetrics] = React.useState<ExecutionMetrics | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const addContextVar = () => {
    setContextVars([...contextVars, { key: '', value: '' }]);
  };

  const removeContextVar = (index: number) => {
    setContextVars(contextVars.filter((_, i) => i !== index));
  };

  const updateContextVar = (index: number, field: 'key' | 'value', value: string) => {
    const updated = [...contextVars];
    if (updated[index]) {
      updated[index][field] = value;
      setContextVars(updated);
    }
  };

  const handleRunTest = async () => {
    if (!testQuery.trim()) return;

    setIsRunning(true);
    setExecutionSteps([]);
    setExecutionMetrics(null);
    setError(null);

    try {
      const context = contextVars.reduce((acc, { key, value }) => {
        if (key) acc[key] = value;
        return acc;
      }, {} as Record<string, any>);

      const eventSource = await agentBuilderAPI.executeAgentStream(agentId, {
        query: testQuery,
        context,
      });

      const startTime = Date.now();

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'step') {
            setExecutionSteps((prev) => [...prev, data.step]);
          } else if (data.type === 'complete') {
            const duration = Date.now() - startTime;
            setExecutionMetrics({
              duration,
              tokens: data.tokens || 0,
              toolCalls: data.tool_calls || 0,
              status: 'success',
            });
            eventSource.close();
            setIsRunning(false);
          } else if (data.type === 'error') {
            setError(data.message);
            eventSource.close();
            setIsRunning(false);
          }
        } catch (err) {
          console.error('Failed to parse SSE data:', err);
        }
      };

      eventSource.onerror = () => {
        setError('Connection to server lost');
        eventSource.close();
        setIsRunning(false);
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute agent');
      setIsRunning(false);
    }
  };

  const getStepIcon = (type: string) => {
    switch (type) {
      case 'thought':
        return <Brain className="h-4 w-4 text-blue-500" />;
      case 'action':
        return <Zap className="h-4 w-4 text-yellow-500" />;
      case 'observation':
        return <Eye className="h-4 w-4 text-green-500" />;
      case 'response':
        return <MessageSquare className="h-4 w-4 text-purple-500" />;
      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Test Agent: {agentName}</DialogTitle>
          <DialogDescription>
            Run a test execution and see real-time results
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-6 overflow-auto">
          {/* Input Panel */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="test-query">Query</Label>
              <Textarea
                id="test-query"
                placeholder="Enter your test query..."
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                className="mt-2"
                rows={4}
              />
            </div>

            <div>
              <Label>Context Variables</Label>
              <Accordion type="single" collapsible className="mt-2">
                <AccordionItem value="variables">
                  <AccordionTrigger>
                    <span className="text-sm">Add context variables</span>
                  </AccordionTrigger>
                  <AccordionContent>
                    <div className="space-y-2">
                      {contextVars.map((v, i) => (
                        <div key={i} className="flex gap-2">
                          <Input
                            placeholder="Key"
                            value={v.key}
                            onChange={(e) => updateContextVar(i, 'key', e.target.value)}
                          />
                          <Input
                            placeholder="Value"
                            value={v.value}
                            onChange={(e) => updateContextVar(i, 'value', e.target.value)}
                          />
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeContextVar(i)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={addContextVar}
                      >
                        <Plus className="mr-2 h-4 w-4" />
                        Add Variable
                      </Button>
                    </div>
                  </AccordionContent>
                </AccordionItem>
              </Accordion>
            </div>

            <Button
              className="w-full"
              onClick={handleRunTest}
              disabled={isRunning || !testQuery.trim()}
            >
              {isRunning ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Test
                </>
              )}
            </Button>
          </div>

          {/* Results Panel */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>Execution Steps</Label>
              {executionMetrics && (
                <Badge variant="outline">
                  {executionMetrics.duration}ms
                </Badge>
              )}
            </div>

            <ScrollArea className="h-[400px] rounded-md border p-4">
              {error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : executionSteps.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <Play className="h-8 w-8 mb-2" />
                  <p className="text-sm">No execution yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {executionSteps.map((step, index) => (
                    <Card key={step.step_id}>
                      <CardHeader className="pb-3">
                        <div className="flex items-center gap-2">
                          {getStepIcon(step.type)}
                          <span className="text-sm font-medium capitalize">
                            {step.type}
                          </span>
                          <Badge variant="outline" className="ml-auto">
                            Step {index + 1}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm whitespace-pre-wrap">
                          {step.content}
                        </p>
                        {step.metadata && Object.keys(step.metadata).length > 0 && (
                          <details className="mt-2">
                            <summary className="text-xs text-muted-foreground cursor-pointer">
                              Metadata
                            </summary>
                            <pre className="text-xs bg-muted p-2 rounded mt-2 overflow-auto">
                              {JSON.stringify(step.metadata, null, 2)}
                            </pre>
                          </details>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </ScrollArea>

            {executionMetrics && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Execution Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Duration:</span>
                    <span className="font-medium">{executionMetrics.duration}ms</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tokens:</span>
                    <span className="font-medium">{executionMetrics.tokens}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Tool Calls:</span>
                    <span className="font-medium">{executionMetrics.toolCalls}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Status:</span>
                    <Badge variant={executionMetrics.status === 'success' ? 'default' : 'destructive'}>
                      {executionMetrics.status}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
