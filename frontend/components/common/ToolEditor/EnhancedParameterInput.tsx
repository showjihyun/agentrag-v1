"use client";

/**
 * Enhanced Parameter Input - n8n/crew.ai style
 * 
 * Features:
 * - All options provided via Select Box
 * - Easy variable reference input
 * - Autocomplete support
 * - Expression builder
 */

import React, { useState, useEffect } from "react";
import {
  ChevronDown, Variable, Code, Sparkles, Plus, X, Check
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ParameterInputProps } from "./types";

// Common options definition (n8n/crew.ai style)
const COMMON_OPTIONS = {
  // AI Models
  ai_models: {
    openai: ['gpt-4', 'gpt-4-turbo', 'gpt-4-turbo-preview', 'gpt-3.5-turbo', 'gpt-3.5-turbo-16k'],
    anthropic: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-2.1', 'claude-2'],
    google: ['gemini-pro', 'gemini-pro-vision', 'gemini-ultra'],
    ollama: ['llama2', 'llama2:13b', 'llama2:70b', 'mistral', 'mixtral', 'codellama'],
  },
  
  // HTTP Methods
  http_methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'],
  
  // Content Types
  content_types: [
    'application/json',
    'application/x-www-form-urlencoded',
    'multipart/form-data',
    'text/plain',
    'text/html',
    'application/xml',
  ],
  
  // Languages
  languages: ['en', 'ko', 'ja', 'zh', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ar'],
  
  // Date Ranges
  date_ranges: ['today', 'yesterday', 'past_week', 'past_month', 'past_year', 'custom'],
  
  // Common Numbers
  common_numbers: [1, 5, 10, 20, 50, 100, 500, 1000],
  
  // Timeouts (seconds)
  timeouts: [5, 10, 30, 60, 120, 300, 600],
  
  // Temperature (AI)
  temperatures: [0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.8, 0.9, 1.0, 1.5, 2.0],
  
  // Max Tokens
  max_tokens: [100, 256, 512, 1000, 2000, 4000, 8000, 16000],
};

// Variable reference templates
const VARIABLE_TEMPLATES = [
  { label: 'Workflow Input', value: '{{ workflow.input }}', category: 'workflow' },
  { label: 'Previous Block Output', value: '{{ previousBlock.output }}', category: 'workflow' },
  { label: 'Current User', value: '{{ user.id }}', category: 'user' },
  { label: 'Current Time', value: '{{ now() }}', category: 'functions' },
  { label: 'Random Number', value: '{{ random() }}', category: 'functions' },
  { label: 'Environment Variable', value: '{{ env.VARIABLE_NAME }}', category: 'env' },
];

export function EnhancedParameterInput({
  name,
  config,
  value,
  onChange,
  error,
  disabled = false,
}: ParameterInputProps) {
  const [inputMode, setInputMode] = useState<'select' | 'expression' | 'manual'>('select');
  const [showVariables, setShowVariables] = useState(false);

  // Determine appropriate options based on parameter name and type
  const getOptionsForParameter = () => {
    const paramLower = name.toLowerCase();
    
    // AI Model related
    if (paramLower.includes('model')) {
      if (paramLower.includes('openai') || paramLower.includes('gpt')) {
        return COMMON_OPTIONS.ai_models.openai;
      }
      if (paramLower.includes('anthropic') || paramLower.includes('claude')) {
        return COMMON_OPTIONS.ai_models.anthropic;
      }
      if (paramLower.includes('google') || paramLower.includes('gemini')) {
        return COMMON_OPTIONS.ai_models.google;
      }
      if (paramLower.includes('ollama')) {
        return COMMON_OPTIONS.ai_models.ollama;
      }
      // All AI models combined
      return [
        ...COMMON_OPTIONS.ai_models.openai,
        ...COMMON_OPTIONS.ai_models.anthropic,
        ...COMMON_OPTIONS.ai_models.google,
        ...COMMON_OPTIONS.ai_models.ollama,
      ];
    }
    
    // HTTP Method
    if (paramLower.includes('method') || paramLower === 'verb') {
      return COMMON_OPTIONS.http_methods;
    }
    
    // Content Type
    if (paramLower.includes('content') && paramLower.includes('type')) {
      return COMMON_OPTIONS.content_types;
    }
    
    // Language
    if (paramLower.includes('language') || paramLower.includes('lang')) {
      return COMMON_OPTIONS.languages;
    }
    
    // Date Range
    if (paramLower.includes('date') && paramLower.includes('range')) {
      return COMMON_OPTIONS.date_ranges;
    }
    
    // Temperature
    if (paramLower.includes('temperature')) {
      return COMMON_OPTIONS.temperatures.map(String);
    }
    
    // Max Tokens
    if (paramLower.includes('token') || paramLower.includes('max_length')) {
      return COMMON_OPTIONS.max_tokens.map(String);
    }
    
    // Timeout
    if (paramLower.includes('timeout')) {
      return COMMON_OPTIONS.timeouts.map(String);
    }
    
    // Max Results / Limit
    if (paramLower.includes('max') || paramLower.includes('limit') || paramLower.includes('count')) {
      return COMMON_OPTIONS.common_numbers.map(String);
    }
    
    // Use enum if defined
    if (config.enum && config.enum.length > 0) {
      return config.enum;
    }
    
    return null;
  };

  const options = getOptionsForParameter();
  const hasOptions = options && options.length > 0;

  // Check if it's a variable reference
  const isExpression = typeof value === 'string' && (
    value.includes('{{') || 
    value.includes('${') ||
    value.startsWith('=')
  );

  useEffect(() => {
    if (isExpression) {
      setInputMode('expression');
    } else if (hasOptions) {
      setInputMode('select');
    } else {
      setInputMode('manual');
    }
  }, [isExpression, hasOptions]);

  const handleInsertVariable = (template: string) => {
    if (typeof value === 'string') {
      onChange(value + template);
    } else {
      onChange(template);
    }
    setShowVariables(false);
  };

  const renderModeSelector = () => (
    <div className="flex items-center gap-1 mb-2">
      <Button
        variant={inputMode === 'select' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => setInputMode('select')}
        disabled={!hasOptions}
        className="h-7 text-xs"
      >
        <ChevronDown className="h-3 w-3 mr-1" />
        Select
      </Button>
      <Button
        variant={inputMode === 'expression' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => setInputMode('expression')}
        className="h-7 text-xs"
      >
        <Code className="h-3 w-3 mr-1" />
        Expression
      </Button>
      <Button
        variant={inputMode === 'manual' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => setInputMode('manual')}
        className="h-7 text-xs"
      >
        Manual
      </Button>
    </div>
  );

  const renderSelectMode = () => {
    if (!hasOptions) return null;

    return (
      <Select
        value={value?.toString() || ""}
        onValueChange={onChange}
        disabled={disabled}
      >
        <SelectTrigger>
          <SelectValue placeholder={config.placeholder || "Select an option"} />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  };

  const renderExpressionMode = () => (
    <div className="space-y-2">
      <div className="relative">
        <Input
          value={value?.toString() || ""}
          onChange={(e) => onChange(e.target.value)}
          placeholder="{{ workflow.input }} or = expression"
          disabled={disabled}
          className="font-mono text-sm pr-20"
        />
        <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
          <Popover open={showVariables} onOpenChange={setShowVariables}>
            <PopoverTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                title="Insert variable"
              >
                <Variable className="h-3 w-3" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80 p-0" align="end">
              <Command>
                <CommandInput placeholder="Search variables..." />
                <CommandList>
                  <CommandEmpty>No variables found.</CommandEmpty>
                  
                  {['workflow', 'user', 'functions', 'env'].map((category) => {
                    const items = VARIABLE_TEMPLATES.filter(t => t.category === category);
                    if (items.length === 0) return null;
                    
                    return (
                      <CommandGroup key={category} heading={category.toUpperCase()}>
                        {items.map((template) => (
                          <CommandItem
                            key={template.value}
                            onSelect={() => handleInsertVariable(template.value)}
                          >
                            <Code className="h-3 w-3 mr-2" />
                            <div className="flex-1">
                              <div className="text-sm font-medium">{template.label}</div>
                              <div className="text-xs text-muted-foreground font-mono">
                                {template.value}
                              </div>
                            </div>
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    );
                  })}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
          
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => onChange('')}
            title="Clear"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </div>
      
      {/* Expression Helper */}
      <div className="text-xs text-muted-foreground space-y-1">
        <p className="font-medium">Expression Examples:</p>
        <ul className="space-y-0.5 pl-4">
          <li>• <code className="bg-muted px-1 rounded">{`{{ workflow.input.query }}`}</code> - Access input</li>
          <li>• <code className="bg-muted px-1 rounded">{`{{ previousBlock.output.result }}`}</code> - Previous result</li>
          <li>• <code className="bg-muted px-1 rounded">{`= $input.value * 2`}</code> - Calculate</li>
        </ul>
      </div>
    </div>
  );

  const renderManualMode = () => (
    <Input
      type={config.type === 'number' ? 'number' : 'text'}
      value={value?.toString() || ""}
      onChange={(e) => {
        const val = config.type === 'number' ? Number(e.target.value) : e.target.value;
        onChange(val);
      }}
      placeholder={config.placeholder || config.default?.toString() || ""}
      disabled={disabled}
      min={config.min}
      max={config.max}
    />
  );

  return (
    <div className="space-y-2">
      {/* Label */}
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium flex items-center gap-2">
          {name}
          {config.required && (
            <Badge variant="destructive" className="text-xs px-1.5 py-0">
              Required
            </Badge>
          )}
        </Label>
        
        {hasOptions && (
          <Badge variant="outline" className="text-xs">
            {options.length} options
          </Badge>
        )}
      </div>

      {/* Description */}
      {config.description && (
        <p className="text-xs text-muted-foreground">{config.description}</p>
      )}

      {/* Mode Selector */}
      {renderModeSelector()}

      {/* Input based on mode */}
      <div className="space-y-1">
        {inputMode === 'select' && renderSelectMode()}
        {inputMode === 'expression' && renderExpressionMode()}
        {inputMode === 'manual' && renderManualMode()}
        
        {/* Error */}
        {error && (
          <p className="text-xs text-destructive flex items-center gap-1">
            <X className="h-3 w-3" />
            {error}
          </p>
        )}
        
        {/* Current Value Display */}
        {value && (
          <div className="flex items-center gap-2 text-xs">
            <span className="text-muted-foreground">Current:</span>
            <code className="bg-muted px-2 py-0.5 rounded font-mono">
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </code>
          </div>
        )}
      </div>
    </div>
  );
}
