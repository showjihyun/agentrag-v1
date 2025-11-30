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
import { ToolSelector } from './ToolSelector';
import { PromptTemplateEditor } from './PromptTemplateEditor';
import { AgentToolsPanel } from './AgentToolsPanel';
import { LLM_PROVIDERS, getModelsForProvider } from '@/lib/llm-models';

const agentFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  agent_type: z.string().default('custom'),
  llm_provider: z.string().min(1, 'LLM provider is required').default('ollama'),
  llm_model: z.string().min(1, 'LLM model is required').default('llama3.1'),
  prompt_template: z.string().optional(),
  tool_ids: z.array(z.string()).optional().default([]),
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
    title: 'Tools',
    description: 'Select capabilities',
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
  mode?: 'create' | 'edit';
}

export function AgentWizard({ agentId, initialData, mode = 'create' }: AgentWizardProps = {}) {
  const router = useRouter();
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = React.useState(1);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [draftSaved, setDraftSaved] = React.useState(false);
  const [allTools, setAllTools] = React.useState<any[]>([]);
  const [selectedToolsWithConfig, setSelectedToolsWithConfig] = React.useState<any[]>([]);
  const [, forceUpdate] = React.useReducer(x => x + 1, 0);

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: initialData?.name || '',
      description: initialData?.description || '',
      agent_type: initialData?.agent_type || 'custom',
      llm_provider: initialData?.llm_provider || 'ollama',
      llm_model: initialData?.llm_model || 'llama3.1',
      prompt_template: initialData?.prompt_template || '',
      tool_ids: initialData?.tools?.map((t: any) => t.id || t.tool_id) || [],
    },
  });

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
  const reviewAgentType = form.watch('agent_type');
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
        return await form.trigger(['name', 'description', 'agent_type']);
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
        description: data.description,
        agent_type: data.agent_type,
        llm_provider: data.llm_provider,
        llm_model: data.llm_model,
        prompt_template: data.prompt_template,
        // Send tool configurations if available, otherwise fall back to tool_ids
        tools: toolConfigurations.length > 0 ? toolConfigurations : undefined,
        tool_ids: data.tool_ids && data.tool_ids.length > 0 ? data.tool_ids : undefined,
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

            <FormField
              control={form.control}
              name="agent_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Agent Type</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="custom">Custom Agent</SelectItem>
                      <SelectItem value="template">From Template</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    Start from scratch or use a template
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="rounded-lg bg-muted p-4">
              <p className="text-sm text-muted-foreground">
                Choose the language model that will power your agent. Different models have different capabilities and costs.
              </p>
            </div>

            <FormField
              control={form.control}
              name="llm_provider"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>LLM Provider *</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select provider" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {LLM_PROVIDERS.map((provider) => (
                        <SelectItem key={provider.id} value={provider.id}>
                          <div className="flex items-center gap-2">
                            <span>{provider.icon}</span>
                            <span>{provider.name}</span>
                            <Badge variant="secondary" className="text-xs">
                              {provider.type === 'local' ? 'Local' : 'Cloud'}
                            </Badge>
                          </div>
                        </SelectItem>
                      ))}
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
                      {getModelsForProvider(form.watch('llm_provider') || 'ollama').map((model) => (
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
                      />
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
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
                  <Separator />
                  <div className="grid grid-cols-3 gap-2">
                    <span className="text-sm font-medium text-muted-foreground">Type:</span>
                    <span className="col-span-2 text-sm">
                      <Badge variant="outline">{currentValues.agent_type}</Badge>
                    </span>
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
                    {STEPS[currentStep - 1].title}
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
            <CardTitle>{STEPS[currentStep - 1].title}</CardTitle>
            <CardDescription>{STEPS[currentStep - 1].description}</CardDescription>
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
    </FormProvider>
  );
}
