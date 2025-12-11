/**
 * ToolConfigField - Common field components for Tool Configurations
 * 
 * Provides reusable form field patterns with consistent styling
 */

'use client';

import { memo, ReactNode } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Button } from '@/components/ui/button';
import { LucideIcon, Plus, Trash, HelpCircle } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

// ============================================
// Base Field Wrapper
// ============================================

interface FieldWrapperProps {
  label: string;
  required?: boolean;
  icon?: LucideIcon;
  hint?: string;
  tooltip?: string;
  children: ReactNode;
}

export const FieldWrapper = memo(function FieldWrapper({
  label,
  required,
  icon: Icon,
  hint,
  tooltip,
  children,
}: FieldWrapperProps) {
  return (
    <div className="space-y-2">
      <Label className="flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4" />}
        {label}
        {required && <span className="text-red-500">*</span>}
        {tooltip && (
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              <p className="text-xs">{tooltip}</p>
            </TooltipContent>
          </Tooltip>
        )}
      </Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
});

// ============================================
// Text Input Field
// ============================================

interface TextFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: 'text' | 'password' | 'email' | 'url' | 'number';
  required?: boolean;
  icon?: LucideIcon;
  hint?: string;
  tooltip?: string;
  className?: string;
  mono?: boolean;
}

export const TextField = memo(function TextField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  required,
  icon,
  hint,
  tooltip,
  className,
  mono,
}: TextFieldProps) {
  return (
    <FieldWrapper label={label} required={required} icon={icon} hint={hint} tooltip={tooltip}>
      <Input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`${mono ? 'font-mono text-sm' : ''} ${className || ''}`}
      />
    </FieldWrapper>
  );
});

// ============================================
// Number Input Field
// ============================================

interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
  icon?: LucideIcon;
  hint?: string;
  tooltip?: string;
}

export const NumberField = memo(function NumberField({
  label,
  value,
  onChange,
  min,
  max,
  step = 1,
  required,
  icon,
  hint,
  tooltip,
}: NumberFieldProps) {
  return (
    <FieldWrapper label={label} required={required} icon={icon} hint={hint} tooltip={tooltip}>
      <Input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
      />
    </FieldWrapper>
  );
});

// ============================================
// Textarea Field
// ============================================

interface TextareaFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  rows?: number;
  required?: boolean;
  icon?: LucideIcon;
  hint?: string;
  tooltip?: string;
  mono?: boolean;
}

export const TextareaField = memo(function TextareaField({
  label,
  value,
  onChange,
  placeholder,
  rows = 4,
  required,
  icon,
  hint,
  tooltip,
  mono,
}: TextareaFieldProps) {
  return (
    <FieldWrapper label={label} required={required} icon={icon} hint={hint} tooltip={tooltip}>
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className={mono ? 'font-mono text-sm' : ''}
      />
    </FieldWrapper>
  );
});

// ============================================
// Select Field
// ============================================

interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
  required?: boolean;
  icon?: LucideIcon;
  hint?: string;
  tooltip?: string;
}

export const SelectField = memo(function SelectField({
  label,
  value,
  onChange,
  options,
  placeholder,
  required,
  icon,
  hint,
  tooltip,
}: SelectFieldProps) {
  return (
    <FieldWrapper label={label} required={required} icon={icon} hint={hint} tooltip={tooltip}>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger>
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.description ? (
                <div className="flex flex-col">
                  <span className="font-medium">{option.label}</span>
                  <span className="text-xs text-muted-foreground">{option.description}</span>
                </div>
              ) : (
                option.label
              )}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </FieldWrapper>
  );
});

// ============================================
// Switch Field
// ============================================

interface SwitchFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  tooltip?: string;
}

export const SwitchField = memo(function SwitchField({
  label,
  description,
  checked,
  onChange,
  tooltip,
}: SwitchFieldProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <Label className="flex items-center gap-2">
          {label}
          {tooltip && (
            <Tooltip>
              <TooltipTrigger asChild>
                <HelpCircle className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-xs">{tooltip}</p>
              </TooltipContent>
            </Tooltip>
          )}
        </Label>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      <Switch checked={checked} onCheckedChange={onChange} />
    </div>
  );
});

// ============================================
// Key-Value List Field
// ============================================

interface KeyValueItem {
  key: string;
  value: string;
}

interface KeyValueListFieldProps {
  label: string;
  items: KeyValueItem[];
  onAdd: () => void;
  onUpdate: (index: number, field: 'key' | 'value', value: string) => void;
  onRemove: (index: number) => void;
  keyPlaceholder?: string;
  valuePlaceholder?: string;
  addButtonText?: string;
  hint?: string;
}

export const KeyValueListField = memo(function KeyValueListField({
  label,
  items,
  onAdd,
  onUpdate,
  onRemove,
  keyPlaceholder = 'Key',
  valuePlaceholder = 'Value',
  addButtonText = 'Add Item',
  hint,
}: KeyValueListFieldProps) {
  return (
    <div className="space-y-3">
      <Label>{label} ({items.length})</Label>
      {items.map((item, index) => (
        <div key={index} className="flex gap-2">
          <Input
            placeholder={keyPlaceholder}
            value={item.key}
            onChange={(e) => onUpdate(index, 'key', e.target.value)}
            className="flex-1"
          />
          <Input
            placeholder={valuePlaceholder}
            value={item.value}
            onChange={(e) => onUpdate(index, 'value', e.target.value)}
            className="flex-1"
          />
          <Button variant="ghost" size="icon" onClick={() => onRemove(index)}>
            <Trash className="h-4 w-4" />
          </Button>
        </div>
      ))}
      <Button variant="outline" size="sm" onClick={onAdd} className="w-full">
        <Plus className="h-4 w-4 mr-2" />
        {addButtonText}
      </Button>
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
});

// ============================================
// Info Box
// ============================================

interface InfoBoxProps {
  title?: string;
  children: ReactNode;
  variant?: 'default' | 'info' | 'warning' | 'success';
}

const INFO_BOX_STYLES = {
  default: 'bg-muted',
  info: 'bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800',
  warning: 'bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800',
  success: 'bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800',
};

export const InfoBox = memo(function InfoBox({
  title,
  children,
  variant = 'default',
}: InfoBoxProps) {
  return (
    <div className={`p-3 rounded-lg ${INFO_BOX_STYLES[variant]}`}>
      {title && <p className="text-xs font-medium mb-1">{title}</p>}
      <div className="text-xs text-muted-foreground">{children}</div>
    </div>
  );
});
