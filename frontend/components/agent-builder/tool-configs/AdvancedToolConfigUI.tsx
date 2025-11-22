"use client";

/**
 * Advanced Tool Config UI
 * 
 * 50+ Tools의 상세한 Config를 위한 고급 UI
 * - Tool별 맞춤형 Select Box
 * - 실시간 유효성 검사
 * - 예제 템플릿
 * - 도움말 및 문서 링크
 */

import React, { useState } from 'react';
import { 
  getToolConfig, 
  type ToolParamSchema 
} from './ToolConfigRegistry';
import { AIAgentConfig } from './AIAgentConfig';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { 
  Tabs, 
  TabsContent, 
  TabsList, 
  TabsTrigger 
} from '@/components/ui/tabs';
import { 
  AlertCircle, 
  CheckCircle2, 
  ExternalLink, 
  Copy, 
  Sparkles 
} from 'lucide-react';

interface AdvancedToolConfigUIProps {
  toolId: string;
  initialConfig?: Record<string, any>;
  initialCredentials?: Record<string, any>;
  onSave: (config: Record<string, any>, credentials: Record<string, any>) => void;
  onCancel: () => void;
}

export function AdvancedToolConfigUI({
  toolId,
  initialConfig = {},
  initialCredentials = {},
  onSave,
  onCancel,
}: AdvancedToolConfigUIProps) {
  const toolSchema = getToolConfig(toolId);
  const [config, setConfig] = useState<Record<string, any>>(initialConfig);
  const [credentials, setCredentials] = useState<Record<string, any>>(initialCredentials);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState('config');

  // Use specialized AI Agent configuration component
  if (toolId === 'ai_agent') {
    return (
      <AIAgentConfig
        initialConfig={initialConfig}
        initialCredentials={initialCredentials}
        onSave={onSave}
        onCancel={onCancel}
      />
    );
  }

  if (!toolSchema) {
    return (
      <div className="p-4 text-center text-red-500">
        Tool configuration not found for: {toolId}
      </div>
    );
  }

  const handleConfigChange = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
    // Clear error for this field
    if (errors[key]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[key];
        return newErrors;
      });
    }
  };

  const handleCredentialChange = (key: string, value: any) => {
    setCredentials(prev => ({ ...prev, [key]: value }));
  };

  const validateConfig = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Validate required parameters
    Object.entries(toolSchema.params).forEach(([key, schema]) => {
      if (schema.required && !config[key]) {
        newErrors[key] = `${schema.description} is required`;
      }
    });

    // Validate required credentials
    if (toolSchema.credentials) {
      Object.entries(toolSchema.credentials).forEach(([key, schema]) => {
        if (schema.required && !credentials[key]) {
          newErrors[`cred_${key}`] = `${schema.description} is required`;
        }
      });
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validateConfig()) {
      onSave(config, credentials);
    }
  };

  const loadExample = (example: any) => {
    setConfig(example.config);
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-2xl">{toolSchema.icon}</span>
            <h2 className="text-2xl font-bold">{toolSchema.name}</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            {toolSchema.description}
          </p>
          {toolSchema.docs_link && (
            <a
              href={toolSchema.docs_link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
            >
              <ExternalLink className="w-3 h-3" />
              Documentation
            </a>
          )}
        </div>
        <div 
          className="w-12 h-12 rounded-lg flex items-center justify-center text-2xl"
          style={{ backgroundColor: toolSchema.bg_color || '#gray' }}
        >
          {toolSchema.icon}
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="credentials">
            Credentials
            {toolSchema.credentials && (
              <span className="ml-1 text-xs">
                ({Object.keys(toolSchema.credentials).length})
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="examples">
            Examples
            {toolSchema.examples && (
              <span className="ml-1 text-xs">
                ({toolSchema.examples.length})
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Parameters</CardTitle>
              <CardDescription>
                Configure the tool parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(toolSchema.params).map(([key, schema]) => (
                <ParameterInput
                  key={key}
                  paramKey={key}
                  schema={schema}
                  value={config[key]}
                  onChange={(value) => handleConfigChange(key, value)}
                  error={errors[key]}
                />
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Credentials Tab */}
        <TabsContent value="credentials" className="space-y-4">
          {toolSchema.credentials ? (
            <Card>
              <CardHeader>
                <CardTitle>Credentials</CardTitle>
                <CardDescription>
                  Secure authentication credentials
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(toolSchema.credentials).map(([key, schema]) => (
                  <ParameterInput
                    key={key}
                    paramKey={key}
                    schema={schema}
                    value={credentials[key]}
                    onChange={(value) => handleCredentialChange(key, value)}
                    error={errors[`cred_${key}`]}
                  />
                ))}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No credentials required for this tool
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Examples Tab */}
        <TabsContent value="examples" className="space-y-4">
          {toolSchema.examples && toolSchema.examples.length > 0 ? (
            <div className="grid gap-4">
              {toolSchema.examples.map((example, index) => (
                <Card key={index} className="hover:border-primary transition-colors">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-lg flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-yellow-500" />
                          {example.name}
                        </CardTitle>
                        <CardDescription>{example.description}</CardDescription>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => loadExample(example)}
                      >
                        <Copy className="w-3 h-3 mr-1" />
                        Use
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-xs bg-muted p-3 rounded-md overflow-x-auto">
                      {JSON.stringify(example.config, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No examples available for this tool
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <div className="flex items-center gap-2 text-sm">
          {Object.keys(errors).length > 0 ? (
            <>
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-red-500">
                {Object.keys(errors).length} validation error(s)
              </span>
            </>
          ) : (
            <>
              <CheckCircle2 className="w-4 h-4 text-green-500" />
              <span className="text-green-500">Configuration valid</span>
            </>
          )}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button onClick={handleSave}>
            Save Configuration
          </Button>
        </div>
      </div>
    </div>
  );
}

// Parameter Input Component
function ParameterInput({
  paramKey,
  schema,
  value,
  onChange,
  error,
}: {
  paramKey: string;
  schema: ToolParamSchema;
  value: any;
  onChange: (value: any) => void;
  error?: string;
}) {
  const renderInput = () => {
    switch (schema.type) {
      case 'select':
        return (
          <Select
            value={value || schema.default}
            onValueChange={onChange}
          >
            <SelectTrigger>
              <SelectValue placeholder={schema.placeholder || 'Select...'} />
            </SelectTrigger>
            <SelectContent>
              {schema.enum?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'textarea':
      case 'code':
        return (
          <Textarea
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={schema.placeholder}
            rows={schema.type === 'code' ? 8 : 4}
            className={schema.type === 'code' ? 'font-mono text-sm' : ''}
          />
        );

      case 'boolean':
        return (
          <div className="flex items-center space-x-2">
            <Switch
              checked={value || schema.default || false}
              onCheckedChange={onChange}
            />
            <span className="text-sm text-muted-foreground">
              {value ? 'Enabled' : 'Disabled'}
            </span>
          </div>
        );

      case 'number':
        return (
          <Input
            type="number"
            value={value || schema.default || ''}
            onChange={(e) => onChange(Number(e.target.value))}
            placeholder={schema.placeholder}
            min={schema.min}
            max={schema.max}
          />
        );

      case 'password':
        return (
          <Input
            type="password"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={schema.placeholder}
          />
        );

      case 'json':
        return (
          <Textarea
            value={typeof value === 'string' ? value : JSON.stringify(value || schema.default || {}, null, 2)}
            onChange={(e) => {
              try {
                onChange(JSON.parse(e.target.value));
              } catch {
                onChange(e.target.value);
              }
            }}
            placeholder={schema.placeholder}
            rows={6}
            className="font-mono text-sm"
          />
        );

      case 'array':
        return (
          <Input
            value={Array.isArray(value) ? value.join(', ') : value || ''}
            onChange={(e) => onChange(e.target.value.split(',').map(s => s.trim()))}
            placeholder={schema.placeholder}
          />
        );

      default:
        return (
          <Input
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            placeholder={schema.placeholder}
            pattern={schema.pattern}
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      <Label htmlFor={paramKey} className="flex items-center gap-2">
        {schema.description}
        {schema.required && <span className="text-red-500">*</span>}
      </Label>
      {renderInput()}
      {schema.helpText && (
        <p className="text-xs text-muted-foreground">{schema.helpText}</p>
      )}
      {error && (
        <p className="text-xs text-red-500 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}
    </div>
  );
}
