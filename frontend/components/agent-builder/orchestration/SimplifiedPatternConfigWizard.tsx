/**
 * Simplified Pattern Config Wizard (4-Step)
 * Simplified pattern configuration wizard (4 steps)
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Info,
  Users,
  Settings,
  Eye,
  Sparkles,
  Lightbulb,
  Zap,
  Clock,
  Target,
  Shield
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  ORCHESTRATION_TYPES,
  AGENT_ROLES,
  DEFAULT_SUPERVISOR_CONFIG,
  type OrchestrationTypeValue,
  type SupervisorConfig,
  type AgentRole,
} from '@/lib/constants/orchestration';
import { useRealTimeValidation } from '@/hooks/useRealTimeValidation';
import { RealTimeValidationFeedback } from '@/components/agent-builder/validation/RealTimeValidationFeedback';

interface SimplifiedPatternConfigWizardProps {
  orchestrationType: OrchestrationTypeValue;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onComplete: (config: OrchestrationConfig) => void;
  initialConfig?: Partial<OrchestrationConfig>;
}

interface OrchestrationConfig {
  orchestrationType: OrchestrationTypeValue;
  name: string;
  description: string;
  supervisorConfig: SupervisorConfig;
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

// Simplified 4-step wizard
const SIMPLIFIED_WIZARD_STEPS = [
  {
    id: 'basic',
    title: 'Basic Settings',
    description: 'Set name, description, and basic options',
    icon: Info,
  },
  {
    id: 'agents',
    title: 'Agent Configuration',
    description: 'Set AI Agent roles and configuration',
    icon: Users,
  },
  {
    id: 'advanced',
    title: 'Advanced Settings',
    description: 'Supervisor, communication rules, performance settings',
    icon: Settings,
  },
  {
    id: 'review',
    title: 'Review & Complete',
    description: 'Review settings and final confirmation',
    icon: Eye,
  },
];

// Smart defaults by pattern
const SMART_DEFAULTS = {
  sequential: {
    name: 'Sequential Processing Workflow',
    description: 'A workflow that processes tasks in order.',
    agentRoles: [
      { name: 'Data Collector', role: 'worker', priority: 1 },
      { name: 'Analyst', role: 'specialist', priority: 2 },
      { name: 'Report Writer', role: 'synthesizer', priority: 3 },
    ],
    supervisorEnabled: false,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: false,
      requireConsensus: false,
      maxNegotiationRounds: 1,
    },
    performanceThresholds: {
      maxExecutionTime: 300000, // 5 minutes
      minSuccessRate: 0.9,
      maxTokenUsage: 5000,
    },
    tags: ['sequential', 'workflow', 'automation'],
  },
  parallel: {
    name: 'Parallel Processing System',
    description: 'A system that processes multiple tasks simultaneously.',
    agentRoles: [
      { name: 'Search Expert', role: 'specialist', priority: 1 },
      { name: 'Translator', role: 'specialist', priority: 1 },
      { name: 'Summary Expert', role: 'specialist', priority: 1 },
      { name: 'Result Integrator', role: 'synthesizer', priority: 2 },
    ],
    supervisorEnabled: true,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: true,
      requireConsensus: false,
      maxNegotiationRounds: 2,
    },
    performanceThresholds: {
      maxExecutionTime: 180000, // 3 minutes
      minSuccessRate: 0.85,
      maxTokenUsage: 8000,
    },
    tags: ['parallel', 'concurrent', 'efficiency'],
  },
  consensus_building: {
    name: 'Consensus-Based Decision Making',
    description: 'Gathers opinions from multiple experts to reach consensus.',
    agentRoles: [
      { name: 'Expert A', role: 'specialist', priority: 1 },
      { name: 'Expert B', role: 'specialist', priority: 1 },
      { name: 'Expert C', role: 'specialist', priority: 1 },
      { name: 'Mediator', role: 'coordinator', priority: 2 },
    ],
    supervisorEnabled: true,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: true,
      requireConsensus: true,
      maxNegotiationRounds: 5,
    },
    performanceThresholds: {
      maxExecutionTime: 600000, // 10 minutes
      minSuccessRate: 0.8,
      maxTokenUsage: 15000,
    },
    tags: ['consensus', 'decision-making', 'expert'],
  },
  dynamic_routing: {
    name: 'Dynamic Routing System',
    description: 'Dynamically routes tasks based on performance.',
    agentRoles: [
      { name: 'Router', role: 'coordinator', priority: 1 },
      { name: 'Processor A', role: 'worker', priority: 2 },
      { name: 'Processor B', role: 'worker', priority: 2 },
      { name: 'Aggregator', role: 'synthesizer', priority: 3 },
    ],
    supervisorEnabled: true,
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: false,
      requireConsensus: false,
      maxNegotiationRounds: 2,
    },
    performanceThresholds: {
      maxExecutionTime: 240000, // 4 minutes
      minSuccessRate: 0.9,
      maxTokenUsage: 7000,
    },
    tags: ['dynamic-routing', 'performance-optimization', 'adaptive'],
  },
  // Other pattern defaults can be added
} as const;

export const SimplifiedPatternConfigWizard: React.FC<SimplifiedPatternConfigWizardProps> = ({
  orchestrationType,
  open,
  onOpenChange,
  onComplete,
  initialConfig,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<OrchestrationConfig>(() => {
    const smartDefaults = SMART_DEFAULTS[orchestrationType] || SMART_DEFAULTS.sequential;
    
    return {
      orchestrationType,
      name: smartDefaults.name,
      description: smartDefaults.description,
      supervisorConfig: {
        ...DEFAULT_SUPERVISOR_CONFIG,
        enabled: smartDefaults.supervisorEnabled,
      },
      agentRoles: smartDefaults.agentRoles.map((role, index) => ({
        id: `agent_${index + 1}`,
        name: role.name,
        role: role.role as AgentRole,
        priority: role.priority,
        maxRetries: 3,
        timeoutSeconds: 300,
        dependencies: [],
      })),
      communicationRules: smartDefaults.communicationRules,
      performanceThresholds: smartDefaults.performanceThresholds,
      tags: smartDefaults.tags,
      ...initialConfig,
    };
  });

  const pattern = ORCHESTRATION_TYPES[orchestrationType];
  const currentStepInfo = SIMPLIFIED_WIZARD_STEPS[currentStep];
  const progress = ((currentStep + 1) / SIMPLIFIED_WIZARD_STEPS.length) * 100;

  // Real-time validation
  const {
    validationResult,
    isValidating,
    hasChanges,
    validate,
    saveConfig,
    resetValidation
  } = useRealTimeValidation({
    debounceMs: 300,
    enableAutoSave: false, // Disable auto-save in wizard
    onValidationChange: (result) => {
      console.log('Validation result:', result);
    }
  });

  // Real-time validation on config change
  useEffect(() => {
    if (open) {
      validate(orchestrationType, config);
    } else {
      resetValidation();
    }
  }, [config, orchestrationType, open, validate, resetValidation]);

  // Apply smart defaults
  const applySmartDefaults = () => {
    const smartDefaults = SMART_DEFAULTS[orchestrationType] || SMART_DEFAULTS.sequential;
    
    setConfig(prev => ({
      ...prev,
      name: smartDefaults.name,
      description: smartDefaults.description,
      agentRoles: smartDefaults.agentRoles.map((role, index) => ({
        id: `agent_${index + 1}`,
        name: role.name,
        role: role.role as AgentRole,
        priority: role.priority,
        maxRetries: 3,
        timeoutSeconds: 300,
        dependencies: [],
      })),
      supervisorConfig: {
        ...prev.supervisorConfig,
        enabled: smartDefaults.supervisorEnabled,
      },
      communicationRules: smartDefaults.communicationRules,
      performanceThresholds: smartDefaults.performanceThresholds,
      tags: smartDefaults.tags,
    }));
  };

  const handleNext = () => {
    if (currentStep < SIMPLIFIED_WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    onComplete(config);
    onOpenChange(false);
  };

  const isStepValid = (stepIndex: number): boolean => {
    switch (stepIndex) {
      case 0: // Basic Settings
        return config.name.trim() !== '';
      case 1: // Agent Configuration
        return config.agentRoles.length > 0;
      case 2: // Advanced Settings
        return !config.supervisorConfig.enabled || 
               (config.supervisorConfig.llm_provider !== '' && config.supervisorConfig.llm_model !== '');
      case 3: // Review
        return validationResult?.valid !== false;
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Settings
        return (
          <div className="space-y-6">
            {/* Smart defaults apply button */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Lightbulb className="h-5 w-5 text-blue-600" />
                    <div>
                      <h4 className="font-medium text-blue-900">Use Smart Defaults</h4>
                      <p className="text-sm text-blue-700">
                        Automatically apply optimized settings for the {pattern.name} pattern
                      </p>
                    </div>
                  </div>
                  <Button variant="outline" onClick={applySmartDefaults} className="border-blue-300">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Apply
                  </Button>
                </div>
              </CardContent>
            </Card>

            <div className="grid grid-cols-1 gap-6">
              <div>
                <Label htmlFor="name">Orchestration Name *</Label>
                <Input
                  id="name"
                  value={config.name}
                  onChange={(e) => setConfig(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Customer Inquiry Processing System"
                  className="mt-1"
                />
              </div>
              
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={config.description}
                  onChange={(e) => setConfig(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe the purpose and functionality of this orchestration"
                  className="mt-1"
                  rows={3}
                />
              </div>
              
              <div>
                <Label>Tags</Label>
                <div className="mt-1 flex flex-wrap gap-2">
                  {config.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary" className="cursor-pointer"
                      onClick={() => setConfig(prev => ({
                        ...prev,
                        tags: prev.tags.filter((_, i) => i !== index)
                      }))}>
                      {tag} ×
                    </Badge>
                  ))}
                  <Input
                    placeholder="Add tag (Press Enter)"
                    className="w-32"
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                        const newTag = e.currentTarget.value.trim();
                        if (!config.tags.includes(newTag)) {
                          setConfig(prev => ({ ...prev, tags: [...prev.tags, newTag] }));
                        }
                        e.currentTarget.value = '';
                      }
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Pattern info display */}
            <Card className="bg-gray-50">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Selected Pattern: {pattern.name}</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <p className="text-sm text-gray-600 mb-3">{pattern.description}</p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="text-xs">
                    <Clock className="w-3 h-3 mr-1" />
                    {pattern.estimated_setup_time}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    <Target className="w-3 h-3 mr-1" />
                    {pattern.complexity}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        );
        
      case 1: // Agent Configuration
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold">Agent Role Configuration</h3>
                <p className="text-sm text-gray-600">
                  Configure the agents needed for the {pattern.name} pattern
                </p>
              </div>
            </div>
            
            <div className="space-y-4">
              {config.agentRoles.map((agent, index) => (
                <Card key={agent.id} className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <Label>Agent Name</Label>
                      <Input
                        value={agent.name}
                        onChange={(e) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].name = e.target.value;
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                        placeholder="Agent Name"
                      />
                    </div>
                    <div>
                      <Label>Role</Label>
                      <Select
                        value={agent.role}
                        onValueChange={(value: AgentRole) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].role = value;
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(AGENT_ROLES).map(([key, role]) => (
                            <SelectItem key={key} value={key}>
                              {role.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Priority</Label>
                      <Select
                        value={agent.priority.toString()}
                        onValueChange={(value) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].priority = parseInt(value);
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[1, 2, 3, 4, 5].map(priority => (
                            <SelectItem key={priority} value={priority.toString()}>
                              {priority}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="mt-4 flex justify-end">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const newRoles = config.agentRoles.filter((_, i) => i !== index);
                        setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                      }}
                    >
                      Remove
                    </Button>
                  </div>
                </Card>
              ))}
              
              <Button
                variant="outline"
                className="w-full"
                onClick={() => {
                  const newAgent = {
                    id: `agent_${config.agentRoles.length + 1}`,
                    name: `Agent ${config.agentRoles.length + 1}`,
                    role: 'worker' as AgentRole,
                    priority: 1,
                    maxRetries: 3,
                    timeoutSeconds: 300,
                    dependencies: [],
                  };
                  setConfig(prev => ({ ...prev, agentRoles: [...prev.agentRoles, newAgent] }));
                }}
              >
                + Add Agent
              </Button>
            </div>
          </div>
        );
        
      case 2: // Advanced Settings (Combined)
        return (
          <div className="space-y-6">
            {/* Supervisor Settings */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="w-5 h-5" />
                  Supervisor Settings
                </CardTitle>
                <CardDescription>
                  Configure the LLM-based intelligent coordinator
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="enableSupervisor"
                    checked={config.supervisorConfig.enabled}
                    onCheckedChange={(checked) => setConfig(prev => ({
                      ...prev,
                      supervisorConfig: { ...prev.supervisorConfig, enabled: checked }
                    }))}
                  />
                  <Label htmlFor="enableSupervisor">Enable Supervisor</Label>
                </div>
                
                {config.supervisorConfig.enabled && (
                  <div className="grid grid-cols-2 gap-4 pl-6 border-l-2 border-blue-200">
                    <div>
                      <Label>LLM Provider</Label>
                      <Select
                        value={config.supervisorConfig.llm_provider}
                        onValueChange={(value) => setConfig(prev => ({
                          ...prev,
                          supervisorConfig: { ...prev.supervisorConfig, llm_provider: value }
                        }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ollama">Ollama (Local)</SelectItem>
                          <SelectItem value="openai">OpenAI</SelectItem>
                          <SelectItem value="claude">Claude</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Model</Label>
                      <Select
                        value={config.supervisorConfig.llm_model}
                        onValueChange={(value) => setConfig(prev => ({
                          ...prev,
                          supervisorConfig: { ...prev.supervisorConfig, llm_model: value }
                        }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="llama3.1">Llama 3.1</SelectItem>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Communication and Performance Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="w-4 h-4" />
                    Communication Rules
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="directComm" className="text-sm">Direct Communication</Label>
                    <Switch
                      id="directComm"
                      checked={config.communicationRules.allowDirectCommunication}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        communicationRules: { ...prev.communicationRules, allowDirectCommunication: checked }
                      }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label htmlFor="broadcast" className="text-sm">Broadcast</Label>
                    <Switch
                      id="broadcast"
                      checked={config.communicationRules.enableBroadcast}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        communicationRules: { ...prev.communicationRules, enableBroadcast: checked }
                      }))}
                    />
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <Label htmlFor="consensus" className="text-sm">Require Consensus</Label>
                    <Switch
                      id="consensus"
                      checked={config.communicationRules.requireConsensus}
                      onCheckedChange={(checked) => setConfig(prev => ({
                        ...prev,
                        communicationRules: { ...prev.communicationRules, requireConsensus: checked }
                      }))}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Zap className="w-4 h-4" />
                    Performance Settings
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <Label className="text-sm">Max Execution Time</Label>
                    <Select
                      value={config.performanceThresholds.maxExecutionTime.toString()}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        performanceThresholds: { ...prev.performanceThresholds, maxExecutionTime: parseInt(value) }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="180000">3 minutes</SelectItem>
                        <SelectItem value="300000">5 minutes</SelectItem>
                        <SelectItem value="600000">10 minutes</SelectItem>
                        <SelectItem value="1800000">30 minutes</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label className="text-sm">Min Success Rate</Label>
                    <Select
                      value={config.performanceThresholds.minSuccessRate.toString()}
                      onValueChange={(value) => setConfig(prev => ({
                        ...prev,
                        performanceThresholds: { ...prev.performanceThresholds, minSuccessRate: parseFloat(value) }
                      }))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.7">70%</SelectItem>
                        <SelectItem value="0.8">80%</SelectItem>
                        <SelectItem value="0.9">90%</SelectItem>
                        <SelectItem value="0.95">95%</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        );
        
      case 3: // Review & Complete
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Review Settings</h3>
              <p className="text-sm text-gray-600">
                Review your settings and complete
              </p>
            </div>

            {/* Real-time validation result */}
            <RealTimeValidationFeedback
              validationResult={validationResult}
              isValidating={isValidating}
              hasChanges={hasChanges}
              showDetails={true}
              compact={false}
            />
            
            <ScrollArea className="h-[300px] space-y-4">
              <div className="space-y-4">
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Basic Information</h4>
                  <div className="space-y-1 text-sm">
                    <div><strong>Name:</strong> {config.name}</div>
                    <div><strong>Pattern:</strong> {pattern.name}</div>
                    <div><strong>Description:</strong> {config.description || 'None'}</div>
                    <div><strong>Tags:</strong> {config.tags.join(', ') || 'None'}</div>
                  </div>
                </Card>
                
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Agent Configuration ({config.agentRoles.length})</h4>
                  <div className="space-y-2">
                    {config.agentRoles.map((agent, index) => (
                      <div key={index} className="text-sm flex items-center justify-between">
                        <span>{agent.name} ({AGENT_ROLES[agent.role].name})</span>
                        <Badge variant="outline">Priority {agent.priority}</Badge>
                      </div>
                    ))}
                  </div>
                </Card>
                
                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Advanced Settings</h4>
                  <div className="space-y-2 text-sm">
                    <div><strong>Supervisor:</strong> {config.supervisorConfig.enabled ? 'Enabled' : 'Disabled'}</div>
                    <div><strong>Direct Communication:</strong> {config.communicationRules.allowDirectCommunication ? 'Allowed' : 'Not Allowed'}</div>
                    <div><strong>Max Execution Time:</strong> {Math.round(config.performanceThresholds.maxExecutionTime / 1000)} seconds</div>
                    <div><strong>Min Success Rate:</strong> {Math.round(config.performanceThresholds.minSuccessRate * 100)}%</div>
                  </div>
                </Card>
              </div>
            </ScrollArea>
          </div>
        );
        
      default:
        return null;
    }
  };

  if (!pattern) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings className="w-5 h-5" />
            {pattern.name} Configuration Wizard (Simplified)
          </DialogTitle>
          <DialogDescription>
            Quickly configure orchestration with a simplified 4-step process
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-6 h-[600px]">
          {/* Step Navigation */}
          <div className="w-64 border-r pr-4">
            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">Progress</div>
              <Progress value={progress} className="h-2" />
              <div className="text-xs text-gray-500 mt-1">{currentStep + 1} / {SIMPLIFIED_WIZARD_STEPS.length}</div>
            </div>
            
            <div className="space-y-2">
              {SIMPLIFIED_WIZARD_STEPS.map((step, index) => {
                const StepIcon = step.icon;
                const isCompleted = index < currentStep;
                const isCurrent = index === currentStep;
                const isValid = isStepValid(index);
                
                return (
                  <div
                    key={step.id}
                    className={cn(
                      'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                      isCurrent && 'bg-blue-50 border border-blue-200',
                      isCompleted && 'bg-green-50',
                      !isValid && index <= currentStep && 'bg-red-50'
                    )}
                    onClick={() => setCurrentStep(index)}
                  >
                    <div className={cn(
                      'p-2 rounded',
                      isCurrent && 'bg-blue-500 text-white',
                      isCompleted && 'bg-green-500 text-white',
                      !isValid && index <= currentStep && 'bg-red-500 text-white',
                      !isCurrent && !isCompleted && isValid && 'bg-gray-200'
                    )}>
                      {isCompleted ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : !isValid && index <= currentStep ? (
                        <AlertCircle className="w-4 h-4" />
                      ) : (
                        <StepIcon className="w-4 h-4" />
                      )}
                    </div>
                    <div>
                      <div className="text-sm font-medium">{step.title}</div>
                      <div className="text-xs text-gray-500">{step.description}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Step Content */}
          <div className="flex-1 overflow-y-auto">
            <div className="mb-6">
              <h2 className="text-xl font-semibold">{currentStepInfo.title}</h2>
              <p className="text-gray-600">{currentStepInfo.description}</p>
            </div>
            
            {renderStepContent()}
          </div>
        </div>

        {/* Bottom Buttons */}
        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 0}
          >
            <ChevronLeft className="w-4 h-4 mr-2" />
            Previous
          </Button>
          
          <div className="flex gap-2">
            {currentStep === SIMPLIFIED_WIZARD_STEPS.length - 1 ? (
              <Button 
                onClick={handleComplete} 
                disabled={!isStepValid(currentStep) || validationResult?.valid === false}
              >
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Complete
              </Button>
            ) : (
              <Button onClick={handleNext} disabled={!isStepValid(currentStep)}>
                Next
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};