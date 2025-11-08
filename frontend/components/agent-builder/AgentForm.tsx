'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { useToast } from '@/components/Toast';
import { agentBuilderAPI, type AgentCreate } from '@/lib/api/agent-builder';
import { Loader2, Plus, Code } from 'lucide-react';
import { useRouter } from 'next/navigation';

// Dynamic imports for heavy components
const ToolSelector = dynamic(() => import('./ToolSelector').then(mod => ({ default: mod.ToolSelector })), {
  loading: () => <Skeleton className="h-[200px] w-full" />,
  ssr: false,
});

const PromptTemplateEditor = dynamic(() => import('./PromptTemplateEditor').then(mod => ({ default: mod.PromptTemplateEditor })), {
  loading: () => <Skeleton className="h-[400px] w-full" />,
  ssr: false,
});

const agentFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  agent_type: z.string().default('custom'),
  llm_provider: z.string().min(1, 'LLM provider is required'),
  llm_model: z.string().min(1, 'LLM model is required'),
  prompt_template: z.string().optional(),
  tool_ids: z.array(z.string()).optional(),
});

type AgentFormValues = z.infer<typeof agentFormSchema>;

interface AgentFormProps {
  initialData?: Partial<AgentFormValues>;
  agentId?: string;
  onSuccess?: () => void;
}

export function AgentForm({ initialData, agentId, onSuccess }: AgentFormProps) {
  const router = useRouter();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [showAdvancedEditor, setShowAdvancedEditor] = React.useState(false);

  const form = useForm<AgentFormValues>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: initialData?.name || '',
      description: initialData?.description || '',
      agent_type: initialData?.agent_type || 'custom',
      llm_provider: initialData?.llm_provider || 'ollama',
      llm_model: initialData?.llm_model || 'llama3.1',
      prompt_template: initialData?.prompt_template || '',
      tool_ids: initialData?.tool_ids || [],
    },
  });

  const onSubmit = async (data: AgentFormValues) => {
    setIsSubmitting(true);
    try {
      const agentData: AgentCreate = {
        name: data.name,
        description: data.description,
        agent_type: data.agent_type,
        llm_provider: data.llm_provider,
        llm_model: data.llm_model,
        prompt_template: data.prompt_template,
        tool_ids: data.tool_ids,
      };

      if (agentId) {
        await agentBuilderAPI.updateAgent(agentId, agentData);
        toast({
          title: 'Agent updated',
          description: 'Your agent has been updated successfully.',
        });
      } else {
        await agentBuilderAPI.createAgent(agentData);
        toast({
          title: 'Agent created',
          description: 'Your agent has been created successfully.',
        });
      }

      onSuccess?.();
      router.push('/agent-builder/agents');
    } catch (error) {
      // Import error handler
      const { ErrorHandler } = await import('@/lib/errors');
      
      // Log error
      ErrorHandler.log(error, 'AgentForm.onSubmit');
      
      // Handle error
      const errorInfo = ErrorHandler.handle(error);
      toast({
        variant: errorInfo.variant,
        title: errorInfo.title,
        description: errorInfo.description,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    router.back();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{agentId ? 'Edit Agent' : 'Create New Agent'}</CardTitle>
        <CardDescription>
          Configure your agent with tools, prompts, and settings
        </CardDescription>
      </CardHeader>
      <CardContent>
        <FormProvider {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Basic Information</h3>

              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Agent Name</FormLabel>
                    <FormControl>
                      <Input placeholder="My Custom Agent" {...field} />
                    </FormControl>
                    <FormDescription>
                      A unique name for your agent
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
                        placeholder="Describe what your agent does..."
                        className="resize-none"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Separator />

            {/* LLM Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">LLM Configuration</h3>

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="llm_provider"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>LLM Provider</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select provider" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="ollama">Ollama</SelectItem>
                          <SelectItem value="openai">OpenAI</SelectItem>
                          <SelectItem value="claude">Claude</SelectItem>
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
                      <FormLabel>Model</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        defaultValue={field.value}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select model" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="llama3.1">Llama 3.1</SelectItem>
                          <SelectItem value="gpt-4">GPT-4</SelectItem>
                          <SelectItem value="claude-3">Claude 3</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <Separator />

            {/* Tool Selection */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Tools</h3>
              </div>

              <FormField
                control={form.control}
                name="tool_ids"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      <ToolSelector
                        selectedTools={field.value || []}
                        onSelectionChange={field.onChange}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Separator />

            {/* Prompt Template */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Prompt Template</h3>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAdvancedEditor(true)}
                >
                  <Code className="mr-2 h-4 w-4" />
                  Advanced Editor
                </Button>
              </div>

              <FormField
                control={form.control}
                name="prompt_template"
                render={({ field }) => (
                  <FormItem>
                    <FormControl>
                      {showAdvancedEditor ? (
                        <PromptTemplateEditor
                          value={field.value || ''}
                          onChange={field.onChange}
                          onClose={() => setShowAdvancedEditor(false)}
                        />
                      ) : (
                        <Textarea
                          placeholder="Enter your prompt template with variables like ${query}, ${context}..."
                          className="font-mono text-sm min-h-[200px]"
                          {...field}
                        />
                      )}
                    </FormControl>
                    <FormDescription>
                      Use ${'{variable_name}'} for variable substitution
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Form Actions */}
            <div className="flex justify-end gap-4">
              <Button type="button" variant="outline" onClick={handleCancel}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
                {agentId ? 'Update Agent' : 'Create Agent'}
              </Button>
            </div>
          </form>
        </FormProvider>
      </CardContent>
    </Card>
  );
}
