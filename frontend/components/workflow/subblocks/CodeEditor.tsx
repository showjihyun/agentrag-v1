'use client';

import React from 'react';
import { Label } from '@/components/ui/label';
import Editor from '@monaco-editor/react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSafeTheme } from '../ThemeWrapper';

export interface CodeEditorProps {
  id: string;
  title: string;
  value?: string;
  defaultValue?: string;
  language?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  height?: string;
  onChange?: (value: string | undefined) => void;
  error?: string;
}

export function CodeEditor({
  id,
  title,
  value,
  defaultValue,
  language = 'json',
  placeholder,
  required,
  disabled,
  height = '200px',
  onChange,
  error,
}: CodeEditorProps) {
  const { theme } = useSafeTheme();

  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {title}
        {required && <span className="text-destructive ml-1">*</span>}
      </Label>
      <div className={`border rounded-md overflow-hidden ${error ? 'border-destructive' : ''}`}>
        <Editor
          height={height}
          language={language}
          value={value}
          defaultValue={defaultValue}
          theme={theme === 'dark' ? 'vs-dark' : 'light'}
          onChange={onChange}
          options={{
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            lineNumbers: 'on',
            readOnly: disabled,
            wordWrap: 'on',
            automaticLayout: true,
          }}
        />
      </div>
      {placeholder && !value && (
        <p className="text-xs text-muted-foreground">{placeholder}</p>
      )}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}

