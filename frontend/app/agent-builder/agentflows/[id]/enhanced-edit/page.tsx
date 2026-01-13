'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Save,
  Play,
  Settings,
  Eye,
  BarChart3,
  Users,
  Layers,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { VisualWorkflowEditor } from '@/components/agent-builder/VisualWorkflowEditor';
import { AgentflowIntegrationPanel } from '@/components/agent-builder/AgentflowIntegrationPanel';
import { RealTimeMonitoring } from '@/components/agent-builder/RealTimeMonitoring';
import { SupervisorDashboard } from '@/components/agent-builder/SupervisorDashboard';
import { SupervisorConfigWizard } from '@/components/agent-builder/SupervisorConfigWizard';

const ORCHESTRATION_TYPES = [
  { id: 'sequential', name: 'Sequential Execution', description: 'Agents execute in order' },
  { id: 'parallel', name: 'Parallel Execution', description: 'Agents execute simultaneously' },
  { id: 'hierarchical', name: 'Hierarchical Execution', description: 'Execute hierarchically based on dependencies' },
  { id: 'adaptive', name: 'Adaptive Execution', description: 'AI determines execution order based on situation' },
  { id: 'consensus_building', name: 'Consensus Building', description: 'Agents make decisions through consensus' },
  { id: 'dynamic_routing', name: 'Dynamic Routing', description: 'Execution path changes based on conditions' },
];

export default function EnhancedAgentflowEditPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Unwrap params
  const { id } = React.use(params);

  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('design');
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    orchestration_type: 'sequential',
    supervisor_enabled: false,
    supervisor_llm_provider: 'ollama',
    supervisor_llm_model: 'llama3.1',
    supervisor_max_iterations: 10,
    supervisor_decision_strategy: 'llm_based' as 'llm_based' | 'consensus' | 'weighted_voting' | 'expert_system',
    tags: [] as string[],
  });

  // Fetch agentflow data
  const { data: agentflow, isLoading } = useQuery({
    queryKey: ['agentflow', id],
    queryFn: () => agentBuilderAPI.getAgentflow(id),
    enabled: !!id,
  });

  // Load existing data
  useEffect(() => {
    if (agentflow) {
      setFormData({
        name: agentflow.name || '',
        description: agentflow.description || '',
        orchestration_type: agentflow.orchestration_type || 'sequential',
        supervisor_enabled: agentflow.supervisor_config?.enabled || false,
        supervisor_llm_provider: agentflow.supervisor_config?.llm_provider || 'ollama',
        supervisor_llm_model: agentflow.supervisor_config?.llm_model || 'llama3.1',
        supervisor_max_iterations: agentflow.supervisor_config?.max_iterations || 10,
        supervisor_decision_strategy: agentflow.supervisor_config?.decision_strategy || 'llm_based',
        tags: agentflow.tags || [],
      });
    }
  }, [agentflow]);

  // Save agentflow
  const saveMutation = useMutation({
    mutationFn: async (data: any) => {
      return agentBuilderAPI.updateAgentflow(id, {
        name: data.name,
        description: data.description,
        orchestration_type: data.orchestration_type,
        supervisor_config: {
          enabled: data.supervisor_enabled,
          llm_provider: data.supervisor_llm_provider,
          llm_model: data.supervisor_llm_model,
          max_iterations: data.supervisor_max_iterations,
          decision_strategy: data.supervisor_decision_strategy,
        },
        tags: data.tags,
      });
    },
    onSuccess: () => {
      toast({
        title: 'Save Complete',
        description: 'Agentflow has been successfully saved.',
      });
      queryClient.invalidateQueries({ queryKey: ['agentflow', id] });
    },
    onError: () => {
      toast({
        title: 'Save Failed',
        description: 'An error occurred while saving.',
        variant: 'destructive',
      });
    },
  });

  // Execute agentflow
  const executeMutation = useMutation({
    mutationFn: () => agentBuilderAPI.executeAgentflow(id, {
      input: 'Enhanced editor execution',
      context: { source: 'enhanced_editor' },
    }),
    onSuccess: (result) => {
      toast({
        title: 'Execution Started',
        description: `Execution ID: ${result.execution_id}`,
      });
      setActiveTab('monitoring');
    },
    onError: () => {
      toast({
        title: 'Execution Failed',
        description: 'An error occurred during execution.',
        variant: 'destructive',
      });
    },
  });

  const handleSave = () => {
    setSaving(true);
    saveMutation.mutate(formData);
    setSaving(false);
  };

  const handleExecute = () => {
    executeMutation.mutate();
  };

  const handleAddTag = (tag: string) => {
    if (tag && !formData.tags.includes(tag)) {
      setFormData(prev => ({
        ...prev,
        tags: [...prev.tags, tag],
      }));
    }
  };

  const handleRemoveTag = (tag: string) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(t => t !== tag),
    }));
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Loading Agentflow...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.back()}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Separator orientation="vertical" className="h-6" />
              <div>
                <h1 className="text-xl font-semibold">{formData.name || 'Edit Agentflow'}</h1>
                <p className="text-sm text-muted-foreground">
                  Design and manage workflows with advanced visual editor
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleSave}
                disabled={saving || saveMutation.isPending}
              >
                <Save className="w-4 h-4 mr-2" />
                {saving || saveMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
              <Button
                onClick={handleExecute}
                disabled={executeMutation.isPending}
                className="bg-green-600 hover:bg-green-700"
              >
                <Play className="w-4 h-4 mr-2" />
                {executeMutation.isPending ? 'Executing...' : 'Execute'}
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-6">
            <TabsTrigger value="design" className="flex items-center gap-2">
              <Layers className="w-4 h-4" />
              <span className="hidden sm:inline">Design</span>
            </TabsTrigger>
            <TabsTrigger value="visual" className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              <span className="hidden sm:inline">Visual Editor</span>
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              <span className="hidden sm:inline">Agents</span>
            </TabsTrigger>
            <TabsTrigger value="supervisor" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              <span className="hidden sm:inline">Supervisor</span>
            </TabsTrigger>
            <TabsTrigger value="integration" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              <span className="hidden sm:inline">Integration</span>
            </TabsTrigger>
            <TabsTrigger value="monitoring" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              <span className="hidden sm:inline">Monitoring</span>
            </TabsTrigger>
          </TabsList>

          {/* Design Tab */}
          <TabsContent value="design" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-6">
                {/* Basic Information */}
                <Card>
                  <CardHeader>
                    <CardTitle>Basic Information</CardTitle>
                    <CardDescription>
                      Configure basic settings for your Agentflow
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        placeholder="Enter Agentflow name"
                      />
                    </div>
                    
                    <div>
                      <Label>Description</Label>
                      <Textarea
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        placeholder="Describe the purpose and functionality of this Agentflow"
                        rows={3}
                      />
                    </div>
                    
                    <div>
                      <Label>Orchestration Type</Label>
                      <Select
                        value={formData.orchestration_type}
                        onValueChange={(value) => setFormData(prev => ({ ...prev, orchestration_type: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.values(ORCHESTRATION_TYPES).map((type) => (
                            <SelectItem key={type.id} value={type.id}>
                              <div>
                                <div className="font-medium">{type.name}</div>
                                <div className="text-xs text-muted-foreground">{type.description}</div>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </CardContent>
                </Card>

                {/* Tags */}
                <Card>
                  <CardHeader>
                    <CardTitle>Tags</CardTitle>
                    <CardDescription>
                      Add tags for search and categorization
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {formData.tags.map((tag) => (
                        <Badge
                          key={tag}
                          variant="secondary"
                          className="cursor-pointer"
                          onClick={() => handleRemoveTag(tag)}
                        >
                          {tag} ×
                        </Badge>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Input
                        placeholder="Enter tag and press Enter"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleAddTag(e.currentTarget.value);
                            e.currentTarget.value = '';
                          }
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Sidebar */}
              <div className="space-y-6">
                {/* Quick Stats */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Quick Statistics</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Agent Count</span>
                      <Badge variant="outline">
                        {agentflow?.agents?.length || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Connection Count</span>
                      <Badge variant="outline">
                        {agentflow?.edges?.length || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Execution Count</span>
                      <Badge variant="outline">
                        {agentflow?.execution_count || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Last Execution</span>
                      <span className="text-xs text-muted-foreground">
                        {agentflow?.last_execution_at
                          ? new Date(agentflow.last_execution_at).toLocaleDateString()
                          : 'None'}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => setActiveTab('visual')}
                    >
                      <Eye className="w-4 h-4 mr-2" />
                      Open Visual Editor
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => setActiveTab('integration')}
                    >
                      <Settings className="w-4 h-4 mr-2" />
                      Validate Integrity
                    </Button>
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={() => setActiveTab('monitoring')}
                    >
                      <BarChart3 className="w-4 h-4 mr-2" />
                      Execution Monitoring
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Visual Editor Tab */}
          <TabsContent value="visual" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Visual Workflow Editor</CardTitle>
                <CardDescription>
                  Place and connect agents with drag and drop
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <VisualWorkflowEditor
                  agentflowId={id}
                  {...(agentflow && { initialData: agentflow })}
                  onSave={(data) => {
                    toast({
                      title: 'Visual Workflow Saved',
                      description: 'Changes have been successfully saved.',
                    });
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Agents Tab */}
          <TabsContent value="agents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Agent Management</CardTitle>
                <CardDescription>
                  Manage agents included in the workflow
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center py-12 text-muted-foreground">
                  Agent management features are available in the visual editor.
                  <br />
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => setActiveTab('visual')}
                  >
                    Go to Visual Editor
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Supervisor Tab */}
          <TabsContent value="supervisor" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <SupervisorConfigWizard
                agentflowId={id}
                orchestrationType={formData.orchestration_type}
                onConfigChange={(config) => {
                  setFormData(prev => ({
                    ...prev,
                    supervisor_enabled: config.enabled,
                    supervisor_llm_provider: config.llm_provider,
                    supervisor_llm_model: config.llm_model,
                    supervisor_max_iterations: config.max_iterations,
                    supervisor_decision_strategy: config.decision_strategy,
                  }));
                }}
              />
              <SupervisorDashboard 
                agentflowId={id} 
                supervisorEnabled={formData.supervisor_enabled}
              />
            </div>
          </TabsContent>

          {/* Integration Tab */}
          <TabsContent value="integration" className="space-y-6">
            <AgentflowIntegrationPanel
              agentflowId={id}
              onExecute={handleExecute}
            />
          </TabsContent>

          {/* Monitoring Tab */}
          <TabsContent value="monitoring" className="space-y-6">
            <RealTimeMonitoring
              agentflowId={id}
              autoRefresh={true}
            />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}