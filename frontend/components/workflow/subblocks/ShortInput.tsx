'use client';

import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export interface ShortInputProps {
  id: string;
  title: string;
  value?: string;
  defaultValue?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  onChange?: (value: string) => void;
  error?: string;
}

export function ShortInput({
  id,
  title,
  value,
  defaultValue,
  placeholder,
  required,
  disabled,
  onChange,
  error,
}: ShortInputProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {title}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <Input
        id={id}
        value={value}
        defaultValue={defaultValue}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        onChange={(e) => onChange?.(e.target.value)}
        className={error ? 'border-destructive' : ''}
      />
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
