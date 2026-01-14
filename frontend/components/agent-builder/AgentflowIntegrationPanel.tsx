'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  RefreshCw,
  Play,
  Users,
  GitBranch,
  Clock,
  Target,
  Zap,
} from 'lucide-react';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import type { ValidationReport, ExecutionPlan } from '@/lib/api/agent-builder';

interface AgentflowIntegrationPanelProps {
  agentflowId: string;
  onExecute?: () => void;
}

export function AgentflowIntegrationPanel({
  agentflowId,
  onExecute,
}: AgentflowIntegrationPanelProps) {
  const [activeTab, setActiveTab] = useState<'validation' | 'execution' | 'monitoring'>('validation');

  // Fetch validation report
  const {
    data: validationReport,
    isLoading: validationLoading,
    refetch: refetchValidation,
  } = useQuery({
    queryKey: ['agentflow-validation', agentflowId],
    queryFn: () => agentBuilderAPI.validateAgentflowIntegrity(agentflowId),
    enabled: !!agentflowId,
  });

  // Fetch execution plan
  const {
    data: executionPlan,
    isLoading: executionLoading,
    refetch: refetchExecution,
  } = useQuery({
    queryKey: ['agentflow-execution-plan', agentflowId],
    queryFn: () => agentBuilderAPI.getAgentflowExecutionPlan(agentflowId),
    enabled: !!agentflowId,
  });

  const handleRefresh = () => {
    refetchValidation();
    refetchExecution();
  };

  const renderValidationReport = () => {
    if (validationLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span className="ml-2">Validating...</span>
        </div>
      );
    }

    if (!validationReport) return null;

    const isValid = validationReport.validation_status === 'valid';

    return (
      <div className="space-y-4">
        {/* Status Overview */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                {isValid ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertTriangle className="h-5 w-5 text-red-500" />
                )}
                Validation Status
              </CardTitle>
              <Badge variant={isValid ? 'default' : 'destructive'}>
                {isValid ? 'Valid' : 'Issues Found'}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Agent Count:</span>
                <span className="ml-2 font-medium">{validationReport.agent_count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Connection Count:</span>
                <span className="ml-2 font-medium">{validationReport.edge_count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Orchestration:</span>
                <span className="ml-2 font-medium">{validationReport.orchestration_type}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Issues */}
        {validationReport.issues.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-red-500" />
                Issues Found ({validationReport.issues.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-32">
                <ul className="space-y-2">
                  {validationReport.issues.map((issue: any, index: number) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        {validationReport.recommendations.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Info className="h-5 w-5 text-blue-500" />
                Recommendations ({validationReport.recommendations.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-32">
                <ul className="space-y-2">
                  {validationReport.recommendations.map((recommendation: any, index: number) => (
                    <li key={index} className="flex items-start gap-2 text-sm">
                      <Info className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                      <span>{recommendation}</span>
                    </li>
                  ))}
                </ul>
              </ScrollArea>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  const renderExecutionPlan = () => {
    if (executionLoading) {
      return (
        <div className="flex items-center justify-center py-8">
          <RefreshCw className="h-6 w-6 animate-spin" />
          <span className="ml-2">Generating execution plan...</span>
        </div>
      );
    }

    if (!executionPlan) return null;

    return (
      <div className="space-y-4">
        {/* Plan Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Target className="h-5 w-5" />
              Execution Plan Overview
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Orchestration:</span>
                <span className="ml-2 font-medium">{executionPlan.orchestration_type}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Total Agents:</span>
                <span className="ml-2 font-medium">{executionPlan.total_agents}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Total Connections:</span>
                <span className="ml-2 font-medium">{executionPlan.total_edges}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Supervisor:</span>
                <span className="ml-2 font-medium">
                  {executionPlan.supervisor_config?.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Execution Steps */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <GitBranch className="h-5 w-5" />
              Execution Steps
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Accordion type="single" collapsible className="w-full">
              {Array.isArray(executionPlan.execution_plan) ? (
                executionPlan.execution_plan.map((step: any, index: number) => (
                  <AccordionItem key={index} value={`step-${index}`}>
                    <AccordionTrigger className="text-left">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">Step {step.step || index + 1}</Badge>
                        <span>{step.name || step.execution_type}</span>
                        {step.execution_type === 'parallel' && (
                          <Badge variant="secondary">Parallel</Badge>
                        )}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-2 text-sm">
                        {step.agents ? (
                          <div>
                            <span className="font-medium">Agents:</span>
                            <ul className="mt-1 space-y-1">
                              {step.agents.map((agent: any, agentIndex: number) => (
                                <li key={agentIndex} className="flex items-center gap-2 ml-4">
                                  <Users className="h-3 w-3" />
                                  <span>{agent.name}</span>
                                  <Badge variant="outline" className="text-xs">
                                    {agent.role}
                                  </Badge>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <Users className="h-4 w-4" />
                            <span>{step.name}</span>
                            <Badge variant="outline">{step.role}</Badge>
                          </div>
                        )}
                        
                        {step.dependencies && step.dependencies.length > 0 && (
                          <div>
                            <span className="font-medium">Dependencies:</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {step.dependencies.map((dep: string, depIndex: number) => (
                                <Badge key={depIndex} variant="secondary" className="text-xs">
                                  {dep}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))
              ) : (
                <div className="text-center py-4 text-muted-foreground">
                  Unable to load execution plan.
                </div>
              )}
            </Accordion>
          </CardContent>
        </Card>

        {/* Supervisor Configuration */}
        {executionPlan.supervisor_config?.enabled && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Supervisor Configuration
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">LLM Provider:</span>
                  <span className="ml-2 font-medium">
                    {executionPlan.supervisor_config.llm_provider || 'ollama'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Model:</span>
                  <span className="ml-2 font-medium">
                    {executionPlan.supervisor_config.llm_model || 'llama3.1'}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Max Iterations:</span>
                  <span className="ml-2 font-medium">
                    {executionPlan.supervisor_config.max_iterations || 10}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground">Decision Strategy:</span>
                  <span className="ml-2 font-medium">
                    {executionPlan.supervisor_config.decision_strategy || 'llm_based'}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Integration Management</h3>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          {onExecute && (
            <Button size="sm" onClick={onExecute}>
              <Play className="h-4 w-4 mr-2" />
              Execute
            </Button>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-muted p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('validation')}
          className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'validation'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Validation Report
        </button>
        <button
          onClick={() => setActiveTab('execution')}
          className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'execution'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Execution Plan
        </button>
        <button
          onClick={() => setActiveTab('monitoring')}
          className={`flex-1 px-3 py-2 text-sm font-medium rounded-md transition-colors ${
            activeTab === 'monitoring'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Monitoring
        </button>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'validation' && renderValidationReport()}
        {activeTab === 'execution' && renderExecutionPlan()}
        {activeTab === 'monitoring' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Real-time Monitoring
              </CardTitle>
              <CardDescription>
                Monitor the status of running workflows in real-time.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                Monitoring feature coming soon.
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}