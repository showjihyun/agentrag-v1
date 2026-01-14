'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
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
  Settings,
  Users,
  MessageSquare,
  Clock,
  Target,
  Zap,
  Shield,
  Brain,
  Sparkles,
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

interface PatternConfigWizardProps {
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

const WIZARD_STEPS = [
  {
    id: 'basic',
    title: 'Basic Information',
    description: 'Set basic information for orchestration',
    icon: Info,
  },
  {
    id: 'agents',
    title: 'Agent Configuration',
    description: 'Set agent roles and priorities',
    icon: Users,
  },
  {
    id: 'supervisor',
    title: 'Supervisor Settings',
    description: 'Configure LLM-based coordinator',
    icon: Brain,
  },
  {
    id: 'communication',
    title: 'Communication Rules',
    description: 'Set communication methods between agents',
    icon: MessageSquare,
  },
  {
    id: 'performance',
    title: 'Performance Settings',
    description: 'Set performance thresholds and limits',
    icon: Zap,
  },
  {
    id: 'review',
    title: 'Review & Complete',
    description: 'Review settings and complete',
    icon: CheckCircle2,
  },
];

export const PatternConfigWizard: React.FC<PatternConfigWizardProps> = ({
  orchestrationType,
  open,
  onOpenChange,
  onComplete,
  initialConfig,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [config, setConfig] = useState<OrchestrationConfig>(() => ({
    orchestrationType,
    name: '',
    description: '',
    supervisorConfig: { ...DEFAULT_SUPERVISOR_CONFIG },
    agentRoles: [],
    communicationRules: {
      allowDirectCommunication: true,
      enableBroadcast: false,
      requireConsensus: false,
      maxNegotiationRounds: 3,
    },
    performanceThresholds: {
      maxExecutionTime: 300000, // 5 minutes
      minSuccessRate: 0.8,
      maxTokenUsage: 10000,
    },
    tags: [],
    ...initialConfig,
  }));

  const pattern = ORCHESTRATION_TYPES[orchestrationType];
  const currentStepInfo = WIZARD_STEPS[currentStep];
  const progress = ((currentStep + 1) / WIZARD_STEPS.length) * 100;

  // Recommended agent roles by pattern
  const getRecommendedAgentRoles = (type: OrchestrationTypeValue) => {
    const roleMap: Record<OrchestrationTypeValue, Array<{ name: string; role: AgentRole; priority: number }>> = {
      sequential: [
        { name: 'Data Collector', role: 'worker', priority: 1 },
        { name: 'Analyst', role: 'worker', priority: 2 },
        { name: 'Report Writer', role: 'synthesizer', priority: 3 },
      ],
      parallel: [
        { name: 'Search Expert', role: 'specialist', priority: 1 },
        { name: 'Translator', role: 'specialist', priority: 1 },
        { name: 'Summary Expert', role: 'specialist', priority: 1 },
        { name: 'Result Integrator', role: 'synthesizer', priority: 2 },
      ],
      hierarchical: [
        { name: 'Project Manager', role: 'manager', priority: 1 },
        { name: 'Researcher A', role: 'worker', priority: 2 },
        { name: 'Researcher B', role: 'worker', priority: 2 },
        { name: 'Quality Reviewer', role: 'critic', priority: 3 },
      ],
      consensus_building: [
        { name: 'Expert A', role: 'specialist', priority: 1 },
        { name: 'Expert B', role: 'specialist', priority: 1 },
        { name: 'Expert C', role: 'specialist', priority: 1 },
        { name: 'Mediator', role: 'coordinator', priority: 2 },
      ],
      swarm_intelligence: [
        { name: 'Explorer 1', role: 'worker', priority: 1 },
        { name: 'Explorer 2', role: 'worker', priority: 1 },
        { name: 'Explorer 3', role: 'worker', priority: 1 },
        { name: 'Coordinator', role: 'coordinator', priority: 2 },
      ],
      // Other patterns can be added
      adaptive: [
        { name: 'Situation Analyst', role: 'specialist', priority: 1 },
        { name: 'Strategy Planner', role: 'manager', priority: 2 },
        { name: 'Executor', role: 'worker', priority: 3 },
      ],
      dynamic_routing: [
        { name: 'Router', role: 'coordinator', priority: 1 },
        { name: 'Processor A', role: 'worker', priority: 2 },
        { name: 'Processor B', role: 'worker', priority: 2 },
        { name: 'Aggregator', role: 'synthesizer', priority: 3 },
      ],
      event_driven: [
        { name: 'Event Detector', role: 'specialist', priority: 1 },
        { name: 'Processor', role: 'worker', priority: 2 },
        { name: 'Responder', role: 'worker', priority: 3 },
      ],
      reflection: [
        { name: 'Analyst', role: 'worker', priority: 1 },
        { name: 'Reviewer', role: 'critic', priority: 2 },
        { name: 'Improver', role: 'synthesizer', priority: 3 },
      ],
      neuromorphic: [
        { name: 'Neuron A', role: 'worker', priority: 1 },
        { name: 'Neuron B', role: 'worker', priority: 1 },
        { name: 'Synapse', role: 'coordinator', priority: 2 },
      ],
      quantum_enhanced: [
        { name: 'Quantum Analyst', role: 'specialist', priority: 1 },
        { name: 'Superposition Processor', role: 'worker', priority: 2 },
        { name: 'Measurer', role: 'synthesizer', priority: 3 },
      ],
      bio_inspired: [
        { name: 'Sensor', role: 'specialist', priority: 1 },
        { name: 'Processor', role: 'worker', priority: 2 },
        { name: 'Actuator', role: 'synthesizer', priority: 3 },
      ],
      self_evolving: [
        { name: 'Learner', role: 'worker', priority: 1 },
        { name: 'Adapter', role: 'coordinator', priority: 2 },
        { name: 'Evolver', role: 'synthesizer', priority: 3 },
      ],
      federated: [
        { name: 'Local Agent A', role: 'worker', priority: 1 },
        { name: 'Local Agent B', role: 'worker', priority: 1 },
        { name: 'Global Coordinator', role: 'coordinator', priority: 2 },
        { name: 'Synchronizer', role: 'synthesizer', priority: 3 },
      ],
      emotional_ai: [
        { name: 'Emotion Analyst', role: 'specialist', priority: 1 },
        { name: 'Empathy Agent', role: 'worker', priority: 2 },
        { name: 'Response Controller', role: 'coordinator', priority: 3 },
      ],
      predictive: [
        { name: 'Predictor', role: 'specialist', priority: 1 },
        { name: 'Validator', role: 'critic', priority: 2 },
        { name: 'Adjuster', role: 'coordinator', priority: 3 },
      ],
    };
    
    return roleMap[type] || [
      { name: 'General Agent', role: 'worker', priority: 1 },
      { name: 'Specialist', role: 'specialist', priority: 2 },
      { name: 'Coordinator', role: 'coordinator', priority: 3 },
    ];
  };

  // Apply recommended agent roles
  const applyRecommendedRoles = () => {
    const recommended = getRecommendedAgentRoles(orchestrationType);
    const newRoles = recommended.map((rec, index) => ({
      id: `agent_${index + 1}`,
      name: rec.name,
      role: rec.role,
      priority: rec.priority,
      maxRetries: 3,
      timeoutSeconds: 300,
      dependencies: [],
    }));
    
    setConfig(prev => ({ ...prev, agentRoles: newRoles }));
  };

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

  const handleComplete = () => {
    onComplete(config);
    onOpenChange(false);
  };

  const isStepValid = (stepIndex: number): boolean => {
    switch (stepIndex) {
      case 0: // Basic Information
        return config.name.trim() !== '';
      case 1: // Agent Configuration
        return config.agentRoles.length > 0;
      case 2: // Supervisor Settings
        return !config.supervisorConfig.enabled || 
               (config.supervisorConfig.llm_provider !== '' && config.supervisorConfig.llm_model !== '');
      case 3: // Communication Rules
        return true; // Always valid since there are default values
      case 4: // Performance Settings
        return config.performanceThresholds.maxExecutionTime > 0 &&
               config.performanceThresholds.minSuccessRate > 0 &&
               config.performanceThresholds.maxTokenUsage > 0;
      default:
        return true;
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basic Information
        return (
          <div className="space-y-6">
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
              <Button variant="outline" onClick={applyRecommendedRoles}>
                <Sparkles className="w-4 h-4 mr-2" />
                Apply Recommended Roles
              </Button>
            </div>
            
            <div className="space-y-4">
              {config.agentRoles.map((agent, index) => (
                <Card key={agent.id} className="p-4">
                  <div className="grid grid-cols-2 gap-4">
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
                              {role.name} - {role.description}
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
                              {priority} (Higher = More Priority)
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Timeout (seconds)</Label>
                      <Input
                        type="number"
                        value={agent.timeoutSeconds}
                        onChange={(e) => {
                          const newRoles = [...config.agentRoles];
                          newRoles[index].timeoutSeconds = parseInt(e.target.value) || 300;
                          setConfig(prev => ({ ...prev, agentRoles: newRoles }));
                        }}
                        min={30}
                        max={3600}
                      />
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
        
      case 2: // Supervisor Settings
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Supervisor Settings</h3>
              <p className="text-sm text-gray-600">
                Configure the LLM-based intelligent coordinator
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="enableSupervisor"
                checked={config.supervisorConfig.enabled}
                onChange={(e) => setConfig(prev => ({
                  ...prev,
                  supervisorConfig: { ...prev.supervisorConfig, enabled: e.target.checked }
                }))}
              />
              <Label htmlFor="enableSupervisor">Enable Supervisor</Label>
            </div>
            
            {config.supervisorConfig.enabled && (
              <div className="space-y-4 pl-6 border-l-2 border-blue-200">
                <div className="grid grid-cols-2 gap-4">
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
                        <SelectItem value="google">Google AI</SelectItem>
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
                        {config.supervisorConfig.llm_provider === 'ollama' && (
                          <>
                            <SelectItem value="llama3.1">Llama 3.1</SelectItem>
                            <SelectItem value="mistral">Mistral</SelectItem>
                            <SelectItem value="codellama">Code Llama</SelectItem>
                          </>
                        )}
                        {config.supervisorConfig.llm_provider === 'openai' && (
                          <>
                            <SelectItem value="gpt-4">GPT-4</SelectItem>
                            <SelectItem value="gpt-3.5-turbo">GPT-3.5 Turbo</SelectItem>
                          </>
                        )}
                        {config.supervisorConfig.llm_provider === 'claude' && (
                          <>
                            <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                            <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
                          </>
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <Label>Decision Strategy</Label>
                  <Select
                    value={config.supervisorConfig.decision_strategy}
                    onValueChange={(value: any) => setConfig(prev => ({
                      ...prev,
                      supervisorConfig: { ...prev.supervisorConfig, decision_strategy: value }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="llm_based">LLM-Based Decision</SelectItem>
                      <SelectItem value="consensus">Consensus-Based</SelectItem>
                      <SelectItem value="weighted_voting">Weighted Voting</SelectItem>
                      <SelectItem value="expert_system">Expert System</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Max Iterations</Label>
                  <Input
                    type="number"
                    value={config.supervisorConfig.max_iterations}
                    onChange={(e) => setConfig(prev => ({
                      ...prev,
                      supervisorConfig: { ...prev.supervisorConfig, max_iterations: parseInt(e.target.value) || 10 }
                    }))}
                    min={1}
                    max={50}
                  />
                </div>
              </div>
            )}
          </div>
        );
        
      case 3: // Communication Rules
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Agent Communication Rules</h3>
              <p className="text-sm text-gray-600">
                Configure how agents communicate with each other
              </p>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="allowDirectCommunication"
                  checked={config.communicationRules.allowDirectCommunication}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, allowDirectCommunication: e.target.checked }
                  }))}
                />
                <Label htmlFor="allowDirectCommunication">Allow Direct Communication</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="enableBroadcast"
                  checked={config.communicationRules.enableBroadcast}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, enableBroadcast: e.target.checked }
                  }))}
                />
                <Label htmlFor="enableBroadcast">Enable Broadcast Communication</Label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="requireConsensus"
                  checked={config.communicationRules.requireConsensus}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, requireConsensus: e.target.checked }
                  }))}
                />
                <Label htmlFor="requireConsensus">Require Consensus</Label>
              </div>
              
              <div>
                <Label>Max Negotiation Rounds</Label>
                <Input
                  type="number"
                  value={config.communicationRules.maxNegotiationRounds}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    communicationRules: { ...prev.communicationRules, maxNegotiationRounds: parseInt(e.target.value) || 3 }
                  }))}
                  min={1}
                  max={10}
                  className="mt-1"
                />
              </div>
            </div>
          </div>
        );
        
      case 4: // Performance Settings
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Performance Thresholds</h3>
              <p className="text-sm text-gray-600">
                Set performance limits and thresholds for orchestration
              </p>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label>Max Execution Time (milliseconds)</Label>
                <Input
                  type="number"
                  value={config.performanceThresholds.maxExecutionTime}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    performanceThresholds: { ...prev.performanceThresholds, maxExecutionTime: parseInt(e.target.value) || 300000 }
                  }))}
                  min={10000}
                  max={3600000}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Current: {Math.round(config.performanceThresholds.maxExecutionTime / 1000)} seconds
                </p>
              </div>
              
              <div>
                <Label>Min Success Rate</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={config.performanceThresholds.minSuccessRate}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    performanceThresholds: { ...prev.performanceThresholds, minSuccessRate: parseFloat(e.target.value) || 0.8 }
                  }))}
                  min={0.1}
                  max={1.0}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Current: {Math.round(config.performanceThresholds.minSuccessRate * 100)}%
                </p>
              </div>
              
              <div>
                <Label>Max Token Usage</Label>
                <Input
                  type="number"
                  value={config.performanceThresholds.maxTokenUsage}
                  onChange={(e) => setConfig(prev => ({
                    ...prev,
                    performanceThresholds: { ...prev.performanceThresholds, maxTokenUsage: parseInt(e.target.value) || 10000 }
                  }))}
                  min={1000}
                  max={100000}
                  className="mt-1"
                />
              </div>
            </div>
          </div>
        );
        
      case 5: // Review & Complete
        return (
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold">Review Settings</h3>
              <p className="text-sm text-gray-600">
                Review your settings and complete
              </p>
            </div>
            
            <ScrollArea className="h-[400px] space-y-4">
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
                <h4 className="font-semibold mb-2">Supervisor</h4>
                <div className="text-sm">
                  {config.supervisorConfig.enabled ? (
                    <div className="space-y-1">
                      <div><strong>Enabled:</strong> Yes</div>
                      <div><strong>LLM:</strong> {config.supervisorConfig.llm_provider} / {config.supervisorConfig.llm_model}</div>
                      <div><strong>Strategy:</strong> {config.supervisorConfig.decision_strategy}</div>
                    </div>
                  ) : (
                    <div>Disabled</div>
                  )}
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-2">Communication Rules</h4>
                <div className="space-y-1 text-sm">
                  <div><strong>Direct Communication:</strong> {config.communicationRules.allowDirectCommunication ? 'Allowed' : 'Not Allowed'}</div>
                  <div><strong>Broadcast:</strong> {config.communicationRules.enableBroadcast ? 'Enabled' : 'Disabled'}</div>
                  <div><strong>Require Consensus:</strong> {config.communicationRules.requireConsensus ? 'Yes' : 'No'}</div>
                  <div><strong>Max Negotiation Rounds:</strong> {config.communicationRules.maxNegotiationRounds}</div>
                </div>
              </Card>
              
              <Card className="p-4">
                <h4 className="font-semibold mb-2">Performance Settings</h4>
                <div className="space-y-1 text-sm">
                  <div><strong>Max Execution Time:</strong> {Math.round(config.performanceThresholds.maxExecutionTime / 1000)} seconds</div>
                  <div><strong>Min Success Rate:</strong> {Math.round(config.performanceThresholds.minSuccessRate * 100)}%</div>
                  <div><strong>Max Token Usage:</strong> {config.performanceThresholds.maxTokenUsage.toLocaleString()}</div>
                </div>
              </Card>
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
            {pattern.name} Configuration Wizard
          </DialogTitle>
          <DialogDescription>
            Configure orchestration step by step
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-6 h-[600px]">
          {/* Step Navigation */}
          <div className="w-64 border-r pr-4">
            <div className="mb-4">
              <div className="text-sm text-gray-600 mb-2">Progress</div>
              <Progress value={progress} className="h-2" />
              <div className="text-xs text-gray-500 mt-1">{currentStep + 1} / {WIZARD_STEPS.length}</div>
            </div>
            
            <div className="space-y-2">
              {WIZARD_STEPS.map((step, index) => {
                const StepIcon = step.icon;
                const isCompleted = index < currentStep;
                const isCurrent = index === currentStep;
                const isValid = isStepValid(index);
                
                return (
                  <div
                    key={step.id}
                    className={cn(
                      'flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors',
                      isCurrent && 'bg-blue-50 border border-blue-200',
                      isCompleted && 'bg-green-50',
                      !isValid && index <= currentStep && 'bg-red-50'
                    )}
                    onClick={() => setCurrentStep(index)}
                  >
                    <div className={cn(
                      'p-1 rounded',
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
            {currentStep === WIZARD_STEPS.length - 1 ? (
              <Button onClick={handleComplete} disabled={!isStepValid(currentStep)}>
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