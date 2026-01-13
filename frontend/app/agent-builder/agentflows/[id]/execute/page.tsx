'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft,
  Play,
  Square,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Loader2,
  Download,
  RefreshCw,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';

interface ExecutionStep {
  id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  input?: any;
  output?: any;
  error?: string;
}

interface LocalExecutionStep {
  id: string;
  agent_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  input?: any;
  output?: string;
  error?: string;
}

interface ExecutionState {
  id?: string;
  status: 'idle' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  steps: LocalExecutionStep[];
  result?: any;
  error?: string;
}

export default function AgentflowExecutePage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { toast } = useToast();
  
  // Unwrap params using React.use()
  const { id } = React.use(params);
  
  const [input, setInput] = useState('');
  const [execution, setExecution] = useState<ExecutionState>({
    status: 'idle',
    steps: [],
  });

  const { data: flowData, isLoading } = useQuery({
    queryKey: ['agentflow', id],
    queryFn: () => flowsAPI.getFlow(id),
  });

  const flow = flowData as any;

  const handleExecute = async () => {
    if (!input.trim()) {
      toast({
        title: 'Input Required',
        description: 'Please provide input to execute',
        variant: 'destructive',
      });
      return;
    }

    try {
      setExecution({
        status: 'running',
        started_at: new Date().toISOString(),
        steps: [],
      });

      // Simulated execution process
      const agents = flow?.agents || [
        { name: 'Data Collection Agent', role: 'collector' },
        { name: 'Analysis Agent', role: 'analyzer' },
        { name: 'Result Generation Agent', role: 'generator' },
      ];

      for (let i = 0; i < agents.length; i++) {
        const agent = agents[i];
        const stepId = `step-${i + 1}`;
        
        // Step start
        setExecution(prev => ({
          ...prev,
          steps: [
            ...prev.steps,
            {
              id: stepId,
              agent_name: agent.name,
              status: 'running',
              started_at: new Date().toISOString(),
            }
          ]
        }));

        // Simulation delay
        await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 3000));

        // Step completion (90% success rate)
        const success = Math.random() > 0.1;
        
        setExecution(prev => ({
          ...prev,
          steps: prev.steps.map(step => 
            step.id === stepId 
              ? {
                  ...step,
                  status: (success ? 'completed' : 'failed') as LocalExecutionStep['status'],
                  completed_at: new Date().toISOString(),
                  duration_ms: 2000 + Math.random() * 3000,
                  ...(success 
                    ? { output: `${agent.name} processing completed` }
                    : { error: `Error occurred while processing ${agent.name}` }
                  ),
                }
              : step
          )
        }));

        if (!success) {
          setExecution(prev => ({
            ...prev,
            status: 'failed',
            completed_at: new Date().toISOString(),
            error: `Execution failed at ${agent.name}`,
          }));
          return;
        }
      }

      // Overall execution completion
      setExecution(prev => ({
        ...prev,
        status: 'completed',
        completed_at: new Date().toISOString(),
        result: {
          message: 'Agentflow execution completed successfully',
          processed_input: input,
          agents_executed: agents.length,
          total_duration: prev.steps.reduce((sum, step) => sum + (step.duration_ms || 0), 0),
        }
      }));

      toast({
        title: 'Execution Complete',
        description: 'Agentflow executed successfully',
      });

    } catch (error: any) {
      setExecution(prev => ({
        ...prev,
        status: 'failed',
        completed_at: new Date().toISOString(),
        error: error.message || 'An error occurred during execution',
      }));

      toast({
        title: 'Execution Failed',
        description: error.message || 'An error occurred during execution',
        variant: 'destructive',
      });
    }
  };

  const handleStop = () => {
    setExecution(prev => ({
      ...prev,
      status: 'failed',
      completed_at: new Date().toISOString(),
      error: 'Cancelled by user',
    }));
  };

  const handleReset = () => {
    setExecution({
      status: 'idle',
      steps: [],
    });
    setInput('');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-gray-400" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'border-blue-500 bg-blue-50 dark:bg-blue-950/20';
      case 'completed':
        return 'border-green-500 bg-green-50 dark:bg-green-950/20';
      case 'failed':
        return 'border-red-500 bg-red-50 dark:bg-red-950/20';
      default:
        return 'border-gray-200 bg-gray-50 dark:bg-gray-900/20';
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Skeleton className="h-12 w-full mb-6" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!flow) {
    return (
      <div className="container mx-auto p-6 max-w-6xl">
        <Card className="border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">Failed to load Agentflow</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Activity className="h-7 w-7 text-purple-600 dark:text-purple-400" />
            </div>
            {flow.name} Execution
          </h1>
          <p className="text-muted-foreground mt-1">{flow.description || 'No description'}</p>
        </div>
        <div className="flex gap-2">
          {execution.status === 'running' ? (
            <Button variant="destructive" onClick={handleStop}>
              <Square className="h-4 w-4 mr-2" />
              Stop
            </Button>
          ) : (
            <>
              {execution.status !== 'idle' && (
                <Button variant="outline" onClick={handleReset}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reset
                </Button>
              )}
              <Button 
                onClick={handleExecute}
                disabled={execution.status !== 'idle'}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                <Play className="h-4 w-4 mr-2" />
                Execute
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Section */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Input</CardTitle>
              <CardDescription>Write the input to pass to the Agentflow</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="input">Execution Input</Label>
                <Textarea
                  id="input"
                  placeholder="e.g., Please write a report on the latest AI trends"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  rows={6}
                  disabled={execution.status === 'running'}
                />
              </div>
              
              {/* Flow Info */}
              <Separator />
              <div className="space-y-2">
                <h4 className="font-medium">Flow Information</h4>
                <div className="text-sm text-muted-foreground space-y-1">
                  <p>Orchestration: {flow.orchestration_type}</p>
                  <p>Agent Count: {flow.agents?.length || 0}</p>
                  <p>Status: {flow.is_active ? 'Active' : 'Inactive'}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Execution Section */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    Execution Status
                    {execution.status === 'running' && (
                      <Badge variant="secondary" className="animate-pulse">
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Running
                      </Badge>
                    )}
                    {execution.status === 'completed' && (
                      <Badge className="bg-green-500">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        Completed
                      </Badge>
                    )}
                    {execution.status === 'failed' && (
                      <Badge variant="destructive">
                        <XCircle className="h-3 w-3 mr-1" />
                        Failed
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>
                    {execution.started_at && (
                      <>Started: {new Date(execution.started_at).toLocaleString()}</>
                    )}
                    {execution.completed_at && (
                      <> | Completed: {new Date(execution.completed_at).toLocaleString()}</>
                    )}
                  </CardDescription>
                </div>
                {execution.status === 'completed' && (
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Download Results
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {execution.status === 'idle' ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>Click the execute button to start the Agentflow</p>
                </div>
              ) : (
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {/* Execution Steps */}
                    {execution.steps.map((step, index) => (
                      <Card key={step.id} className={`border-2 ${getStatusColor(step.status)}`}>
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-3">
                            <div className="flex-shrink-0 mt-1">
                              {getStatusIcon(step.status)}
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <h4 className="font-medium">{step.agent_name}</h4>
                                <Badge variant="outline" className="text-xs">
                                  Step {index + 1}
                                </Badge>
                              </div>
                              {step.started_at && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Started: {new Date(step.started_at).toLocaleTimeString()}
                                  {step.duration_ms && (
                                    <> | Duration: {(step.duration_ms / 1000).toFixed(1)}s</>
                                  )}
                                </p>
                              )}
                              {step.output && (
                                <div className="mt-2 p-2 bg-green-50 dark:bg-green-950/20 rounded text-sm">
                                  {step.output}
                                </div>
                              )}
                              {step.error && (
                                <div className="mt-2 p-2 bg-red-50 dark:bg-red-950/20 rounded text-sm text-red-700 dark:text-red-300">
                                  {step.error}
                                </div>
                              )}
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}

                    {/* Final Result */}
                    {execution.result && (
                      <Card className="border-2 border-green-500 bg-green-50 dark:bg-green-950/20">
                        <CardHeader>
                          <CardTitle className="text-green-700 dark:text-green-300 flex items-center gap-2">
                            <CheckCircle className="h-5 w-5" />
                            Execution Results
                          </CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <p className="font-medium">{execution.result.message}</p>
                            <div className="text-sm text-muted-foreground">
                              <p>Processed Input: {execution.result.processed_input}</p>
                              <p>Executed Agents: {execution.result.agents_executed}</p>
                              <p>Total Duration: {(execution.result.total_duration / 1000).toFixed(1)}s</p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}

                    {/* Error */}
                    {execution.error && (
                      <Card className="border-2 border-red-500 bg-red-50 dark:bg-red-950/20">
                        <CardContent className="pt-4">
                          <div className="flex items-start gap-3">
                            <AlertTriangle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                            <div>
                              <h4 className="font-medium text-red-700 dark:text-red-300">Execution Error</h4>
                              <p className="text-sm text-red-600 dark:text-red-400 mt-1">
                                {execution.error}
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}