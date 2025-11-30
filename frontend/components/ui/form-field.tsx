'use client';

/**
 * Form Field Component
 * 
 * Enhanced form field with:
 * - Real-time validation
 * - Error/success states
 * - Helper text
 * - Character counter
 * - Accessibility
 */

import React, { useState, useCallback, useEffect, useId } from 'react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { CheckCircle2, XCircle, AlertCircle, Eye, EyeOff } from 'lucide-react';

type ValidationRule = {
  validate: (value: string) => boolean;
  message: string;
};

type FieldStatus = 'idle' | 'valid' | 'invalid' | 'validating';

interface FormFieldProps {
  name: string;
  label?: string;
  type?: 'text' | 'email' | 'password' | 'number' | 'url' | 'tel' | 'textarea';
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  readOnly?: boolean;
  maxLength?: number;
  minLength?: number;
  pattern?: string;
  rows?: number;
  showCharCount?: boolean;
  showPasswordToggle?: boolean;
  validateOnBlur?: boolean;
  validateOnChange?: boolean;
  debounceMs?: number;
  rules?: ValidationRule[];
  onChange?: (value: string, isValid: boolean) => void;
  onBlur?: (value: string, isValid: boolean) => void;
  onValidate?: (isValid: boolean, errors: string[]) => void;
  className?: string;
  inputClassName?: string;
}

// Built-in validation rules
export const validationRules = {
  required: (message = 'This field is required'): ValidationRule => ({
    validate: (value) => value.trim().length > 0,
    message,
  }),
  email: (message = 'Please enter a valid email'): ValidationRule => ({
    validate: (value) => !value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
    message,
  }),
  url: (message = 'Please enter a valid URL'): ValidationRule => ({
    validate: (value) => {
      if (!value) return true;
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    },
    message,
  }),
  minLength: (min: number, message?: string): ValidationRule => ({
    validate: (value) => !value || value.length >= min,
    message: message || `Must be at least ${min} characters`,
  }),
  maxLength: (max: number, message?: string): ValidationRule => ({
    validate: (value) => !value || value.length <= max,
    message: message || `Must be no more than ${max} characters`,
  }),
  pattern: (regex: RegExp, message: string): ValidationRule => ({
    validate: (value) => !value || regex.test(value),
    message,
  }),
  number: (message = 'Please enter a valid number'): ValidationRule => ({
    validate: (value) => !value || !isNaN(Number(value)),
    message,
  }),
  integer: (message = 'Please enter a whole number'): ValidationRule => ({
    validate: (value) => !value || Number.isInteger(Number(value)),
    message,
  }),
  positive: (message = 'Must be a positive number'): ValidationRule => ({
    validate: (value) => !value || Number(value) > 0,
    message,
  }),
  json: (message = 'Please enter valid JSON'): ValidationRule => ({
    validate: (value) => {
      if (!value) return true;
      try {
        JSON.parse(value);
        return true;
      } catch {
        return false;
      }
    },
    message,
  }),
};

export function FormField({
  name,
  label,
  type = 'text',
  value: controlledValue,
  defaultValue = '',
  placeholder,
  helperText,
  required = false,
  disabled = false,
  readOnly = false,
  maxLength,
  minLength,
  pattern,
  rows = 3,
  showCharCount = false,
  showPasswordToggle = false,
  validateOnBlur = true,
  validateOnChange = false,
  debounceMs = 300,
  rules = [],
  onChange,
  onBlur,
  onValidate,
  className,
  inputClassName,
}: FormFieldProps) {
  const id = useId();
  const [internalValue, setInternalValue] = useState(defaultValue);
  const [status, setStatus] = useState<FieldStatus>('idle');
  const [errors, setErrors] = useState<string[]>([]);
  const [touched, setTouched] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const value = controlledValue ?? internalValue;
  const fieldId = `${id}-${name}`;
  const errorId = `${fieldId}-error`;
  const helperId = `${fieldId}-helper`;

  // Build validation rules
  const allRules = React.useMemo(() => {
    const builtRules: ValidationRule[] = [...rules];
    
    if (required) {
      builtRules.unshift(validationRules.required());
    }
    if (minLength) {
      builtRules.push(validationRules.minLength(minLength));
    }
    if (maxLength) {
      builtRules.push(validationRules.maxLength(maxLength));
    }
    if (type === 'email') {
      builtRules.push(validationRules.email());
    }
    if (type === 'url') {
      builtRules.push(validationRules.url());
    }
    if (type === 'number') {
      builtRules.push(validationRules.number());
    }
    if (pattern) {
      builtRules.push(validationRules.pattern(new RegExp(pattern), 'Invalid format'));
    }

    return builtRules;
  }, [rules, required, minLength, maxLength, type, pattern]);

  // Validate value
  const validate = useCallback((val: string): { isValid: boolean; errors: string[] } => {
    const validationErrors: string[] = [];
    
    for (const rule of allRules) {
      if (!rule.validate(val)) {
        validationErrors.push(rule.message);
      }
    }

    return {
      isValid: validationErrors.length === 0,
      errors: validationErrors,
    };
  }, [allRules]);

  // Debounced validation
  useEffect(() => {
    if (!validateOnChange || !touched) return;

    setStatus('validating');
    const timer = setTimeout(() => {
      const result = validate(value);
      setStatus(result.isValid ? 'valid' : 'invalid');
      setErrors(result.errors);
      onValidate?.(result.isValid, result.errors);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [value, validateOnChange, touched, validate, debounceMs, onValidate]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    
    if (controlledValue === undefined) {
      setInternalValue(newValue);
    }

    const result = validate(newValue);
    onChange?.(newValue, result.isValid);
  }, [controlledValue, validate, onChange]);

  const handleBlur = useCallback(() => {
    setTouched(true);
    
    if (validateOnBlur) {
      const result = validate(value);
      setStatus(result.isValid ? 'valid' : 'invalid');
      setErrors(result.errors);
      onValidate?.(result.isValid, result.errors);
    }

    onBlur?.(value, errors.length === 0);
  }, [value, validateOnBlur, validate, onValidate, onBlur, errors.length]);

  // Status icon
  const StatusIcon = status === 'valid' ? CheckCircle2 : status === 'invalid' ? XCircle : null;
  const statusColor = status === 'valid' ? 'text-green-500' : status === 'invalid' ? 'text-red-500' : '';

  // Input type for password toggle
  const inputType = type === 'password' && showPassword ? 'text' : type === 'textarea' ? undefined : type;

  const inputProps = {
    id: fieldId,
    name,
    value,
    placeholder,
    disabled,
    readOnly,
    maxLength,
    onChange: handleChange,
    onBlur: handleBlur,
    'aria-invalid': status === 'invalid',
    'aria-describedby': [
      errors.length > 0 ? errorId : null,
      helperText ? helperId : null,
    ].filter(Boolean).join(' ') || undefined,
    className: cn(
      inputClassName,
      status === 'invalid' && 'border-red-500 focus-visible:ring-red-500',
      status === 'valid' && touched && 'border-green-500 focus-visible:ring-green-500',
      (StatusIcon || (type === 'password' && showPasswordToggle)) && 'pr-10'
    ),
  };

  return (
    <div className={cn('space-y-1.5', className)}>
      {/* Label */}
      {label && (
        <Label htmlFor={fieldId} className={cn(status === 'invalid' && 'text-red-500')}>
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </Label>
      )}

      {/* Input wrapper */}
      <div className="relative">
        {type === 'textarea' ? (
          <Textarea {...inputProps} rows={rows} />
        ) : (
          <Input {...inputProps} type={inputType} />
        )}

        {/* Status/Password toggle icons */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
          {type === 'password' && showPasswordToggle && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="p-1 text-muted-foreground hover:text-foreground transition-colors"
              tabIndex={-1}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
          {StatusIcon && touched && (
            <StatusIcon className={cn('h-4 w-4', statusColor)} aria-hidden="true" />
          )}
        </div>
      </div>

      {/* Character count */}
      {showCharCount && maxLength && (
        <div className="flex justify-end">
          <span className={cn(
            'text-xs',
            value.length > maxLength * 0.9 ? 'text-amber-500' : 'text-muted-foreground',
            value.length >= maxLength && 'text-red-500'
          )}>
            {value.length}/{maxLength}
          </span>
        </div>
      )}

      {/* Error messages */}
      {status === 'invalid' && errors.length > 0 && (
        <div id={errorId} className="flex items-start gap-1.5 text-red-500" role="alert">
          <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" aria-hidden="true" />
          <div className="text-sm space-y-0.5">
            {errors.map((error, i) => (
              <p key={i}>{error}</p>
            ))}
          </div>
        </div>
      )}

      {/* Helper text */}
      {helperText && status !== 'invalid' && (
        <p id={helperId} className="text-sm text-muted-foreground">
          {helperText}
        </p>
      )}
    </div>
  );
}

// Form wrapper with validation state
interface FormProps {
  children: React.ReactNode;
  onSubmit?: (e: React.FormEvent, isValid: boolean) => void;
  className?: string;
}

export function Form({ children, onSubmit, className }: FormProps) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Check all form fields for validity
    const form = e.target as HTMLFormElement;
    const isValid = form.checkValidity();
    onSubmit?.(e, isValid);
  };

  return (
    <form onSubmit={handleSubmit} className={className} noValidate>
      {children}
    </form>
  );
}
