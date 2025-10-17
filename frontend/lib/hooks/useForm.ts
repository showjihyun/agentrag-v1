/**
 * Enhanced form hooks using React Hook Form
 * Provides optimized form handling with validation
 */

import { useForm as useHookForm, UseFormProps, FieldValues } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCallback } from 'react';

// Common form schemas
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
});

export const registerSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

export const querySchema = z.object({
  query: z.string().min(1, 'Query cannot be empty').max(1000, 'Query too long'),
  mode: z.enum(['fast', 'balanced', 'deep']).optional(),
});

export const documentUploadSchema = z.object({
  files: z.array(z.instanceof(File)).min(1, 'At least one file required'),
  tags: z.array(z.string()).optional(),
  isPublic: z.boolean().optional(),
});

// Enhanced useForm hook with Zod validation
export function useForm<TFieldValues extends FieldValues = FieldValues>(
  schema: z.ZodSchema<TFieldValues>,
  options?: Omit<UseFormProps<TFieldValues>, 'resolver'>
) {
  const form = useHookForm<TFieldValues>({
    ...options,
    resolver: zodResolver(schema),
    mode: options?.mode || 'onBlur',
  });

  // Enhanced submit handler with error handling
  const handleSubmit = useCallback(
    (onValid: (data: TFieldValues) => void | Promise<void>) => {
      return form.handleSubmit(
        async (data) => {
          try {
            await onValid(data);
          } catch (error) {
            console.error('Form submission error:', error);
            form.setError('root', {
              type: 'manual',
              message: error instanceof Error ? error.message : 'Submission failed',
            });
          }
        },
        (errors) => {
          console.error('Form validation errors:', errors);
        }
      );
    },
    [form]
  );

  return {
    ...form,
    handleSubmit,
  };
}

// Specific form hooks
export function useLoginForm() {
  return useForm(loginSchema, {
    defaultValues: {
      email: '',
      password: '',
    },
  });
}

export function useRegisterForm() {
  return useForm(registerSchema, {
    defaultValues: {
      username: '',
      email: '',
      password: '',
      confirmPassword: '',
    },
  });
}

export function useQueryForm() {
  return useForm(querySchema, {
    defaultValues: {
      query: '',
      mode: 'balanced',
    },
  });
}

export function useDocumentUploadForm() {
  return useForm(documentUploadSchema, {
    defaultValues: {
      files: [],
      tags: [],
      isPublic: false,
    },
  });
}
