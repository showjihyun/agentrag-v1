'use client';

import { useEffect } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Variable, VariableCreate } from '@/lib/api/agent-builder';

const variableSchema = z.object({
  name: z
    .string()
    .min(1, 'Variable name is required')
    .regex(/^[A-Z][A-Z0-9_]*$/, 'Variable name must be in UPPER_SNAKE_CASE'),
  scope: z.enum(['global', 'workspace', 'user', 'agent']),
  scope_id: z.string().optional(),
  value_type: z.enum(['string', 'number', 'boolean', 'json']),
  value: z.string().min(1, 'Value is required'),
  is_secret: z.boolean().default(false),
});

type VariableFormValues = z.infer<typeof variableSchema>;

interface VariableEditorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variable?: Variable | null;
  onSaved: () => void;
}

export function VariableEditor({ open, onOpenChange, variable, onSaved }: VariableEditorProps) {
  const { toast } = useToast();
  const isEditing = !!variable;

  const form = useForm<VariableFormValues>({
    resolver: zodResolver(variableSchema),
    defaultValues: {
      name: '',
      scope: 'user',
      scope_id: undefined,
      value_type: 'string',
      value: '',
      is_secret: false,
    },
  });

  useEffect(() => {
    if (variable) {
      form.reset({
        name: variable.name,
        scope: variable.scope,
        scope_id: variable.scope_id,
        value_type: variable.value_type,
        value: variable.value,
        is_secret: variable.is_secret,
      });
    } else {
      form.reset({
        name: '',
        scope: 'user',
        scope_id: undefined,
        value_type: 'string',
        value: '',
        is_secret: false,
      });
    }
  }, [variable, form]);

  const onSubmit = async (data: VariableFormValues) => {
    try {
      // Validate JSON if type is json
      if (data.value_type === 'json') {
        try {
          JSON.parse(data.value);
        } catch (error) {
          form.setError('value', {
            type: 'manual',
            message: 'Invalid JSON format',
          });
          return;
        }
      }

      // Validate number if type is number
      if (data.value_type === 'number') {
        if (isNaN(Number(data.value))) {
          form.setError('value', {
            type: 'manual',
            message: 'Invalid number format',
          });
          return;
        }
      }

      // Validate boolean if type is boolean
      if (data.value_type === 'boolean') {
        const lowerValue = data.value.toLowerCase();
        if (!['true', 'false', '1', '0', 'yes', 'no'].includes(lowerValue)) {
          form.setError('value', {
            type: 'manual',
            message: 'Invalid boolean format (use true/false, 1/0, or yes/no)',
          });
          return;
        }
      }

      if (isEditing) {
        await agentBuilderAPI.updateVariable(variable.id, {
          name: data.name,
          value: data.value,
          value_type: data.value_type,
        });
        toast({
          title: 'Variable updated',
          description: 'The variable has been updated successfully',
        });
      } else {
        const createData: VariableCreate = {
          name: data.name,
          scope: data.scope,
          scope_id: data.scope_id,
          value_type: data.value_type,
          value: data.value,
          is_secret: data.is_secret,
        };
        await agentBuilderAPI.createVariable(createData);
        toast({
          title: 'Variable created',
          description: 'The variable has been created successfully',
        });
      }

      onSaved();
      form.reset();
    } catch (error: any) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: error.message || `Failed to ${isEditing ? 'update' : 'create'} variable`,
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Edit Variable' : 'Create Variable'}</DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the variable configuration'
              : 'Add a new variable or secret to your workspace'}
          </DialogDescription>
        </DialogHeader>

        <FormProvider {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Variable Name</FormLabel>
                  <FormControl>
                    <Input
                      placeholder="MY_VARIABLE"
                      {...field}
                      disabled={isEditing}
                      className="font-mono"
                    />
                  </FormControl>
                  <FormDescription>
                    Use UPPER_SNAKE_CASE for variable names (e.g., API_KEY, DATABASE_URL)
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!isEditing && (
              <FormField
                control={form.control}
                name="scope"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scope</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select scope" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="global">Global</SelectItem>
                        <SelectItem value="workspace">Workspace</SelectItem>
                        <SelectItem value="user">User</SelectItem>
                        <SelectItem value="agent">Agent</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Scope determines where this variable is accessible
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <FormField
              control={form.control}
              name="value_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="string">String</SelectItem>
                      <SelectItem value="number">Number</SelectItem>
                      <SelectItem value="boolean">Boolean</SelectItem>
                      <SelectItem value="json">JSON</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>The data type of the variable value</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="value"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Value</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder={
                        form.watch('value_type') === 'json'
                          ? '{"key": "value"}'
                          : form.watch('value_type') === 'number'
                          ? '42'
                          : form.watch('value_type') === 'boolean'
                          ? 'true'
                          : 'Enter value...'
                      }
                      className="font-mono text-sm min-h-[100px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    {form.watch('value_type') === 'json' && 'Enter valid JSON'}
                    {form.watch('value_type') === 'number' && 'Enter a numeric value'}
                    {form.watch('value_type') === 'boolean' &&
                      'Enter true/false, 1/0, or yes/no'}
                    {form.watch('value_type') === 'string' && 'Enter any text value'}
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            {!isEditing && (
              <FormField
                control={form.control}
                name="is_secret"
                render={({ field }) => (
                  <FormItem className="flex items-center justify-between rounded-lg border p-4">
                    <div className="space-y-0.5">
                      <FormLabel className="text-base">Secret</FormLabel>
                      <FormDescription>
                        Encrypt this variable value for secure storage
                      </FormDescription>
                    </div>
                    <FormControl>
                      <Switch checked={field.value} onCheckedChange={field.onChange} />
                    </FormControl>
                  </FormItem>
                )}
              />
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  onOpenChange(false);
                  form.reset();
                }}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting
                  ? isEditing
                    ? 'Updating...'
                    : 'Creating...'
                  : isEditing
                  ? 'Update Variable'
                  : 'Create Variable'}
              </Button>
            </DialogFooter>
          </form>
        </FormProvider>
      </DialogContent>
    </Dialog>
  );
}
