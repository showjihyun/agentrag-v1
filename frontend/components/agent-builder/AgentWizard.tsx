'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useToast } from '@/components/Toast';
import { agentBuilderAPI, type AgentCreate } from '@/lib/api/agent-builder';
import {
  Check,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Info,
  Sparkles,
  Wrench,
  Code,
  TestTube,
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ToolSelector } from './ToolSelector';
import { PromptTemplateEditor } from './PromptTemplateEditor';
import { AgentToolsPanel } from './AgentToolsPanel';
import { ContextManager, type ContextItem } from './ContextManager';
import { MCPServerSelector, type SelectedMCPServer } from './MCPServerSelector';
import { AgentPreview } from './AgentPreview';
import { LLM_PROVIDERS, getModelsForProvider, getAvailableProviders, LLMProvider } from '@/lib/llm-models';
import { FileText, Server } from 'lucide-react';

// LLM Config interface matching settings page
interface LLMConfig {
  apiKeys: {
    openai: string;
    anthropic: string;
    gemini: string;
  };
  ollama: {
    enabled: boolean;
    baseUrl: string;
    defaultModel: string;
  };
  defaultProvider: 'openai' | 'anthropic' | 'gemini' | 'ollama';
  defaultModel: string;
}

// Provider ID mapping (settings page uses 'anthropic', llm-models uses 'claude')
const providerIdMap: Record<string, string> = {
  anthropic: 'claude',
  claude: 'anthropic',
};

const agentFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  agent_type: z.string().default('custom'), // Hidden field with default value
  llm_provider: z.string().min(1, 'LLM provider is required'),
  llm_model: z.string().min(1, 'LLM model is required'),
  prompt_template: z.string().optional(),
  tool_ids: z.array(z.string()),
});

type AgentFormValues = z.infer<typeof agentFormSchema>;

const STEPS = [
  {
    id: 1,
    title: 'Basic Info',
    description: 'Name and description',
    icon: Info,
  },
  {
    id: 2,
    title: 'LLM Config',
    description: 'Choose your model',
    icon: Sparkles,
  },
  {
    id: 3,
    title: 'Capabilities',
    description: 'Tools, Context & MCP',
    icon: Wrench,
  },
  {
    id: 4,
    title: 'Prompt',
    description: 'Define behavior',
    icon: Code,
  },
  {
    id: 5,
    title: 'Review',
    description: 'Test and save',
    icon: TestTube,
  },
];

interface AgentWizardProps {
  agentId?: string;
  initialData?: any;
  templateData?: any;
  mode?: 'create' | 'edit';
}

export function AgentWizard({ agentId, initialData, templateData, mode = 'create' }: AgentWizardProps = {}) {
  console.log('[AgentWizard] Component rendered', { agentId, initialData, templateData, mode });
  
  const router = useRouter();
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = React.useState(1);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [draftSaved, setDraftSaved] = React.useState(false);
  const [allTools, setAllTools] = React.useState<any[]>([]);
  const [selectedToolsWithConfig, setSelectedToolsWithConfig] = React.useState<any[]>([]);
  const [, forceUpdate] = React.useReducer(x => x + 1, 0);
  const [llmConfig, setLlmConfig] = React.useState<LLMConfig | null>(null);
  const [ollamaModels, setOllamaModels] = React.useState<string[]>([]);
  
  // Context & MCP state - initialize from initialData if available
  const [contexts, setContexts] = React.useState<ContextItem[]>(
    initialData?.context_items || []
  );
  const [selectedMCPServers, setSelectedMCPServers] = React.useState<SelectedMCPServer[]>(
    initialData?.mcp_servers || []
  );
  const [capabilitiesTab, setCapabilitiesTab] = React.useState<string>('tools');

  console.log('[AgentWizard] State:', { 
    contextsCount: contexts.length, 
    mcpServersCount: selectedMCPServers.length,
    currentStep,
    mode,
    initialData: initialData ? 'loaded' : 'none'
  });

  // Load LLM config from localStorage (set in settings/llm page)
  React.useEffect(() => {
    const saved = localStorage.getItem('llm_config');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setLlmConfig(parsed);
      } catch {
        console.warn('Failed to parse LLM config from localStorage');
      }
    }
  }, []);

  // Fetch Ollama models if enabled
  React.useEffect(() => {
    if (llmConfig?.ollama?.enabled) {
      const fetchOllamaModels = async () => {
        try {
          const response = await fetch(`${llmConfig.ollama.baseUrl}/api/tags`);
          if (response.ok) {
            const data = await response.json();
            const models = data.models?.map((m: any) => m.name) || [];
            setOllamaModels(models);
            // Save to localStorage for use by other components
            localStorage.setItem('ollama_models', JSON.stringify(models));
          }
        } catch (error) {
          console.error('Failed to fetch Ollama models:', error);
        }
      };
      fetchOllamaModels();
    }
  }, [llmConfig?.ollama?.enabled, llmConfig?.ollama?.baseUrl]);

  // Get default provider/model from template, initialData, or LLM config
  const getDefaultProvider = () => {
    if (templateData?.configuration?.llm_provider) return templateData.configuration.llm_provider;
    if (initialData?.llm_provider) return initialData.llm_provider;
    if (llmConfig?.defaultProvider) {
      // Map 'anthropic' to 'claude' for consistency with LLM_PROVIDERS
      return llmConfig.defaultProvider === 'anthropic' ? 'claude' : llmConfig.defaultProvider;
    }
    return 'ollama';
  };

  const getDefaultModel = () => {
    if (templateData?.configuration?.llm_model) return templateData.configuration.llm_model;
    if (initialData?.llm_model) return initialData.llm_model;
    if (llmConfig?.defaultModel) return llmConfig.defaultModel;
    return 'llama3.1';
  };

  const getDefaultPrompt = () => {
    if (templateData?.configuration?.system_prompt) return templateData.configuration.system_prompt;
    if (initialData?.prompt_template) return initialData.prompt_template;
    return '';
  };

  const getDefaultTools = () => {
    if (templateData?.tools) return templateData.tools;
    if (initialData?.tools) return initialData.tools.map((t: any) => t.id || t.tool_id);
    return [];
  };

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: templateData?.name || initialData?.name || '',
      description: templateData?.description || initialData?.description || '',
      agent_type: initialData?.agent_type || 'custom',
      llm_provider: getDefaultProvider(),
      llm_model: getDefaultModel(),
      prompt_template: getDefaultPrompt(),
      tool_ids: getDefaultTools(),
    },
  });

  // Update form defaults when llmConfig loads
  React.useEffect(() => {
    if (llmConfig && !initialData) {
      const provider = llmConfig.defaultProvider === 'anthropic' ? 'claude' : llmConfig.defaultProvider;
      form.setValue('llm_provider', provider);
      form.setValue('llm_model', llmConfig.defaultModel);
    }
  }, [llmConfig, initialData, form]);

  // Check if a provider has API key configured
  const isProviderConfigured = (providerId: string): boolean => {
    if (!llmConfig) return providerId === 'ollama';
    
    switch (providerId) {
      case 'ollama':
        return llmConfig.ollama?.enabled !== false;
      case 'openai':
        return !!llmConfig.apiKeys?.openai;
      case 'claude':
      case 'anthropic':
        return !!llmConfig.apiKeys?.anthropic;
      case 'gemini':
        return !!llmConfig.apiKeys?.gemini;
      default:
        return false;
    }
  };

  // Fetch tools for display in review
  React.useEffect(() => {
    const fetchTools = async () => {
      try {
        const tools = await agentBuilderAPI.getTools();
        setAllTools(tools);
      } catch (error) {
        console.error('Failed to fetch tools:', error);
      }
    };
    fetchTools();
  }, []);

  const progress = (currentStep / STEPS.length) * 100;

  // Watch form values for Review step
  const reviewName = form.watch('name');
  const reviewDescription = form.watch('description');
  const reviewLlmProvider = form.watch('llm_provider');
  const reviewLlmModel = form.watch('llm_model');
  const reviewToolIds = form.watch('tool_ids');
  const reviewPromptTemplate = form.watch('prompt_template');

  // Debug effect for review step (development only)
  React.useEffect(() => {
    if (process.env.NODE_ENV === 'development' && currentStep === 5) {
      // Review step debugging available in dev tools
    }
  }, [currentStep, reviewToolIds, reviewName]);

  // Draft functionality disabled for simplicity
  const saveDraft = async () => {
    // No-op: Draft auto-save disabled
  };

  const loadDraft = () => {
    // No-op: Draft loading disabled
  };

  const validateStep = async (step: number): Promise<boolean> => {
    switch (step) {
      case 1:
        return await form.trigger(['name', 'description']);
      case 2:
        return await form.trigger(['llm_provider', 'llm_model']);
      case 3:
        return true; // Tools are optional
      case 4:
        return true; // Prompt is optional
      default:
        return true;
    }
  };

  const nextStep = async () => {
    const isValid = await validateStep(currentStep);
    if (isValid && currentStep < STEPS.length) {
      saveDraft();
      setCurrentStep(currentStep + 1);
      // Force re-render to ensure form values are fresh
      setTimeout(() => {
        forceUpdate();
      }, 10);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const onSubmit = async (data: AgentFormValues) => {
    setIsSubmitting(true);
    try {
      // Get tool configurations from selectedToolsWithConfig state
      const toolConfigurations = selectedToolsWithConfig.map(t => ({
        tool_id: t.tool_id,
        configuration: t.configuration || {},
        order: t.order
      }));

      const agentData: AgentCreate = {
        name: data.name,
        agent_type: data.agent_type,
        llm_provider: data.llm_provider,
        llm_model: data.llm_model,
        ...(data.description && { description: data.description }),
        ...(data.prompt_template && { prompt_template: data.prompt_template }),
        // Send tool configurations if available, otherwise fall back to tool_ids
        ...(toolConfigurations.length > 0 && { tools: toolConfigurations }),
        ...(data.tool_ids && data.tool_ids.length > 0 && { tool_ids: data.tool_ids }),
        // Add context items and MCP servers
        context_items: contexts,
        mcp_servers: selectedMCPServers.map(server => ({
          id: server.id,
          name: server.name,
          command: server.command,
          args: server.args,
          env: server.env,
          enabled: server.enabled
        })),
      };

      if (mode === 'edit' && agentId) {
        await agentBuilderAPI.updateAgent(agentId, agentData);
        
        toast({
          title: 'Agent updated',
          description: 'Your agent has been updated successfully.',
        });

        router.push(`/agent-builder/agents/${agentId}`);
      } else {
        const createdAgent = await agentBuilderAPI.createAgent(agentData);
        
        // Clear draft
        localStorage.removeItem('agent_draft');
        
        toast({
          title: 'Agent created',
          description: 'Your agent has been created successfully.',
        });

        // If tools were selected, redirect to tools configuration page
        if (data.tool_ids && data.tool_ids.length > 0) {
          router.push(`/agent-builder/agents/${createdAgent.id}/tools`);
        } else {
          router.push('/agent-builder/agents');
        }
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: mode === 'edit' ? 'Failed to update agent.' : 'Failed to create agent.',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Agent Name *</FormLabel>
                  <FormControl>
                    <Input placeholder="My Custom Agent" {...field} />
                  </FormControl>
                  <FormDescription>
                    A unique, descriptive name for your agent
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="Describe what your agent does and when to use it..."
                      className="resize-none min-h-[120px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Help others understand the purpose of this agent
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        );

      case 2:
        const currentProvider = form.watch('llm_provider') || 'ollama';
        const availableModels = currentProvider === 'ollama' && ollamaModels.length > 0
          ? ollamaModels.map(m => ({ id: m, name: m, description: 'Local model' }))
          : getModelsForProvider(currentProvider);
        
        return (
          <div className="space-y-6">
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm text-muted-foreground">
                Choose the language model that will power your agent. Different models have different capabilities and costs.
              </p>
            </div>

            {/* LLM Settings Status */}
            {llmConfig ? (
              <div className="rounded-lg border border-green-200 bg-green-50 dark:border-green-900 dark:bg-green-950/20 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    <span className="text-sm font-medium text-green-800 dark:text-green-200">
                      LLM 설정이 구성되어 있습니다
                    </span>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push('/agent-builder/settings/llm')}
                  >
                    설정 변경
                  </Button>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {llmConfig.ollama?.enabled && (
                    <Badge variant="outline" className="text-xs">
                      🦙 Ollama 활성화
                    </Badge>
                  )}
                  {llmConfig.apiKeys?.openai && (
                    <Badge variant="outline" className="text-xs text-green-600">
                      🤖 OpenAI 연결됨
                    </Badge>
                  )}
                  {llmConfig.apiKeys?.anthropic && (
                    <Badge variant="outline" className="text-xs text-green-600">
                      🧠 Claude 연결됨
                    </Badge>
                  )}
                  {llmConfig.apiKeys?.gemini && (
                    <Badge variant="outline" className="text-xs text-green-600">
                      💎 Gemini 연결됨
                    </Badge>
                  )}
                </div>
              </div>
            ) : (
              <div className="rounded-lg border border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-950/20 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-yellow-600" />
                    <span className="text-sm text-yellow-800 dark:text-yellow-200">
                      LLM API 키가 설정되지 않았습니다. Ollama(로컬)만 사용 가능합니다.
                    </span>
                  </div>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => router.push('/agent-builder/settings/llm')}
                  >
                    설정하기
                  </Button>
                </div>
              </div>
            )}

            <FormField
              control={form.control}
              name="llm_provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>LLM Provider *</FormLabel>
                  <Select onValueChange={(value) => {
                    field.onChange(value);
                    // Reset model when provider changes
                    const models = value === 'ollama' && ollamaModels.length > 0
                      ? ollamaModels
                      : getModelsForProvider(value).map(m => m.id);
                    if (models.length > 0 && models[0]) {
                      form.setValue('llm_model', models[0]);
                    }
                  }} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select provider" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {getAvailableProviders().map((provider) => {
                        const configured = isProviderConfigured(provider.id);
                        const isDisabled = !configured && provider.type === 'cloud';
                        return (
                          <SelectItem 
                            key={provider.id} 
                            value={provider.id}
                            className={isDisabled ? 'opacity-50 cursor-not-allowed' : ''}
                          >
                            <div className="flex items-center gap-2">
                              <span>{provider.icon}</span>
                              <span className={isDisabled ? 'text-muted-foreground' : ''}>{provider.name}</span>
                              <Badge 
                                variant={configured ? "default" : "secondary"} 
                                className="text-xs"
                              >
                                {provider.type === 'local' ? 'Local' : configured ? '연결됨' : 'API 키 필요'}
                              </Badge>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="llm_model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Model *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select model" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {availableModels.map((model) => (
                        <SelectItem key={model.id} value={model.id}>
                          <div className="flex flex-col">
                            <span>{model.name}</span>
                            {model.description && (
                              <span className="text-xs text-muted-foreground">{model.description}</span>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Default Settings Info */}
            {llmConfig && (
              <div className="rounded-lg border p-4 space-y-2">
                <h4 className="font-medium text-sm flex items-center gap-2">
                  <Sparkles className="h-4 w-4" />
                  기본 설정 (Settings에서 구성됨)
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">기본 Provider</p>
                    <p className="font-medium">
                      {llmConfig.defaultProvider === 'anthropic' ? 'Claude' : 
                       llmConfig.defaultProvider.charAt(0).toUpperCase() + llmConfig.defaultProvider.slice(1)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">기본 Model</p>
                    <p className="font-medium">{llmConfig.defaultModel}</p>
                  </div>
                </div>
              </div>
            )}

            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="font-medium text-sm">Model Comparison</h4>
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div>
                  <p className="text-muted-foreground">Speed</p>
                  <div className="flex gap-1 mt-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                      <div key={i} className="h-2 w-2 rounded-full bg-primary" />
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground">Quality</p>
                  <div className="flex gap-1 mt-1">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-2 w-2 rounded-full bg-primary" />
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-muted-foreground">Cost</p>
                  <div className="flex gap-1 mt-1">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-2 w-2 rounded-full bg-primary" />
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        const currentToolIds = form.watch('tool_ids');
        
        return (
          <div className="space-y-6" onClick={(e) => e.stopPropagation()}>
            <Tabs value={capabilitiesTab} onValueChange={setCapabilitiesTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="tools" className="flex items-center gap-2">
                  <Wrench className="h-4 w-4" />
                  <span>Tools</span>
                  {currentToolIds && currentToolIds.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                      {currentToolIds.length}
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="context" className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>Context</span>
                  {contexts.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                      {contexts.length}
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="mcp" className="flex items-center gap-2">
                  <Server className="h-4 w-4" />
                  <span>MCP</span>
                  {selectedMCPServers.length > 0 && (
                    <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 flex items-center justify-center text-xs">
                      {selectedMCPServers.length}
                    </Badge>
                  )}
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="tools" className="mt-4">
                <FormField
                  control={form.control}
                  name="tool_ids"
                  render={({ field }) => (
                    <FormItem>
                      <FormControl>
                        <div onClick={(e) => e.stopPropagation()}>
                          <AgentToolsPanel
                            agentId={agentId || 'new'}
                            selectedTools={field.value || []}
                            onToolsChange={(newValue) => {
                              field.onChange(newValue);
                            }}
                            onToolsWithConfigChange={(toolsWithConfig) => {
                              setSelectedToolsWithConfig(toolsWithConfig);
                            }}
                            agentType={form.watch('agent_type')}
                            agentDescription={form.watch('description')}
                          />
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </TabsContent>
              
              <TabsContent value="context" className="mt-4">
                <ContextManager
                  contexts={contexts}
                  onContextsChange={setContexts}
                  maxContexts={10}
                />
              </TabsContent>
              
              <TabsContent value="mcp" className="mt-4">
                <MCPServerSelector
                  selectedServers={selectedMCPServers}
                  onServersChange={setSelectedMCPServers}
                />
              </TabsContent>
            </Tabs>
          </div>
        );

      case 4:
        const step4ToolIds = form.watch('tool_ids');
        console.log('Step 4 - tool_ids:', step4ToolIds);
        
        return (
          <div className="space-y-6">
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm text-muted-foreground">
                The prompt template defines how your agent behaves. Use variables like ${'{query}'} and ${'{context}'} for dynamic content.
              </p>
            </div>
            
            {/* Debug info */}
            <div className="text-xs text-muted-foreground p-2 bg-muted rounded">
              Debug Step 4: tool_ids = {JSON.stringify(step4ToolIds || [])}
            </div>

            <FormField
              control={form.control}
              name="prompt_template"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Prompt Template</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder="You are a helpful AI assistant. Answer the following question: ${query}"
                      className="font-mono text-sm min-h-[300px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Use ${'{variable_name}'} for variable substitution
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="rounded-lg border p-4 space-y-2">
              <h4 className="font-medium text-sm">Available Variables</h4>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{'${query}'}</Badge>
                <Badge variant="outline">{'${context}'}</Badge>
                <Badge variant="outline">{'${history}'}</Badge>
                <Badge variant="outline">{'${user_name}'}</Badge>
              </div>
            </div>
          </div>
        );

      case 5:
        // Get current form values directly
        const currentValues = form.getValues();
        console.log('Review - currentValues:', currentValues);
        
        return (
          <div className="space-y-6">
            <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="rounded-full bg-primary/20 p-2">
                    <Check className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-lg mb-1">Ready to Create</h3>
                    <p className="text-sm text-muted-foreground">
                      Review your agent configuration below. You can edit these settings anytime after creation.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-4">
              {/* Basic Information */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Info className="h-4 w-4" />
                    Basic Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-2">
                    <span className="text-sm font-medium text-muted-foreground">Name:</span>
                    <span className="col-span-2 text-sm font-semibold">{currentValues.name}</span>
                  </div>
                  {currentValues.description && (
                    <>
                      <Separator />
                      <div className="grid grid-cols-3 gap-2">
                        <span className="text-sm font-medium text-muted-foreground">Description:</span>
                        <span className="col-span-2 text-sm text-muted-foreground">{currentValues.description}</span>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* LLM Configuration */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    LLM Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-2">
                    <span className="text-sm font-medium text-muted-foreground">Provider:</span>
                    <span className="col-span-2 text-sm">
                      <Badge variant="secondary">{currentValues.llm_provider}</Badge>
                    </span>
                  </div>
                  <Separator />
                  <div className="grid grid-cols-3 gap-2">
                    <span className="text-sm font-medium text-muted-foreground">Model:</span>
                    <span className="col-span-2 text-sm font-semibold">{currentValues.llm_model}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Tools */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Wrench className="h-4 w-4" />
                    Tools & Capabilities
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {currentValues.tool_ids && Array.isArray(currentValues.tool_ids) && currentValues.tool_ids.length > 0 ? (
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Badge className="font-semibold">{currentValues.tool_ids.length}</Badge>
                        <span className="text-sm text-muted-foreground">
                          {currentValues.tool_ids.length === 1 ? 'tool selected' : 'tools selected'}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {currentValues.tool_ids.map((toolId) => {
                          const tool = allTools.find((t) => t.id === toolId);
                          return (
                            <Badge key={toolId} variant="secondary" className="text-xs px-3 py-1">
                              {tool?.name || toolId}
                            </Badge>
                          );
                        })}
                      </div>
                      <div className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
                        <p className="text-xs text-blue-900 dark:text-blue-100">
                          💡 After creating the agent, you'll be redirected to configure tool parameters.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No tools selected - Agent will use default capabilities
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* Prompt Template */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Code className="h-4 w-4" />
                    Prompt Template
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {currentValues.prompt_template ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Badge variant="outline">{currentValues.prompt_template.length} characters</Badge>
                      </div>
                      <div className="rounded-md bg-muted p-3 max-h-32 overflow-y-auto">
                        <pre className="text-xs font-mono whitespace-pre-wrap">{currentValues.prompt_template}</pre>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No custom prompt template - Agent will use default system prompt
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <FormProvider {...form}>
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Main Form - Left Side (3/5) */}
        <div className="lg:col-span-3">
          <form 
            onSubmit={(e) => {
              console.log('Form onSubmit event triggered');
              form.handleSubmit(onSubmit)(e);
            }} 
            className="space-y-6"
          >
            {/* Progress Bar */}
            <Card>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-semibold">
                        Step {currentStep} of {STEPS.length}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {STEPS[currentStep - 1]?.title}
                      </p>
                    </div>
                    {draftSaved && (
                      <Badge variant="secondary" className="animate-in fade-in">
                        <Check className="mr-1 h-3 w-3" />
                        Draft Saved
                      </Badge>
                    )}
                  </div>
                  <Progress value={progress} className="h-2" />
                  <div className="flex justify-between">
                    {STEPS.map((step) => {
                      const Icon = step.icon;
                      const isCompleted = step.id < currentStep;
                      const isCurrent = step.id === currentStep;
                      
                      return (
                        <div
                          key={step.id}
                          className={`flex flex-col items-center gap-2 ${
                            isCurrent ? 'text-primary' : isCompleted ? 'text-green-600' : 'text-muted-foreground'
                          }`}
                        >
                          <div
                            className={`flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                              isCurrent
                                ? 'border-primary bg-primary/10'
                                : isCompleted
                                ? 'border-green-600 bg-green-50'
                                : 'border-muted'
                            }`}
                      >
                        {isCompleted ? (
                          <Check className="h-5 w-5" />
                        ) : (
                          <Icon className="h-5 w-5" />
                        )}
                      </div>
                      <span className="text-xs font-medium hidden sm:block">{step.title}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Step Content */}
        <Card>
          <CardHeader>
            <CardTitle>{STEPS[currentStep - 1]?.title}</CardTitle>
            <CardDescription>{STEPS[currentStep - 1]?.description}</CardDescription>
          </CardHeader>
          <CardContent>{renderStepContent()}</CardContent>
        </Card>

            {/* Navigation */}
            <div className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 1}
              >
                <ChevronLeft className="mr-2 h-4 w-4" />
                Previous
              </Button>

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={saveDraft}
                >
                  Save Draft
                </Button>

                {currentStep < STEPS.length ? (
                  <Button type="button" onClick={nextStep}>
                    Next
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                ) : (
                  <Button 
                    type="submit" 
                    disabled={isSubmitting}
                    onClick={(e) => {
                      console.log(`${mode === 'edit' ? 'Update' : 'Create'} Agent button clicked`);
                      console.log('Form errors:', form.formState.errors);
                      console.log('Form values:', form.getValues());
                    }}
                  >
                    {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    {mode === 'edit' ? 'Update Agent' : 'Create Agent'}
                  </Button>
                )}
              </div>
            </div>
          </form>
        </div>

        {/* Preview Panel - Right Side (2/5 for wider chat) */}
        <div className="lg:col-span-2 hidden lg:block">
          <div className="sticky top-6">
            <AgentPreview
              agentName={form.watch('name') || 'Untitled Agent'}
              agentDescription={form.watch('description')}
              llmProvider={form.watch('llm_provider') || getDefaultProvider()}
              llmModel={form.watch('llm_model') || getDefaultModel()}
              contextItems={contexts}
              mcpServers={selectedMCPServers}
              promptTemplate={form.watch('prompt_template')}
            />
          </div>
        </div>
      </div>
    </FormProvider>
  );
}
