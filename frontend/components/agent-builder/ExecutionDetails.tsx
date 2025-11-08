'use client';

import { useState, useEffect } from 'react';
import { Brain, Zap, Eye, MessageSquare, ChevronDown, Clock, User, Bot } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { agentBuilderAPI, Execution, ExecutionStep } from '@/lib/api/agent-builder';

interface ExecutionDetailsProps {
  executionId: string;
}

export function ExecutionDetails({ executionId }: ExecutionDetailsProps) {
  const [execution, setExecution] = useState<Execution | null>(null);
  const [steps, setSteps] = useState<ExecutionStep[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadExecutionDetails();
  }, [executionId]);

  const loadExecutionDetails = async () => {
    try {
      const [executionData, stepsData] = await Promise.all([
        agentBuilderAPI.getExecution(executionId),
        agentBuilderAPI.getExecutionSteps(executionId),
      ]);

      setExecution(executionData);
      setSteps(stepsData);
    } catch (error) {
      console.error('Failed to load execution details:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStepIcon = (stepType: string) => {
    switch (stepType) {
      case 'thought':
        return <Brain className="h-4 w-4 text-blue-500" />;
      case 'action':
        return <Zap className="h-4 w-4 text-yellow-500" />;
      case 'observation':
        return <Eye className="h-4 w-4 text-green-500" />;
      case 'response':
        return <MessageSquare className="h-4 w-4 text-purple-500" />;
      default:
        return <MessageSquare className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-muted-foreground">Loading execution details...</div>
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-muted-foreground">Execution not found</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Execution Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-muted-foreground">Execution ID</div>
              <div className="font-mono text-sm">{execution.id}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Status</div>
              <Badge
                variant={
                  execution.status === 'completed'
                    ? 'default'
                    : execution.status === 'running'
                    ? 'secondary'
                    : execution.status === 'failed'
                    ? 'destructive'
                    : 'outline'
                }
              >
                {execution.status}
              </Badge>
            </div>
            <div>
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <Bot className="h-4 w-4" />
                Agent
              </div>
              <div className="text-sm font-medium">{execution.agent_name || 'Unknown'}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <User className="h-4 w-4" />
                User
              </div>
              <div className="text-sm font-medium">{execution.user_id}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground flex items-center gap-2">
                <Clock className="h-4 w-4" />
                Duration
              </div>
              <div className="text-sm font-medium">{formatDuration(execution.duration_ms)}</div>
            </div>
            <div>
              <div className="text-sm text-muted-foreground">Started At</div>
              <div className="text-sm font-medium">{formatDate(execution.started_at)}</div>
            </div>
          </div>

          {execution.error_message && (
            <>
              <Separator />
              <div>
                <div className="text-sm text-muted-foreground mb-2">Error Message</div>
                <div className="bg-destructive/10 text-destructive p-3 rounded-md text-sm font-mono">
                  {execution.error_message}
                </div>
              </div>
            </>
          )}

          {execution.input_data && (
            <>
              <Separator />
              <div>
                <div className="text-sm text-muted-foreground mb-2">Input Data</div>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-auto">
                  {JSON.stringify(execution.input_data, null, 2)}
                </pre>
              </div>
            </>
          )}

          {execution.output_data && (
            <>
              <Separator />
              <div>
                <div className="text-sm text-muted-foreground mb-2">Output Data</div>
                <pre className="bg-muted p-3 rounded-md text-xs overflow-auto">
                  {JSON.stringify(execution.output_data, null, 2)}
                </pre>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Execution Steps Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px] pr-4">
            {steps.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <MessageSquare className="h-8 w-8 mb-2" />
                <p className="text-sm">No execution steps recorded</p>
              </div>
            ) : (
              <div className="space-y-4">
                {steps.map((step, index) => (
                  <Card key={step.id} className="border-l-4 border-l-primary/20">
                    <CardHeader className="pb-3">
                      <div className="flex items-center gap-2">
                        {getStepIcon(step.step_type)}
                        <span className="text-sm font-medium capitalize">{step.step_type}</span>
                        <Badge variant="outline" className="ml-auto">
                          Step {step.step_number}
                        </Badge>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {new Date(step.timestamp).toLocaleTimeString()}
                      </div>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm whitespace-pre-wrap">{step.content}</p>

                      {step.metadata && Object.keys(step.metadata).length > 0 && (
                        <Accordion type="single" collapsible className="mt-3">
                          <AccordionItem value="metadata">
                            <AccordionTrigger className="text-sm">
                              View Metadata
                            </AccordionTrigger>
                            <AccordionContent>
                            <div className="mt-2">
                              {/* LangGraph State */}
                              {step.metadata.state && (
                                <div className="mb-3">
                                  <div className="text-xs font-semibold text-muted-foreground mb-1">
                                    LangGraph State
                                  </div>
                                  <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-[200px]">
                                    {JSON.stringify(step.metadata.state, null, 2)}
                                  </pre>
                                </div>
                              )}

                              {/* Tool Calls */}
                              {step.metadata.tool_call && (
                                <div className="mb-3">
                                  <div className="text-xs font-semibold text-muted-foreground mb-1">
                                    Tool Call
                                  </div>
                                  <div className="bg-muted p-2 rounded space-y-2">
                                    <div>
                                      <span className="text-xs font-medium">Tool:</span>
                                      <span className="text-xs ml-2">{step.metadata.tool_call.name}</span>
                                    </div>
                                    <div>
                                      <span className="text-xs font-medium">Parameters:</span>
                                      <pre className="text-xs mt-1 overflow-auto">
                                        {JSON.stringify(step.metadata.tool_call.parameters, null, 2)}
                                      </pre>
                                    </div>
                                    {step.metadata.tool_call.response && (
                                      <div>
                                        <span className="text-xs font-medium">Response:</span>
                                        <pre className="text-xs mt-1 overflow-auto max-h-[150px]">
                                          {JSON.stringify(step.metadata.tool_call.response, null, 2)}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              )}

                              {/* Other Metadata */}
                              {Object.keys(step.metadata).filter(
                                (key) => key !== 'state' && key !== 'tool_call'
                              ).length > 0 && (
                                <div>
                                  <div className="text-xs font-semibold text-muted-foreground mb-1">
                                    Additional Metadata
                                  </div>
                                  <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-[200px]">
                                    {JSON.stringify(
                                      Object.fromEntries(
                                        Object.entries(step.metadata).filter(
                                          ([key]) => key !== 'state' && key !== 'tool_call'
                                        )
                                      ),
                                      null,
                                      2
                                    )}
                                  </pre>
                                </div>
                              )}
                            </div>
                            </AccordionContent>
                          </AccordionItem>
                        </Accordion>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}
