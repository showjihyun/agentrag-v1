'use client';

import { useState, useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Block, BlockCreate, BlockUpdate } from '@/lib/api/agent-builder';
import dynamic from 'next/dynamic';

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

const blockFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
  block_type: z.enum(['llm', 'tool', 'logic', 'composite']),
  input_schema: z.string().optional(),
  output_schema: z.string().optional(),
  configuration: z.string().optional(),
  implementation: z.string().optional(),
});

type BlockFormValues = z.infer<typeof blockFormSchema>;

interface BlockEditorProps {
  blockId?: string;
  onSave?: (block: Block) => void;
  onCancel?: () => void;
}

export default function BlockEditor({ blockId, onSave, onCancel }: BlockEditorProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!blockId);

  const form = useForm<BlockFormValues>({
    resolver: zodResolver(blockFormSchema),
    defaultValues: {
      name: '',
      description: '',
      block_type: 'llm',
      input_schema: '{\n  "type": "object",\n  "properties": {\n    "input": {\n      "type": "string"\n    }\n  }\n}',
      output_schema: '{\n  "type": "object",\n  "properties": {\n    "output": {\n      "type": "string"\n    }\n  }\n}',
      configuration: '{}',
      implementation: '',
    },
  });

  const blockType = form.watch('block_type');

  useEffect(() => {
    if (blockId) {
      loadBlock();
    }
  }, [blockId]);

  const loadBlock = async () => {
    if (!blockId) return;

    try {
      setInitialLoading(true);
      const block = await agentBuilderAPI.getBlock(blockId);
      
      form.reset({
        name: block.name,
        description: block.description || '',
        block_type: block.block_type,
        input_schema: JSON.stringify(block.input_schema || {}, null, 2),
        output_schema: JSON.stringify(block.output_schema || {}, null, 2),
        configuration: JSON.stringify(block.configuration || {}, null, 2),
        implementation: block.implementation || '',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load block',
        variant: 'destructive',
      });
    } finally {
      setInitialLoading(false);
    }
  };

  const onSubmit = async (values: BlockFormValues) => {
    try {
      setLoading(true);

      // Parse JSON fields
      let inputSchema, outputSchema, configuration;
      
      try {
        inputSchema = values.input_schema ? JSON.parse(values.input_schema) : undefined;
      } catch (e) {
        toast({
          title: 'Invalid Input Schema',
          description: 'Input schema must be valid JSON',
          variant: 'destructive',
        });
        return;
      }

      try {
        outputSchema = values.output_schema ? JSON.parse(values.output_schema) : undefined;
      } catch (e) {
        toast({
          title: 'Invalid Output Schema',
          description: 'Output schema must be valid JSON',
          variant: 'destructive',
        });
        return;
      }

      try {
        configuration = values.configuration ? JSON.parse(values.configuration) : undefined;
      } catch (e) {
        toast({
          title: 'Invalid Configuration',
          description: 'Configuration must be valid JSON',
          variant: 'destructive',
        });
        return;
      }

      const blockData = {
        name: values.name,
        description: values.description,
        block_type: values.block_type,
        input_schema: inputSchema,
        output_schema: outputSchema,
        configuration,
        implementation: values.implementation,
      };

      let savedBlock: Block;
      if (blockId) {
        savedBlock = await agentBuilderAPI.updateBlock(blockId, blockData as BlockUpdate);
        toast({
          title: 'Success',
          description: 'Block updated successfully',
        });
      } else {
        savedBlock = await agentBuilderAPI.createBlock(blockData as BlockCreate);
        toast({
          title: 'Success',
          description: 'Block created successfully',
        });
      }

      if (onSave) {
        onSave(savedBlock);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: blockId ? 'Failed to update block' : 'Failed to create block',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{blockId ? 'Edit Block' : 'Create New Block'}</CardTitle>
        <CardDescription>
          Configure your reusable block component
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
                    <FormLabel>Block Name</FormLabel>
                    <FormControl>
                      <Input placeholder="My Custom Block" {...field} />
                    </FormControl>
                    <FormDescription>
                      A unique name for your block
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
                        placeholder="Describe what your block does..."
                        className="resize-none"
                        rows={3}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="block_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Block Type</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select block type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="llm">LLM Block</SelectItem>
                        <SelectItem value="tool">Tool Block</SelectItem>
                        <SelectItem value="logic">Logic Block</SelectItem>
                        <SelectItem value="composite">Composite Block</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      {blockType === 'llm' && 'Executes an LLM call with a prompt template'}
                      {blockType === 'tool' && 'Invokes a single tool or function'}
                      {blockType === 'logic' && 'Runs custom Python code'}
                      {blockType === 'composite' && 'Combines multiple blocks into a workflow'}
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Separator />

            {/* Schema Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Input/Output Schema</h3>
              
              <FormField
                control={form.control}
                name="input_schema"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Input Schema (JSON)</FormLabel>
                    <FormControl>
                      <div className="border rounded-md overflow-hidden">
                        <MonacoEditor
                          height="200px"
                          language="json"
                          theme="vs-dark"
                          value={field.value}
                          onChange={(value) => field.onChange(value || '')}
                          options={{
                            minimap: { enabled: false },
                            fontSize: 12,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                          }}
                        />
                      </div>
                    </FormControl>
                    <FormDescription>
                      JSON Schema defining the block's input parameters
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="output_schema"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Output Schema (JSON)</FormLabel>
                    <FormControl>
                      <div className="border rounded-md overflow-hidden">
                        <MonacoEditor
                          height="200px"
                          language="json"
                          theme="vs-dark"
                          value={field.value}
                          onChange={(value) => field.onChange(value || '')}
                          options={{
                            minimap: { enabled: false },
                            fontSize: 12,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                          }}
                        />
                      </div>
                    </FormControl>
                    <FormDescription>
                      JSON Schema defining the block's output structure
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <Separator />

            {/* Implementation */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Implementation</h3>
              
              {blockType === 'logic' && (
                <FormField
                  control={form.control}
                  name="implementation"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Python Code</FormLabel>
                      <FormControl>
                        <div className="border rounded-md overflow-hidden">
                          <MonacoEditor
                            height="300px"
                            language="python"
                            theme="vs-dark"
                            value={field.value}
                            onChange={(value) => field.onChange(value || '')}
                            options={{
                              minimap: { enabled: false },
                              fontSize: 12,
                              lineNumbers: 'on',
                              scrollBeyondLastLine: false,
                              automaticLayout: true,
                            }}
                          />
                        </div>
                      </FormControl>
                      <FormDescription>
                        Python code to execute. Input available as 'input_data' variable.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="configuration"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Configuration (JSON)</FormLabel>
                    <FormControl>
                      <div className="border rounded-md overflow-hidden">
                        <MonacoEditor
                          height="150px"
                          language="json"
                          theme="vs-dark"
                          value={field.value}
                          onChange={(value) => field.onChange(value || '')}
                          options={{
                            minimap: { enabled: false },
                            fontSize: 12,
                            lineNumbers: 'on',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                          }}
                        />
                      </div>
                    </FormControl>
                    <FormDescription>
                      Additional configuration parameters for the block
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            {/* Form Actions */}
            <div className="flex justify-end gap-4">
              {onCancel && (
                <Button type="button" variant="outline" onClick={onCancel}>
                  Cancel
                </Button>
              )}
              <Button type="submit" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                {blockId ? 'Update Block' : 'Create Block'}
              </Button>
            </div>
          </form>
        </FormProvider>
      </CardContent>
    </Card>
  );
}
