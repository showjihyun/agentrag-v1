'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  ArrowLeft,
  Save,
  Play,
  Users,
  Settings,
  Sparkles,
  ArrowRight,
  Zap,
  GitBranch,
  MessageSquare,
  Route,
  Hexagon,
  Bell,
  RefreshCw,
  Brain,
  Atom,
  Leaf,
  TrendingUp,
  Network,
  Heart,
  Crystal,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { flowsAPI } from '@/lib/api/flows';
import { 
  ORCHESTRATION_TYPES, 
  CORE_ORCHESTRATION_TYPES,
  TRENDS_2025_ORCHESTRATION_TYPES,
  TRENDS_2026_ORCHESTRATION_TYPES,
  CATEGORY_COLORS,
  COMPLEXITY_COLORS,
  MATURITY_COLORS,
  type OrchestrationTypeValue 
} from '@/lib/constants/orchestration';

// Icon mapping for orchestration types
const getIconComponent = (iconName: string) => {
  const iconMap: Record<string, any> = {
    ArrowRight,
    Zap,
    Users,
    GitBranch,
    MessageSquare,
    Route,
    Hexagon,
    Bell,
    RefreshCw,
    Brain,
    Atom,
    Leaf,
    TrendingUp,
    Network,
    Heart,
    Crystal,
  };
  return iconMap[iconName] || ArrowRight; // fallback to ArrowRight
};

// Orchestration types are now imported from constants

const TEMPLATES = [
  {
    id: 'multi-agent-research',
    name: 'Research Agent Team',
    description: 'Multiple agents collaborate to collect and analyze information',
    orchestration: 'hierarchical',
    agents: 4,
    icon: '🔬',
    tags: ['research', 'analysis', 'multi-agent'],
  },
  {
    id: 'customer-support-team',
    name: 'Customer Support Team',
    description: 'Agent team responsible for classification, response, and escalation',
    orchestration: 'adaptive',
    agents: 3,
    icon: '🎧',
    tags: ['customer-service', 'support', 'routing'],
  },
  {
    id: 'content-pipeline',
    name: 'Content Generation Pipeline',
    description: 'Sequential processing of planning, writing, review, and publishing',
    orchestration: 'sequential',
    agents: 4,
    icon: '✍️',
    tags: ['content', 'writing', 'pipeline'],
  },
  {
    id: 'data-analysis-team',
    name: 'Data Analysis Team',
    description: 'Analyze multiple data sources in parallel and integrate results',
    orchestration: 'parallel',
    agents: 5,
    icon: '📊',
    tags: ['data', 'analysis', 'parallel'],
  },
];

export default function NewAgentflowPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();
  
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    orchestration_type: 'sequential' as OrchestrationTypeValue,
    supervisor_config: {
      enabled: true,
      llm_provider: 'ollama',
      llm_model: 'llama3.1:8b',
      max_iterations: 10,
      decision_strategy: 'llm_based' as const,
    },
    graph_definition: {
      nodes: [],
      edges: []
    },
    tags: [] as string[],
  });
  
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  // Load template if specified in URL
  useEffect(() => {
    const templateId = searchParams.get('template');
    if (templateId) {
      const template = TEMPLATES.find(t => t.id === templateId);
      if (template) {
        setSelectedTemplate(templateId);
        setFormData(prev => ({
          ...prev,
          name: template.name,
          description: template.description,
          orchestration_type: template.orchestration as OrchestrationTypeValue,
          tags: template.tags,
        }));
      }
    }
  }, [searchParams]);

  const handleSave = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter an Agentflow name',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSaving(true);
      const agentflow = await flowsAPI.createAgentflow(formData);
      
      toast({
        title: 'Created',
        description: `"${formData.name}" Agentflow has been created`,
      });
      
      router.push(`/agent-builder/agentflows/${agentflow.id}`);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create Agentflow',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleTemplateSelect = (template: typeof TEMPLATES[0]) => {
    setSelectedTemplate(template.id);
    setFormData(prev => ({
      ...prev,
      name: template.name,
      description: template.description,
      orchestration_type: template.orchestration as OrchestrationTypeValue,
      tags: template.tags,
    }));
  };

  const selectedOrchestration = ORCHESTRATION_TYPES[formData.orchestration_type];
  const SelectedIcon = selectedOrchestration ? getIconComponent(selectedOrchestration.icon) : null;

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900">
              <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            Create New Agentflow
          </h1>
          <p className="text-muted-foreground mt-1">
            Build multi-agent systems to automate complex tasks
          </p>
        </div>
      </div>

      <Tabs defaultValue="basic" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="basic">Basic Info</TabsTrigger>
          <TabsTrigger value="orchestration">Orchestration</TabsTrigger>
          <TabsTrigger value="templates">Templates</TabsTrigger>
        </TabsList>

        {/* Basic Information */}
        <TabsContent value="basic" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>
                Enter the name and description of your Agentflow
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name *</Label>
                <Input
                  id="name"
                  placeholder="e.g., Customer Support Automation System"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Describe what this Agentflow will do..."
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="flex flex-wrap gap-2">
                  {formData.tags.map((tag, index) => (
                    <Badge key={index} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                  {formData.tags.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      Tags will be automatically added when you select a template or set orchestration type
                    </p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Orchestration */}
        <TabsContent value="orchestration" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Orchestration Settings</CardTitle>
              <CardDescription>
                Decide how agents will collaborate
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-8">
              {/* Core Patterns */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <h3 className="text-lg font-semibold">Core Patterns</h3>
                  <Badge variant="outline" className="text-xs">Stable</Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.values(CORE_ORCHESTRATION_TYPES).map((type) => {
                    const Icon = getIconComponent(type.icon);
                    const isSelected = formData.orchestration_type === type.id;
                    
                    return (
                      <Card
                        key={type.id}
                        className={`cursor-pointer transition-all border-2 ${
                          isSelected 
                            ? 'border-primary shadow-lg' 
                            : 'border-border hover:border-primary/50'
                        }`}
                        onClick={() => setFormData(prev => ({ 
                          ...prev, 
                          orchestration_type: type.id as OrchestrationTypeValue
                        }))}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg bg-blue-50 dark:bg-blue-950`}>
                              <Icon className={`h-5 w-5 text-blue-500`} />
                            </div>
                            <div className="flex-1">
                              <CardTitle className="text-base">{type.name}</CardTitle>
                              <CardDescription className="text-sm">
                                {type.description}
                              </CardDescription>
                            </div>
                            {isSelected && (
                              <Badge className="bg-primary">Selected</Badge>
                            )}
                          </div>
                        </CardHeader>
                      </Card>
                    );
                  })}
                </div>
              </div>

              {/* 2025 Trends */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <h3 className="text-lg font-semibold">2025 Trend Patterns</h3>
                  <Badge variant="outline" className="text-xs bg-purple-50 text-purple-700">Advanced</Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.values(TRENDS_2025_ORCHESTRATION_TYPES).map((type) => {
                    const Icon = getIconComponent(type.icon);
                    const isSelected = formData.orchestration_type === type.id;
                    
                    return (
                      <Card
                        key={type.id}
                        className={`cursor-pointer transition-all border-2 ${
                          isSelected 
                            ? 'border-primary shadow-lg' 
                            : 'border-border hover:border-primary/50'
                        }`}
                        onClick={() => setFormData(prev => ({ 
                          ...prev, 
                          orchestration_type: type.id as OrchestrationTypeValue
                        }))}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg bg-purple-50 dark:bg-purple-950`}>
                              <Icon className={`h-5 w-5 text-purple-500`} />
                            </div>
                            <div className="flex-1">
                              <CardTitle className="text-base">{type.name}</CardTitle>
                              <CardDescription className="text-sm">
                                {type.description}
                              </CardDescription>
                              <div className="flex gap-1 mt-2">
                                <Badge variant="secondary" className="text-xs">
                                  {type.complexity}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {type.maturity}
                                </Badge>
                              </div>
                            </div>
                            {isSelected && (
                              <Badge className="bg-primary">Selected</Badge>
                            )}
                          </div>
                        </CardHeader>
                      </Card>
                    );
                  })}
                </div>
              </div>

              {/* 2026 Trends */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                  <h3 className="text-lg font-semibold">2026 Next-Gen Patterns</h3>
                  <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700">Experimental</Badge>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.values(TRENDS_2026_ORCHESTRATION_TYPES).map((type) => {
                    const Icon = getIconComponent(type.icon);
                    const isSelected = formData.orchestration_type === type.id;
                    
                    return (
                      <Card
                        key={type.id}
                        className={`cursor-pointer transition-all border-2 ${
                          isSelected 
                            ? 'border-primary shadow-lg' 
                            : 'border-border hover:border-primary/50'
                        }`}
                        onClick={() => setFormData(prev => ({ 
                          ...prev, 
                          orchestration_type: type.id as OrchestrationTypeValue
                        }))}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg bg-emerald-50 dark:bg-emerald-950`}>
                              <Icon className={`h-5 w-5 text-emerald-500`} />
                            </div>
                            <div className="flex-1">
                              <CardTitle className="text-base">{type.name}</CardTitle>
                              <CardDescription className="text-sm">
                                {type.description}
                              </CardDescription>
                              <div className="flex gap-1 mt-2">
                                <Badge variant="secondary" className="text-xs">
                                  {type.complexity}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {type.maturity}
                                </Badge>
                              </div>
                            </div>
                            {isSelected && (
                              <Badge className="bg-primary">Selected</Badge>
                            )}
                          </div>
                        </CardHeader>
                      </Card>
                    );
                  })}
                </div>
              </div>

              {selectedOrchestration && SelectedIcon && (
                <div className="mt-6 p-4 rounded-lg bg-muted">
                  <div className="flex items-center gap-2 mb-2">
                    <SelectedIcon className={`h-4 w-4 ${
                      selectedOrchestration.category === 'core' ? 'text-blue-500' :
                      selectedOrchestration.category === '2025_trends' ? 'text-purple-500' :
                      'text-emerald-500'
                    }`} />
                    <span className="font-medium">{selectedOrchestration.name} Selected</span>
                    <Badge variant="outline" className="text-xs">
                      {selectedOrchestration.category === 'core' ? 'Core' : 
                       selectedOrchestration.category === '2025_trends' ? '2025 Trends' : '2026 Next-Gen'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">
                    {selectedOrchestration.description}
                  </p>
                  
                  {selectedOrchestration.useCases && (
                    <div className="mb-3">
                      <p className="text-sm font-medium mb-1">Key Use Cases:</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedOrchestration.useCases.map((useCase, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {useCase}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedOrchestration.benefits && (
                    <div className="mb-3">
                      <p className="text-sm font-medium mb-1">Key Benefits:</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedOrchestration.benefits.map((benefit, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {benefit}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedOrchestration.requirements && (
                    <div>
                      <p className="text-sm font-medium mb-1">Requirements:</p>
                      <div className="flex flex-wrap gap-1">
                        {selectedOrchestration.requirements.map((req, index) => (
                          <Badge key={index} variant="destructive" className="text-xs">
                            {req}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Supervisor Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Supervisor Settings
              </CardTitle>
              <CardDescription>
                Configure the supervisor AI to manage agents
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>LLM Provider</Label>
                  <Select
                    value={formData.supervisor_config.llm_provider}
                    onValueChange={(value) => setFormData(prev => ({
                      ...prev,
                      supervisor_config: {
                        ...prev.supervisor_config,
                        llm_provider: value,
                      }
                    }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ollama">Ollama (Local)</SelectItem>
                      <SelectItem value="openai">OpenAI</SelectItem>
                      <SelectItem value="anthropic">Anthropic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Model</Label>
                  <Input
                    value={formData.supervisor_config.llm_model}
                    onChange={(e) => setFormData(prev => ({
                      ...prev,
                      supervisor_config: {
                        ...prev.supervisor_config,
                        llm_model: e.target.value,
                      }
                    }))}
                    placeholder="llama3.1:8b"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Max Iterations</Label>
                <Input
                  type="number"
                  min="1"
                  max="50"
                  value={formData.supervisor_config.max_iterations}
                  onChange={(e) => setFormData(prev => ({
                    ...prev,
                    supervisor_config: {
                      ...prev.supervisor_config,
                      max_iterations: parseInt(e.target.value) || 10,
                    }
                  }))}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Templates */}
        <TabsContent value="templates" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                Select Template
              </CardTitle>
              <CardDescription>
                Get started quickly with pre-configured templates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {TEMPLATES.map((template) => {
                  const isSelected = selectedTemplate === template.id;
                  
                  return (
                    <Card
                      key={template.id}
                      className={`cursor-pointer transition-all border-2 ${
                        isSelected 
                          ? 'border-primary shadow-lg' 
                          : 'border-border hover:border-primary/50'
                      }`}
                      onClick={() => handleTemplateSelect(template)}
                    >
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="text-3xl mb-2">{template.icon}</div>
                          <Badge variant="outline">
                            {template.agents} Agents
                          </Badge>
                        </div>
                        <CardTitle className="text-base">{template.name}</CardTitle>
                        <CardDescription className="text-sm">
                          {template.description}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex flex-wrap gap-1">
                          {template.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button variant="outline" onClick={() => router.back()}>
          Cancel
        </Button>
        <div className="flex gap-3">
          <Button variant="outline" disabled={saving}>
            <Play className="h-4 w-4 mr-2" />
            Preview
          </Button>
          <Button onClick={handleSave} disabled={saving || !formData.name.trim()}>
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Creating...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Create
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}