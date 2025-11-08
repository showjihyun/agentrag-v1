'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, Check, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { agentBuilderAPI, Execution, ExecutionStep, ExecutionMetrics } from '@/lib/api/agent-builder';

interface ExecutionComparisonProps {
  initialExecutionId?: string;
}

export function ExecutionComparison({ initialExecutionId }: ExecutionComparisonProps) {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [selectedExecution1, setSelectedExecution1] = useState<string>(initialExecutionId || '');
  const [selectedExecution2, setSelectedExecution2] = useState<string>('');
  const [execution1Data, setExecution1Data] = useState<{
    execution: Execution | null;
    steps: ExecutionStep[];
    metrics: ExecutionMetrics | null;
  }>({ execution: null, steps: [], metrics: null });
  const [execution2Data, setExecution2Data] = useState<{
    execution: Execution | null;
    steps: ExecutionStep[];
    metrics: ExecutionMetrics | null;
  }>({ execution: null, steps: [], metrics: null });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadExecutions();
  }, []);

  useEffect(() => {
    if (selectedExecution1) {
      loadExecutionData(selectedExecution1, 1);
    }
  }, [selectedExecution1]);

  useEffect(() => {
    if (selectedExecution2) {
      loadExecutionData(selectedExecution2, 2);
    }
  }, [selectedExecution2]);

  const loadExecutions = async () => {
    try {
      const { executions: executionsData } = await agentBuilderAPI.getExecutions();
      setExecutions(executionsData);
    } catch (error) {
      console.error('Failed to load executions:', error);
    }
  };

  const loadExecutionData = async (executionId: string, executionNumber: 1 | 2) => {
    setLoading(true);
    try {
      const [execution, steps, metrics] = await Promise.all([
        agentBuilderAPI.getExecution(executionId),
        agentBuilderAPI.getExecutionSteps(executionId),
        agentBuilderAPI.getExecutionMetrics(executionId),
      ]);

      if (executionNumber === 1) {
        setExecution1Data({ execution, steps, metrics });
      } else {
        setExecution2Data({ execution, steps, metrics });
      }
    } catch (error) {
      console.error('Failed to load execution data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const getDifference = (val1?: number, val2?: number) => {
    if (!val1 || !val2) return null;
    const diff = val1 - val2;
    const percent = ((diff / val2) * 100).toFixed(1);
    return { diff, percent };
  };

  const renderDifference = (val1?: number, val2?: number, unit: string = '') => {
    const difference = getDifference(val1, val2);
    if (!difference) return '-';

    const isPositive = difference.diff > 0;
    return (
      <div className={`text-sm ${isPositive ? 'text-red-500' : 'text-green-500'}`}>
        {isPositive ? '+' : ''}
        {difference.diff}
        {unit} ({difference.percent}%)
      </div>
    );
  };

  const compareSteps = () => {
    const steps1 = execution1Data.steps;
    const steps2 = execution2Data.steps;
    const maxLength = Math.max(steps1.length, steps2.length);

    return Array.from({ length: maxLength }, (_, i) => ({
      step1: steps1[i],
      step2: steps2[i],
      index: i,
    }));
  };

  return (
    <div className="space-y-6">
      {/* Execution Selectors */}
      <Card>
        <CardHeader>
          <CardTitle>Select Executions to Compare</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label>Execution 1</Label>
              <Select value={selectedExecution1} onValueChange={setSelectedExecution1}>
                <SelectTrigger className="mt-2">
                  <SelectValue placeholder="Select first execution" />
                </SelectTrigger>
                <SelectContent>
                  {executions.map((execution) => (
                    <SelectItem key={execution.id} value={execution.id}>
                      {execution.id.substring(0, 8)}... - {execution.agent_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Execution 2</Label>
              <Select value={selectedExecution2} onValueChange={setSelectedExecution2}>
                <SelectTrigger className="mt-2">
                  <SelectValue placeholder="Select second execution" />
                </SelectTrigger>
                <SelectContent>
                  {executions
                    .filter((e) => e.id !== selectedExecution1)
                    .map((execution) => (
                      <SelectItem key={execution.id} value={execution.id}>
                        {execution.id.substring(0, 8)}... - {execution.agent_name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {selectedExecution1 && selectedExecution2 && (
        <>
          {/* Metrics Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Metrics Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Metric</TableHead>
                    <TableHead>Execution 1</TableHead>
                    <TableHead>Execution 2</TableHead>
                    <TableHead>Difference</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell className="font-medium">Duration</TableCell>
                    <TableCell>{formatDuration(execution1Data.execution?.duration_ms)}</TableCell>
                    <TableCell>{formatDuration(execution2Data.execution?.duration_ms)}</TableCell>
                    <TableCell>
                      {renderDifference(
                        execution1Data.execution?.duration_ms,
                        execution2Data.execution?.duration_ms,
                        'ms'
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Status</TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          execution1Data.execution?.status === 'completed' ? 'default' : 'destructive'
                        }
                      >
                        {execution1Data.execution?.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          execution2Data.execution?.status === 'completed' ? 'default' : 'destructive'
                        }
                      >
                        {execution2Data.execution?.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {execution1Data.execution?.status === execution2Data.execution?.status ? (
                        <Check className="h-4 w-4 text-green-500" />
                      ) : (
                        <X className="h-4 w-4 text-red-500" />
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">LLM Calls</TableCell>
                    <TableCell>{execution1Data.metrics?.llm_call_count || 0}</TableCell>
                    <TableCell>{execution2Data.metrics?.llm_call_count || 0}</TableCell>
                    <TableCell>
                      {renderDifference(
                        execution1Data.metrics?.llm_call_count,
                        execution2Data.metrics?.llm_call_count
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Total Tokens</TableCell>
                    <TableCell>{execution1Data.metrics?.llm_total_tokens.toLocaleString() || 0}</TableCell>
                    <TableCell>{execution2Data.metrics?.llm_total_tokens.toLocaleString() || 0}</TableCell>
                    <TableCell>
                      {renderDifference(
                        execution1Data.metrics?.llm_total_tokens,
                        execution2Data.metrics?.llm_total_tokens
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Tool Calls</TableCell>
                    <TableCell>{execution1Data.metrics?.tool_call_count || 0}</TableCell>
                    <TableCell>{execution2Data.metrics?.tool_call_count || 0}</TableCell>
                    <TableCell>
                      {renderDifference(
                        execution1Data.metrics?.tool_call_count,
                        execution2Data.metrics?.tool_call_count
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell className="font-medium">Cache Hits</TableCell>
                    <TableCell>{execution1Data.metrics?.cache_hit_count || 0}</TableCell>
                    <TableCell>{execution2Data.metrics?.cache_hit_count || 0}</TableCell>
                    <TableCell>
                      {renderDifference(
                        execution1Data.metrics?.cache_hit_count,
                        execution2Data.metrics?.cache_hit_count
                      )}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Steps Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Steps Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {compareSteps().map(({ step1, step2, index }) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="outline">Step {index + 1}</Badge>
                        {step1 && step2 && step1.step_type === step2.step_type ? (
                          <Check className="h-4 w-4 text-green-500" />
                        ) : (
                          <X className="h-4 w-4 text-red-500" />
                        )}
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <div className="text-sm font-medium mb-2">Execution 1</div>
                          {step1 ? (
                            <div className="bg-muted p-3 rounded-md">
                              <div className="text-xs text-muted-foreground mb-1 capitalize">
                                {step1.step_type}
                              </div>
                              <div className="text-sm whitespace-pre-wrap">{step1.content}</div>
                            </div>
                          ) : (
                            <div className="bg-muted p-3 rounded-md text-sm text-muted-foreground">
                              No step at this position
                            </div>
                          )}
                        </div>

                        <div>
                          <div className="text-sm font-medium mb-2">Execution 2</div>
                          {step2 ? (
                            <div className="bg-muted p-3 rounded-md">
                              <div className="text-xs text-muted-foreground mb-1 capitalize">
                                {step2.step_type}
                              </div>
                              <div className="text-sm whitespace-pre-wrap">{step2.content}</div>
                            </div>
                          ) : (
                            <div className="bg-muted p-3 rounded-md text-sm text-muted-foreground">
                              No step at this position
                            </div>
                          )}
                        </div>
                      </div>

                      {step1 && step2 && step1.content !== step2.content && (
                        <div className="mt-3 flex items-center gap-2 text-sm text-yellow-600">
                          <ArrowRight className="h-4 w-4" />
                          <span>Content differs between executions</span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Output Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Output Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-medium mb-2">Execution 1 Output</div>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-[300px]">
                    {JSON.stringify(execution1Data.execution?.output_data, null, 2)}
                  </pre>
                </div>

                <div>
                  <div className="text-sm font-medium mb-2">Execution 2 Output</div>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-auto max-h-[300px]">
                    {JSON.stringify(execution2Data.execution?.output_data, null, 2)}
                  </pre>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
