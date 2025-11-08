'use client';

import React, { useMemo } from 'react';
import { ShortInput, ShortInputProps } from './ShortInput';
import { LongInput, LongInputProps } from './LongInput';
import { Dropdown, DropdownProps } from './Dropdown';
import { CodeEditor, CodeEditorProps } from './CodeEditor';
import { OAuthInput, OAuthInputProps } from './OAuthInput';
import { KnowledgeBaseInput, KnowledgeBaseInputProps } from './KnowledgeBaseInput';

export interface SubBlockConfig {
  id: string;
  type: 'short-input' | 'long-input' | 'dropdown' | 'code' | 'oauth-input' | 'knowledge-base';
  title: string;
  defaultValue?: any;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  options?: Array<{ label: string; value: string }>;
  language?: string;
  provider?: string;
  condition?: {
    field: string;
    operator: 'equals' | 'not_equals' | 'contains' | 'not_contains';
    value: any;
  };
  [key: string]: any;
}

export interface SubBlockRendererProps {
  subBlocks: SubBlockConfig[];
  values: Record<string, any>;
  errors?: Record<string, string>;
  onChange: (id: string, value: any) => void;
  onOAuthConnect?: (id: string) => void;
  onOAuthDisconnect?: (id: string) => void;
}

export function SubBlockRenderer({
  subBlocks,
  values,
  errors = {},
  onChange,
  onOAuthConnect,
  onOAuthDisconnect,
}: SubBlockRendererProps) {
  // Evaluate condition for a subblock
  const evaluateCondition = (condition: SubBlockConfig['condition']): boolean => {
    if (!condition) return true;

    const fieldValue = values[condition.field];
    const { operator, value } = condition;

    switch (operator) {
      case 'equals':
        return fieldValue === value;
      case 'not_equals':
        return fieldValue !== value;
      case 'contains':
        return String(fieldValue || '').includes(String(value));
      case 'not_contains':
        return !String(fieldValue || '').includes(String(value));
      default:
        return true;
    }
  };

  // Filter visible subblocks based on conditions
  const visibleSubBlocks = useMemo(() => {
    return subBlocks.filter((subBlock) => evaluateCondition(subBlock.condition));
  }, [subBlocks, values]);

  return (
    <div className="space-y-4">
      {visibleSubBlocks.map((subBlock) => {
        const commonProps = {
          id: subBlock.id,
          title: subBlock.title,
          value: values[subBlock.id],
          defaultValue: subBlock.defaultValue,
          placeholder: subBlock.placeholder,
          required: subBlock.required,
          disabled: subBlock.disabled,
          error: errors[subBlock.id],
        };

        switch (subBlock.type) {
          case 'short-input':
            return (
              <ShortInput
                key={subBlock.id}
                {...(commonProps as ShortInputProps)}
                onChange={(value) => onChange(subBlock.id, value)}
              />
            );

          case 'long-input':
            return (
              <LongInput
                key={subBlock.id}
                {...(commonProps as LongInputProps)}
                rows={subBlock.rows}
                onChange={(value) => onChange(subBlock.id, value)}
              />
            );

          case 'dropdown':
            return (
              <Dropdown
                key={subBlock.id}
                {...(commonProps as DropdownProps)}
                options={subBlock.options || []}
                onChange={(value) => onChange(subBlock.id, value)}
              />
            );

          case 'code':
            return (
              <CodeEditor
                key={subBlock.id}
                {...(commonProps as CodeEditorProps)}
                language={subBlock.language}
                height={subBlock.height}
                onChange={(value) => onChange(subBlock.id, value)}
              />
            );

          case 'oauth-input':
            return (
              <OAuthInput
                key={subBlock.id}
                {...commonProps}
                provider={subBlock.provider || 'OAuth Provider'}
                isConnected={subBlock.isConnected}
                accountInfo={subBlock.accountInfo}
                onConnect={() => onOAuthConnect?.(subBlock.id)}
                onDisconnect={() => onOAuthDisconnect?.(subBlock.id)}
              />
            );

          case 'knowledge-base':
            return (
              <KnowledgeBaseInput
                key={subBlock.id}
                {...(commonProps as KnowledgeBaseInputProps)}
                onChange={(value) => onChange(subBlock.id, value)}
              />
            );

          default:
            return null;
        }
      })}
    </div>
  );
}
