'use client';

import React from 'react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export interface DropdownOption {
  label: string;
  value: string;
}

export interface DropdownProps {
  id: string;
  title: string;
  value?: string;
  defaultValue?: string;
  options: DropdownOption[];
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  onChange?: (value: string) => void;
  error?: string;
}

export function Dropdown({
  id,
  title,
  value,
  defaultValue,
  options,
  placeholder,
  required,
  disabled,
  onChange,
  error,
}: DropdownProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {title}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <Select
        value={value}
        defaultValue={defaultValue}
        onValueChange={onChange}
        disabled={disabled}
      >
        <SelectTrigger id={id} className={error ? 'border-destructive' : ''}>
          <SelectValue placeholder={placeholder || 'Select an option'} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
