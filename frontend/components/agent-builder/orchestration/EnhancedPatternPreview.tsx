/**
 * Enhanced Pattern Preview
 * Enhanced pattern preview component
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Eye,
  Users,
  MessageSquare,
  Zap,
  Clock,
  Target,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Info,
  Play,
  Settings,
  BarChart3,
  Network,
  Shield
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ORCHESTRATION_TYPES,
  AGENT_ROLES,
  type OrchestrationTypeValue,
  type AgentRole,
} from '@/lib/constants/orchestration';

interface OrchestrationConfig {
  orchestrationType: OrchestrationTypeValue;
  name: string;
  description: string;
  supervisorConfig: {
    enabled: boolean;
    llm_provider: string;
    llm_model: string;
    decision_strategy: string;
    max_iterations: number;
  };
  agentRoles: Array<{
    id: string;
    name: string;
    role: AgentRole;
    priority: number;
    maxRetries: number;
    timeoutSeconds: number;
    dependencies: string[];
  }>;
  communicationRules: {
    allowDirectCommunication: boolean;
    enableBroadcast: boolean;
    requireConsensus: boolean;
    maxNegotiationRounds: number;
  };
  performanceThresholds: {
    maxExecutionTime: number;
    minSuccessRate: number;
    maxTokenUsage: number;
  };
  tags: string[];
}

interface EnhancedPatternPreviewProps {
  config: OrchestrationConfig;
  className?: string;
  showExecutionFlow?: boolean;
  showPerformanceMetrics?: boolean;
  onExecuteTest?: () => void;
  onEditConfig?: () => void;
}

export function EnhancedPatternPreview({
  config,
  className,
  showExecutionFlow = true,
  showPerformanceMetrics = true,
  onExecuteTest,
  onEditConfig
}: EnhancedPatternPreviewProps) {
  const [activeTab, setActiveTab] = useState('overview');
  const [simulationRunning, setSimulationRunning] = useState(false);
  
  const pattern = ORCHESTRATION_TYPES[config.orchestrationType];
  
  // Configuration analysis
  const configAnalysis = analyzeConfiguration(config);
  
  // Run simulation
  const runSimulation = async () => {
    setSimulationRunning(true);
    // Simulation logic (actual API call in production)
    await new Promise(resolve => setTimeout(resolve, 2000));
    setSimulationRunning(false);
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-xl font-semibold">{config.name}</h3>
          <p className="text-sm text-gray-600">{pattern.name} Pattern</p>
        </div>
        <div className="flex gap-2">
          {onEditConfig && (
            <Button variant="outline" onClick={onEditConfig}>
              <Settings className="w-4 h-4 mr-2" />
              Edit Settings
            </Button>
          )}
          {onExecuteTest && (
            <Button onClick={onExecuteTest}>
              <Play className="w-4 h-4 mr-2" />
              Run Test
            </Button>
          )}
        </div>
      </div>

      {/* Configuration Analysis Summary */}
      <Card className={cn(
        "border-l-4",
        configAnalysis.overallScore >= 80 && "border-l-green-500 bg-green-50",
        configAnalysis.overallScore >= 60 && configAnalysis.overallScore < 80 && "border-l-yellow-500 bg-yellow-50",
        configAnalysis.overallScore < 60 && "border-l-red-500 bg-red-50"
      )}>
        <CardContent className="pt-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              {configAnalysis.overallScore >= 80 ? (
                <CheckCircle2 className="w-5 h-5 text-green-600" />
              ) : configAnalysis.overallScore >= 60 ? (
                <AlertTriangle className="w-5 h-5 text-yellow-600" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-red-600" />
              )}
              <span className="font-medium">Configuration Analysis Result</span>
            </div>
            <Badge variant={
              configAnalysis.overallScore >= 80 ? "default" :
              configAnalysis.overallScore >= 60 ? "secondary" : "destructive"
            }>
              {configAnalysis.overallScore} points
            </Badge>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <div className="font-medium text-gray-700 mb-1">Strengths</div>
              <ul className="space-y-1">
                {configAnalysis.strengths.map((strength, index) => (
                  <li key={index} className="flex items-center gap-1 text-green-700">
                    <CheckCircle2 className="w-3 h-3" />
                    {strength}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <div className="font-medium text-gray-700 mb-1">Improvements</div>
              <ul className="space-y-1">
                {configAnalysis.improvements.map((improvement, index) => (
                  <li key={index} className="flex items-center gap-1 text-yellow-700">
                    <AlertTriangle className="w-3 h-3" />
                    {improvement}
                  </li>
                ))}
              </ul>
            </div>
            
            <div>
              <div className="font-medium text-gray-700 mb-1">Expected Performance</div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Response Time</span>
                  <span className="font-medium">{configAnalysis.estimatedResponseTime}</span>
                </div>
                <div className="flex justify-between">
                  <span>Success Rate</span>
                  <span className="font-medium">{configAnalysis.estimatedSuccessRate}</span>
                </div>
                <div className="flex justify-between">
                  <span>Cost Efficiency</span>
                  <span className="font-medium">{configAnalysis.costEfficiency}</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Detail Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="agents">Agent Configuration</TabsTrigger>
          <TabsTrigger value="flow">Execution Flow</TabsTrigger>
          <TabsTrigger value="metrics">Performance Metrics</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Info className="w-4 h-4" />
                  Basic Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-sm font-medium text-gray-700">Description</div>
                  <p className="text-sm text-gray-600">{config.description || 'No description available.'}</p>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700 mb-1">Tags</div>
                  <div className="flex flex-wrap gap-1">
                    {config.tags.map((tag, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <div className="text-sm font-medium text-gray-700">Pattern Characteristics</div>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className="text-xs">
                      <Clock className="w-3 h-3 mr-1" />
                      {pattern.estimated_setup_time}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      <Target className="w-3 h-3 mr-1" />
                      {pattern.complexity}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="w-4 h-4" />
                  Supervisor Settings
                </CardTitle>
              </CardHeader>
              <CardContent>
                {config.supervisorConfig.enabled ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status</span>
                      <Badge className="bg-green-100 text-green-700">Enabled</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">LLM</span>
                      <span className="font-medium">
                        {config.supervisorConfig.llm_provider} / {config.supervisorConfig.llm_model}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Strategy</span>
                      <span className="font-medium">{config.supervisorConfig.decision_strategy}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Max Iterations</span>
                      <span className="font-medium">{config.supervisorConfig.max_iterations}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 text-center py-4">
                    Supervisor is disabled
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Agent Configuration Tab */}
        <TabsContent value="agents" className="space-y-4">
          <div className="grid grid-cols-1 gap-4">
            {config.agentRoles.map((agent, index) => (
              <Card key={agent.id}>
                <CardContent className="pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Users className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">{agent.name}</h4>
                        <p className="text-sm text-gray-600">{AGENT_ROLES[agent.role].name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">Priority {agent.priority}</Badge>
                      <Badge variant="secondary">{AGENT_ROLES[agent.role].category}</Badge>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Max Retries</div>
                      <div className="font-medium">{agent.maxRetries}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Timeout</div>
                      <div className="font-medium">{agent.timeoutSeconds} seconds</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Dependencies</div>
                      <div className="font-medium">
                        {agent.dependencies.length > 0 ? `${agent.dependencies.length}` : 'None'}
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-600">
                    {AGENT_ROLES[agent.role].description}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Execution Flow Tab */}
        <TabsContent value="flow" className="space-y-4">
          {showExecutionFlow && (
            <ExecutionFlowVisualization 
              config={config} 
              isSimulating={simulationRunning}
              onRunSimulation={runSimulation}
            />
          )}
        </TabsContent>

        {/* Performance Metrics Tab */}
        <TabsContent value="metrics" className="space-y-4">
          {showPerformanceMetrics && (
            <PerformanceMetricsView config={config} />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Configuration analysis function
function analyzeConfiguration(config: OrchestrationConfig) {
  const strengths: string[] = [];
  const improvements: string[] = [];
  let score = 0;

  // Agent configuration analysis
  if (config.agentRoles.length >= 2) {
    strengths.push('Adequate number of agents');
    score += 20;
  } else {
    improvements.push('Insufficient number of agents');
  }

  // Supervisor analysis
  if (config.supervisorConfig.enabled) {
    strengths.push('Supervisor enabled');
    score += 15;
  }

  // Communication rules analysis
  if (config.communicationRules.allowDirectCommunication) {
    strengths.push('Efficient communication setup');
    score += 10;
  }

  // Performance threshold analysis
  if (config.performanceThresholds.minSuccessRate >= 0.8) {
    strengths.push('High success rate target');
    score += 15;
  }

  if (config.performanceThresholds.maxExecutionTime <= 300000) {
    strengths.push('Appropriate execution time limit');
    score += 10;
  }

  // Tags and documentation
  if (config.tags.length > 0) {
    strengths.push('Proper tag configuration');
    score += 5;
  }

  if (config.description && config.description.length > 10) {
    strengths.push('Detailed description');
    score += 5;
  }

  // Add improvements
  if (score < 60) {
    improvements.push('Overall configuration improvement needed');
  }

  if (!config.supervisorConfig.enabled && config.agentRoles.length > 3) {
    improvements.push('Consider Supervisor for managing multiple agents');
  }

  return {
    overallScore: Math.min(score + 20, 100), // Add 20 base points
    strengths,
    improvements,
    estimatedResponseTime: calculateEstimatedResponseTime(config),
    estimatedSuccessRate: `${Math.round(config.performanceThresholds.minSuccessRate * 100)}%`,
    costEfficiency: calculateCostEfficiency(config)
  };
}

function calculateEstimatedResponseTime(config: OrchestrationConfig): string {
  const baseTime = 2000; // 2 seconds base
  const agentFactor = config.agentRoles.length * 500; // 0.5 seconds per agent
  const supervisorFactor = config.supervisorConfig.enabled ? 1000 : 0; // 1 second for supervisor
  
  const totalMs = baseTime + agentFactor + supervisorFactor;
  return `${(totalMs / 1000).toFixed(1)} seconds`;
}

function calculateCostEfficiency(config: OrchestrationConfig): string {
  let efficiency = 'Medium';
  
  if (config.performanceThresholds.maxTokenUsage < 5000) {
    efficiency = 'High';
  } else if (config.performanceThresholds.maxTokenUsage > 15000) {
    efficiency = 'Low';
  }
  
  return efficiency;
}

// Execution flow visualization component
function ExecutionFlowVisualization({ 
  config, 
  isSimulating, 
  onRunSimulation 
}: { 
  config: OrchestrationConfig; 
  isSimulating: boolean;
  onRunSimulation: () => void;
}) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            Execution Flow Simulation
          </CardTitle>
          <Button 
            onClick={onRunSimulation} 
            disabled={isSimulating}
            size="sm"
          >
            {isSimulating ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Simulating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                Run Simulation
              </>
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {config.agentRoles
            .sort((a, b) => a.priority - b.priority)
            .map((agent, index) => (
              <div key={agent.id} className="flex items-center gap-4">
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
                  isSimulating && index === 0 ? "bg-blue-500 animate-pulse" : "bg-gray-400"
                )}>
                  {index + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-sm text-gray-600">{AGENT_ROLES[agent.role].name}</div>
                </div>
                <Badge variant="outline">Priority {agent.priority}</Badge>
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}

// Performance metrics view component
function PerformanceMetricsView({ config }: { config: OrchestrationConfig }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Performance Thresholds
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Max Execution Time</span>
            <span className="font-medium">{Math.round(config.performanceThresholds.maxExecutionTime / 1000)} seconds</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Min Success Rate</span>
            <span className="font-medium">{Math.round(config.performanceThresholds.minSuccessRate * 100)}%</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Max Token Usage</span>
            <span className="font-medium">{config.performanceThresholds.maxTokenUsage.toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Expected Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Expected Response Time</span>
            <span className="font-medium">{calculateEstimatedResponseTime(config)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Expected Cost Efficiency</span>
            <span className="font-medium">{calculateCostEfficiency(config)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Complexity</span>
            <Badge variant="outline">
              {ORCHESTRATION_TYPES[config.orchestrationType].complexity}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}