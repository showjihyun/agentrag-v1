'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Separator } from '@/components/ui/separator';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Settings,
  Brain,
  Target,
  Users,
  Zap,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  TrendingUp,
  Shield,
  Clock,
  BarChart3,
  Lightbulb,
  Wand2,
} from 'lucide-react';

interface SupervisorConfig {
  enabled: boolean;
  llm_provider: string;
  llm_model: string;
  max_iterations: number;
  decision_strategy: 'llm_based' | 'consensus' | 'weighted_voting' | 'expert_system';
  
  // Advanced settings
  auto_agent_selection: boolean;
  performance_based_routing: boolean;
  dynamic_role_assignment: boolean;
  learning_enabled: boolean;
  optimization_strategy: 'performance' | 'cost' | 'speed' | 'quality';
  adaptation_threshold: number;
  
  // Monitoring settings
  monitoring_enabled: boolean;
  alert_thresholds: {
    success_rate: number;
    response_time: number;
    error_rate: number;
  };
  
  // Collaboration settings
  team_learning_enabled: boolean;
  knowledge_sharing: boolean;
  template_integration: boolean;
}

interface SupervisorConfigWizardProps {
  agentflowId: string;
  orchestrationType: string;
  currentConfig?: Partial<SupervisorConfig>;
  onConfigChange: (config: SupervisorConfig) => void;
  trigger?: React.ReactNode;
}

const WIZARD_STEPS = [
  { id: 'objective', title: 'Set Objective', description: 'Set the main objective for the supervisor' },
  { id: 'strategy', title: 'Select Strategy', description: 'Choose decision strategy and optimization direction' },
  { id: 'monitoring', title: 'Monitoring Setup', description: 'Configure performance monitoring and alerts' },
  { id: 'collaboration', title: 'Collaboration Features', description: 'Set up team learning and knowledge sharing' },
  { id: 'review', title: 'Review Settings', description: 'Review and apply final settings' },
];

const DECISION_STRATEGIES = [
  {
    id: 'llm_based',
    name: 'LLM-based Decision',
    description: 'AI analyzes the situation and makes optimal decisions',
    icon: Brain,
    complexity: 'Medium',
    recommended: true,
  },
  {
    id: 'consensus',
    name: 'Consensus-based',
    description: 'Aggregates opinions from all agents to make decisions',
    icon: Users,
    complexity: 'High',
    recommended: false,
  },
  {
    id: 'weighted_voting',
    name: 'Weighted Voting',
    description: 'Makes decisions through voting with agent-specific weights',
    icon: BarChart3,
    complexity: 'Medium',
    recommended: false,
  },
  {
    id: 'expert_system',
    name: 'Expert System',
    description: 'Makes decisions based on predefined rules',
    icon: Shield,
    complexity: 'Low',
    recommended: false,
  },
];

const OPTIMIZATION_STRATEGIES = [
  { id: 'performance', name: 'Performance Optimization', description: 'Prioritize processing speed and accuracy', icon: Zap },
  { id: 'cost', name: 'Cost Optimization', description: 'Minimize resource usage and costs', icon: TrendingUp },
  { id: 'speed', name: 'Speed Optimization', description: 'Minimize response time', icon: Clock },
  { id: 'quality', name: 'Quality Optimization', description: 'Prioritize result quality and reliability', icon: Target },
];

export function SupervisorConfigWizard({
  agentflowId,
  orchestrationType,
  currentConfig,
  onConfigChange,
  trigger,
}: SupervisorConfigWizardProps) {
  const { toast } = useToast();
  const [open, setOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<SupervisorConfig>({
    enabled: true,
    llm_provider: 'ollama',
    llm_model: 'llama3.1',
    max_iterations: 10,
    decision_strategy: 'llm_based',
    auto_agent_selection: true,
    performance_based_routing: true,
    dynamic_role_assignment: false,
    learning_enabled: true,
    optimization_strategy: 'performance',
    adaptation_threshold: 0.8,
    monitoring_enabled: true,
    alert_thresholds: {
      success_rate: 85,
      response_time: 5,
      error_rate: 10,
    },
    team_learning_enabled: false,
    knowledge_sharing: false,
    template_integration: true,
    ...currentConfig,
  });

  // AI recommendation settings query
  const { data: recommendations } = useQuery({
    queryKey: ['supervisor-recommendations', agentflowId, orchestrationType],
    queryFn: () => agentBuilderAPI.getSupervisorRecommendations(agentflowId, orchestrationType),
    enabled: open,
  });

  const handleNext = () => {
    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleApplyRecommendation = (recommendedConfig: Partial<SupervisorConfig>) => {
    setConfig({ ...config, ...recommendedConfig });
    toast({
      title: 'AI Recommendation Applied',
      description: 'Recommended settings have been applied',
    });
  };

  const handleFinish = () => {
    onConfigChange(config);
    setOpen(false);
    toast({
      title: 'Supervisor Configuration Complete',
      description: 'Advanced supervisor settings have been applied',
    });
  };

  const renderStepContent = () => {
    switch (WIZARD_STEPS[currentStep].id) {
      case 'objective':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Target className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Set the main objective for the supervisor</h3>
              <p className="text-muted-foreground">
                We recommend optimized settings for {orchestrationType} orchestration
              </p>
            </div>

            {/* AI Recommendation Card */}
            {recommendations?.recommended_config && (
              <Card className="border-purple-200 bg-purple-50 dark:bg-purple-950/20">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
                    <Sparkles className="h-5 w-5" />
                    AI Recommended Settings
                  </CardTitle>
                  <CardDescription>
                    Settings optimized for the current orchestration type
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Decision Strategy:</span>
                      <span className="ml-2">{recommendations.recommended_config.decision_strategy}</span>
                    </div>
                    <div>
                      <span className="font-medium">Optimization Strategy:</span>
                      <span className="ml-2">{recommendations.recommended_config.optimization_strategy}</span>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => handleApplyRecommendation(recommendations.recommended_config)}
                    className="w-full gap-2"
                  >
                    <Wand2 className="h-4 w-4" />
                    Apply Recommended Settings
                  </Button>
                </CardContent>
              </Card>
            )}

            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Optimization Strategy</Label>
                <div className="grid grid-cols-2 gap-3">
                  {OPTIMIZATION_STRATEGIES.map((strategy) => {
                    const Icon = strategy.icon;
                    const isSelected = config.optimization_strategy === strategy.id;
                    return (
                      <Card
                        key={strategy.id}
                        className={`cursor-pointer transition-all ${
                          isSelected ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/20' : ''
                        }`}
                        onClick={() => setConfig({ ...config, optimization_strategy: strategy.id as any })}
                      >
                        <CardContent className="pt-4 pb-3">
                          <div className="flex items-center gap-2 mb-2">
                            <Icon className="h-4 w-4" />
                            <span className="font-medium text-sm">{strategy.name}</span>
                          </div>
                          <p className="text-xs text-muted-foreground">{strategy.description}</p>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <Label>Adaptation Threshold</Label>
                <div className="space-y-2">
                  <Input
                    type="range"
                    min="0.1"
                    max="1.0"
                    step="0.1"
                    value={config.adaptation_threshold}
                    onChange={(e) => setConfig({ ...config, adaptation_threshold: parseFloat(e.target.value) })}
                  />
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Sensitive (0.1)</span>
                    <span>Current: {config.adaptation_threshold}</span>
                    <span>Stable (1.0)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'strategy':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Brain className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Select a decision strategy</h3>
              <p className="text-muted-foreground">
                Configure how agents collaborate and make decisions
              </p>
            </div>

            <div className="space-y-3">
              {DECISION_STRATEGIES.map((strategy) => {
                const Icon = strategy.icon;
                const isSelected = config.decision_strategy === strategy.id;
                return (
                  <Card
                    key={strategy.id}
                    className={`cursor-pointer transition-all ${
                      isSelected ? 'border-purple-500 bg-purple-50 dark:bg-purple-950/20' : ''
                    }`}
                    onClick={() => setConfig({ ...config, decision_strategy: strategy.id as any })}
                  >
                    <CardContent className="pt-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Icon className="h-5 w-5" />
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{strategy.name}</span>
                              {strategy.recommended && (
                                <Badge variant="outline" className="text-xs bg-green-50 text-green-700">
                                  Recommended
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{strategy.description}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <Badge variant="outline">{strategy.complexity}</Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            <div className="space-y-4">
              <Separator />
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Auto Agent Selection</Label>
                    <p className="text-sm text-muted-foreground">Automatically select optimal agents for tasks</p>
                  </div>
                  <Switch
                    checked={config.auto_agent_selection}
                    onCheckedChange={(checked) => setConfig({ ...config, auto_agent_selection: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Performance-based Routing</Label>
                    <p className="text-sm text-muted-foreground">Distribute tasks based on real-time performance</p>
                  </div>
                  <Switch
                    checked={config.performance_based_routing}
                    onCheckedChange={(checked) => setConfig({ ...config, performance_based_routing: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Dynamic Role Reassignment</Label>
                    <p className="text-sm text-muted-foreground">Adjust agent roles in real-time based on situation</p>
                  </div>
                  <Switch
                    checked={config.dynamic_role_assignment}
                    onCheckedChange={(checked) => setConfig({ ...config, dynamic_role_assignment: checked })}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Learning Feature</Label>
                    <p className="text-sm text-muted-foreground">Continuously improve by learning from performance data</p>
                  </div>
                  <Switch
                    checked={config.learning_enabled}
                    onCheckedChange={(checked) => setConfig({ ...config, learning_enabled: checked })}
                  />
                </div>
              </div>
            </div>
          </div>
        );

      case 'monitoring':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <BarChart3 className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Configure monitoring and alerts</h3>
              <p className="text-muted-foreground">
                Set up real-time performance tracking and issue alerts
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Real-time Monitoring</Label>
                  <p className="text-sm text-muted-foreground">Track agent performance and system status in real-time</p>
                </div>
                <Switch
                  checked={config.monitoring_enabled}
                  onCheckedChange={(checked) => setConfig({ ...config, monitoring_enabled: checked })}
                />
              </div>

              {config.monitoring_enabled && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Alert Threshold Settings</CardTitle>
                    <CardDescription>
                      You will receive alerts when these conditions are met
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Minimum Success Rate (%)</Label>
                      <Input
                        type="number"
                        min="0"
                        max="100"
                        value={config.alert_thresholds.success_rate}
                        onChange={(e) => setConfig({
                          ...config,
                          alert_thresholds: {
                            ...config.alert_thresholds,
                            success_rate: parseInt(e.target.value) || 85
                          }
                        })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Maximum Response Time (seconds)</Label>
                      <Input
                        type="number"
                        min="1"
                        max="60"
                        value={config.alert_thresholds.response_time}
                        onChange={(e) => setConfig({
                          ...config,
                          alert_thresholds: {
                            ...config.alert_thresholds,
                            response_time: parseInt(e.target.value) || 5
                          }
                        })}
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Maximum Error Rate (%)</Label>
                      <Input
                        type="number"
                        min="0"
                        max="50"
                        value={config.alert_thresholds.error_rate}
                        onChange={(e) => setConfig({
                          ...config,
                          alert_thresholds: {
                            ...config.alert_thresholds,
                            error_rate: parseInt(e.target.value) || 10
                          }
                        })}
                      />
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        );

      case 'collaboration':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <Users className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Configure collaboration features</h3>
              <p className="text-muted-foreground">
                Improve overall system performance through team learning and knowledge sharing
              </p>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Team Learning</Label>
                  <p className="text-sm text-muted-foreground">Improve performance by learning success patterns from other teams</p>
                </div>
                <Switch
                  checked={config.team_learning_enabled}
                  onCheckedChange={(checked) => setConfig({ ...config, team_learning_enabled: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Knowledge Sharing</Label>
                  <p className="text-sm text-muted-foreground">Share performance insights and optimization strategies between teams</p>
                </div>
                <Switch
                  checked={config.knowledge_sharing}
                  onCheckedChange={(checked) => setConfig({ ...config, knowledge_sharing: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Template Integration</Label>
                  <p className="text-sm text-muted-foreground">Auto-optimize based on verified team templates</p>
                </div>
                <Switch
                  checked={config.template_integration}
                  onCheckedChange={(checked) => setConfig({ ...config, template_integration: checked })}
                />
              </div>

              {(config.team_learning_enabled || config.knowledge_sharing) && (
                <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200">
                  <CardContent className="pt-4">
                    <div className="flex items-start gap-3">
                      <Lightbulb className="h-5 w-5 text-blue-600 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-800 dark:text-blue-200 mb-1">
                          Collaboration Features Enabled
                        </h4>
                        <p className="text-sm text-blue-700 dark:text-blue-300">
                          With these settings, you can share performance data with other teams and leverage collective intelligence.
                          Personal information is protected, and only performance patterns are shared anonymously.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        );

      case 'review':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <CheckCircle2 className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Review Settings</h3>
              <p className="text-muted-foreground">
                Review final settings and activate the supervisor
              </p>
            </div>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Basic Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>LLM Provider:</span>
                    <span className="font-medium">{config.llm_provider}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Model:</span>
                    <span className="font-medium">{config.llm_model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max Iterations:</span>
                    <span className="font-medium">{config.max_iterations}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Decision Strategy:</span>
                    <span className="font-medium">
                      {DECISION_STRATEGIES.find(s => s.id === config.decision_strategy)?.name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Optimization Strategy:</span>
                    <span className="font-medium">
                      {OPTIMIZATION_STRATEGIES.find(s => s.id === config.optimization_strategy)?.name}
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Advanced Features</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Auto Agent Selection:</span>
                    <Badge variant={config.auto_agent_selection ? 'default' : 'secondary'}>
                      {config.auto_agent_selection ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Performance-based Routing:</span>
                    <Badge variant={config.performance_based_routing ? 'default' : 'secondary'}>
                      {config.performance_based_routing ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Learning Feature:</span>
                    <Badge variant={config.learning_enabled ? 'default' : 'secondary'}>
                      {config.learning_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Real-time Monitoring:</span>
                    <Badge variant={config.monitoring_enabled ? 'default' : 'secondary'}>
                      {config.monitoring_enabled ? 'Enabled' : 'Disabled'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              {(config.team_learning_enabled || config.knowledge_sharing) && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Collaboration Features</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Team Learning:</span>
                      <Badge variant={config.team_learning_enabled ? 'default' : 'secondary'}>
                        {config.team_learning_enabled ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Knowledge Sharing:</span>
                      <Badge variant={config.knowledge_sharing ? 'default' : 'secondary'}>
                        {config.knowledge_sharing ? 'Enabled' : 'Disabled'}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || (
          <Button className="gap-2">
            <Settings className="h-4 w-4" />
            Advanced Settings
          </Button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Supervisor Configuration Wizard
          </DialogTitle>
          <DialogDescription>
            Configure advanced supervisor through step-by-step guide
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Progress</span>
              <span>{currentStep + 1} / {WIZARD_STEPS.length}</span>
            </div>
            <Progress value={(currentStep + 1) / WIZARD_STEPS.length * 100} />
            <div className="flex justify-between text-xs text-muted-foreground">
              {WIZARD_STEPS.map((step, index) => (
                <span
                  key={step.id}
                  className={index <= currentStep ? 'text-purple-600' : ''}
                >
                  {step.title}
                </span>
              ))}
            </div>
          </div>

          {/* Current Step Content */}
          <div className="min-h-[400px]">
            <div className="mb-4">
              <h3 className="text-lg font-semibold">{WIZARD_STEPS[currentStep].title}</h3>
              <p className="text-muted-foreground">{WIZARD_STEPS[currentStep].description}</p>
            </div>
            {renderStepContent()}
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Previous
            </Button>

            {currentStep === WIZARD_STEPS.length - 1 ? (
              <Button onClick={handleFinish} className="gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Complete Setup
              </Button>
            ) : (
              <Button onClick={handleNext} className="gap-2">
                Next
                <ArrowRight className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}