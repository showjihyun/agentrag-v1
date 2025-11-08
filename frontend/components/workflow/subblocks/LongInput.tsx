'use client';

import React from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';

export interface LongInputProps {
  id: string;
  title: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  rows?: number;
  onChange?: (value: string) => void;
  error?: string;
}

export function LongInput({
  id,
  title,
  value,
  defaultValue,
  placeholder,
  required,
  disabled,
  rows = 4,
  onChange,
  error,
}: LongInputProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {title}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <Textarea
        id={id}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        rows={rows}
        onChange={(e) => onChange?.(e.target.value)}
        className={error ? 'border-destructive' : ''}
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
