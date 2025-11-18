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

  React.useEffect(() => {
    if (currentStep === 5) {
      console.log('Review step - ALL VALUES:');
      console.log('  name:', reviewName);
      console.log('  tool_ids:', reviewToolIds);
      console.log('  form.getValues():', form.getValues());
      console.log('  form.getValues().tool_ids:', form.getValues().tool_ids);
    }
  }, [currentStep, reviewToolIds, reviewName]);

  const saveDraft = async () => {
    const values = form.getValues();
    console.log('saveDraft - values:', values);
    console.log('saveDraft - tool_ids:', values.tool_ids);
    localStorage.setItem('agent_draft', JSON.stringify(values));
    setDraftSaved(true);
    toast({
      title: 'Draft saved',
      description: 'Your progress has been saved locally.',
    });
    setTimeout(() => setDraftSaved(false), 2000);
  };

  const loadDraft = () => {
    const draft = localStorage.getItem('agent_draft');
    if (draft) {
      const values = JSON.parse(draft);
      Object.keys(values).forEach((key) => {
        form.setValue(key as any, values[key]);
      });
      toast({
        title: 'Draft loaded',
        description: 'Your previous progress has been restored.',
      });
    }
  };

  React.useEffect(() => {
    // Check for draft on mount
    const draft = localStorage.getItem('agent_draft');
    if (draft) {
      const shouldLoad = confirm('Found a saved draft. Would you like to continue from where you left off?');
      if (shouldLoad) {
        loadDraft();
      }
    }
  }, []);

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
        console.log('After step change - tool_ids:', form.getValues().tool_ids);
      }, 10);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const onSubmit = async (data: AgentFormValues) => {
    console.log('onSubmit called with data:', data);
    setIsSubmitting(true);
    try {
      const agentData: AgentCreate = {
        name: data.name,
        description: data.description,
        agent_type: data.agent_type,
        llm_provider: data.llm_provider,
        llm_model: data.llm_model,
        prompt_template: data.prompt_template,
        // Only include tool_ids if there are any selected
        tool_ids: data.tool_ids && data.tool_ids.length > 0 ? data.tool_ids : undefined,
      };

      if (mode === 'edit' && agentId) {
        console.log('Updating agent with data:', agentData);
        await agentBuilderAPI.updateAgent(agentId, agentData);
        console.log('Agent updated successfully');
        
        toast({
          title: 'Agent updated',
          description: 'Your agent has been updated successfully.',
        });

        router.push(`/agent-builder/agents/${agentId}`);
      } else {
        console.log('Creating agent with data:', agentData);
        const createdAgent = await agentBuilderAPI.createAgent(agentData);
        console.log('Agent created successfully:', createdAgent);
        
        // Clear draft
        localStorage.removeItem('agent_draft');
        
        toast({
          title: 'Agent created',
          description: 'Your agent has been created successfully.',
        });

        router.push('/agent-builder/agents');
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
                      <SelectItem value="ollama">
                        <div className="flex items-center gap-2">
                          <span>Ollama</span>
                          <Badge variant="secondary" className="text-xs">Local</Badge>
                        </div>
                      </SelectItem>
                      <SelectItem value="openai">
                        <div className="flex items-center gap-2">
                          <span>OpenAI</span>
                          <Badge variant="secondary" className="text-xs">Cloud</Badge>
                        </div>
                      </SelectItem>
                      <SelectItem value="claude">
                        <div className="flex items-center gap-2">
                          <span>Claude</span>
                          <Badge variant="secondary" className="text-xs">Cloud</Badge>
                        </div>
                      </SelectItem>
                      <SelectItem value="gemini">
                        <div className="flex items-center gap-2">
                          <span>Gemini</span>
                          <Badge variant="secondary" className="text-xs">Cloud</Badge>
                        </div>
                      </SelectItem>
                      <SelectItem value="grok">
                        <div className="flex items-center gap-2">
                          <span>Grok</span>
                          <Badge variant="secondary" className="text-xs">Cloud</Badge>
                        </div>
                      </SelectItem>
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
                      {form.watch('llm_provider') === 'ollama' && (
                        <>
                          <SelectItem value="llama3.3:70b">Llama 3.3 70B</SelectItem>
                          <SelectItem value="llama3.1:70b">Llama 3.1 70B</SelectItem>
                          <SelectItem value="qwen2.5:72b">Qwen 2.5 72B</SelectItem>
                          <SelectItem value="deepseek-r1:70b">DeepSeek R1 70B</SelectItem>
                          <SelectItem value="mixtral:8x7b">Mixtral 8x7B</SelectItem>
                        </>
                      )}
                      {form.watch('llm_provider') === 'openai' && (
                        <>
                          <SelectItem value="gpt-5">GPT-5</SelectItem>
                          <SelectItem value="o3">GPT-o3</SelectItem>
                          <SelectItem value="o3-mini">GPT-o3 Mini</SelectItem>
                          <SelectItem value="gpt-4o">GPT-4o</SelectItem>
                          <SelectItem value="gpt-4o-mini">GPT-4o Mini</SelectItem>
                        </>
                      )}
                      {form.watch('llm_provider') === 'claude' && (
                        <>
                          <SelectItem value="claude-4.5-sonnet">Claude 4.5 Sonnet</SelectItem>
                          <SelectItem value="claude-4-sonnet">Claude 4 Sonnet</SelectItem>
                          <SelectItem value="claude-3.7-sonnet">Claude 3.7 Sonnet</SelectItem>
                          <SelectItem value="claude-3.5-sonnet">Claude 3.5 Sonnet</SelectItem>
                          <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
                        </>
                      )}
                      {form.watch('llm_provider') === 'gemini' && (
                        <>
                          <SelectItem value="gemini-2.0-flash">Gemini 2.0 Flash</SelectItem>
                          <SelectItem value="gemini-2.0-pro">Gemini 2.0 Pro</SelectItem>
                          <SelectItem value="gemini-1.5-pro">Gemini 1.5 Pro</SelectItem>
                          <SelectItem value="gemini-1.5-flash">Gemini 1.5 Flash</SelectItem>
                          <SelectItem value="gemini-ultra">Gemini Ultra</SelectItem>
                        </>
                      )}
                      {form.watch('llm_provider') === 'grok' && (
                        <>
                          <SelectItem value="grok-3">Grok 3</SelectItem>
                          <SelectItem value="grok-2.5">Grok 2.5</SelectItem>
                          <SelectItem value="grok-2">Grok 2</SelectItem>
                          <SelectItem value="grok-2-mini">Grok 2 Mini</SelectItem>
                          <SelectItem value="grok-vision">Grok Vision</SelectItem>
                        </>
                      )}
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
          <div className="space-y-6">
            <FormField
              control={form.control}
              name="tool_ids"
              render={({ field }) => (
                <FormItem>
                  <FormControl>
                    <AgentToolsPanel
                      agentId={agentId || 'new'}
                      selectedTools={field.value || []}
                      onToolsChange={(newValue) => {
                        field.onChange(newValue);
                      }}
                    />
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
