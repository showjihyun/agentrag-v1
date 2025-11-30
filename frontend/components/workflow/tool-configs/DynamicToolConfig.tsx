'use client';

import { useState, useEffect, useCallback } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Settings, TestTube, AlertCircle, CheckCircle, 
  Copy, Code, Lightbulb, RefreshCw 
} from 'lucide-react';
import { ToolConfigProps } from './ToolConfigRegistry';

interface ParamSchema {
  type: string;
  description: string;
  required: boolean;
  default?: any;
  enum?: string[];
  min?: number;
  max?: number;
  pattern?: string;
}

interface ToolSchema {
  tool_id: string;
  name: string;
  description: string;
  params: Record<string, ParamSchema>;
  outputs: Record<string, { type: string; description: string }>;
  examples?: {
    basic?: Record<string, any>;
    advanced?: Record<string, any>;
  };
}

interface ValidationResult {
  valid: boolean;
  errors: Record<string, string>;
  warnings: Record<string, string>;
}

interface DynamicToolConfigProps extends ToolConfigProps {
  toolId: string;
}

export default function DynamicToolConfig({ 
  toolId, 
  data, 
  onChange, 
  onTest 
}: DynamicToolConfigProps) {
  const [schema, setSchema] = useState<ToolSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<Record<string, any>>(data || {});
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validating, setValidating] = useState(false);

  // Fetch tool schema
  useEffect(() => {
    const fetchSchema = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/agent-builder/tool-config/schema/${toolId}`, {
          credentials: 'include',
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch schema: ${response.statusText}`);
        }
        
        const schemaData = await response.json();
        setSchema(schemaData);
        
        // Initialize config with defaults
        const initialConfig: Record<string, any> = { ...data };
        Object.entries(schemaData.params).forEach(([key, param]) => {
          const p = param as ParamSchema;
          if (initialConfig[key] === undefined && p.default !== undefined) {
            initialConfig[key] = p.default;
          }
        });
        setConfig(initialConfig);
        
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tool schema');
      } finally {
        setLoading(false);
      }
    };

    if (toolId) {
      fetchSchema();
    }
  }, [toolId]);

  // Update parent when config changes
  useEffect(() => {
    onChange(config);
  }, [config]);

  // Validate configuration
  const validateConfig = useCallback(async () => {
    if (!schema) return;
    
    setValidating(true);
    try {
      const response = await fetch('/api/agent-builder/tool-config/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          tool_id: toolId,
          configuration: config,
        }),
      });
      
      if (response.ok) {
        const result = await response.json();
        setValidation(result);
      }
    } catch (err) {
      console.error('Validation failed:', err);
    } finally {
      setValidating(false);
    }
  }, [toolId, config, schema]);

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
    setValidation(null); // Clear validation on change
  };

  const applyExample = (example: Record<string, any>) => {
    setConfig(prev => ({ ...prev, ...example }));
  };

  // Render field based on schema type
  const renderField = (name: string, param: ParamSchema) => {
    const value = config[name];
    const fieldError = validation?.errors?.[name];
    const fieldWarning = validation?.warnings?.[name];

    const fieldLabel = (
      <div className="flex items-center gap-2">
        <Label className={fieldError ? 'text-destructive' : ''}>
          {name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
        </Label>
        {param.required && <Badge variant="destructive" className="text-xs">Required</Badge>}
      </div>
    );

    const fieldDescription = param.description && (
      <p className="text-xs text-muted-foreground mt-1">{param.description}</p>
    );

    const fieldErrorMsg = fieldError && (
      <p className="text-xs text-destructive mt-1">{fieldError}</p>
    );

    const fieldWarningMsg = fieldWarning && (
      <p className="text-xs text-yellow-600 mt-1">{fieldWarning}</p>
    );

    switch (param.type) {
      case 'string':
        if (param.enum && param.enum.length > 0) {
          return (
            <div className="space-y-1" key={name}>
              {fieldLabel}
              <Select 
                value={value || ''} 
                onValueChange={(v) => updateConfig(name, v)}
              >
                <SelectTrigger className={fieldError ? 'border-destructive' : ''}>
                  <SelectValue placeholder={`Select ${name}`} />
                </SelectTrigger>
                <SelectContent>
                  {param.enum.map(opt => (
                    <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {fieldDescription}
              {fieldErrorMsg}
            </div>
          );
        }
        
        // Long text fields
        if (name.includes('body') || name.includes('content') || name.includes('query') || name.includes('prompt')) {
          return (
            <div className="space-y-1" key={name}>
              {fieldLabel}
              <Textarea
                placeholder={param.default || `Enter ${name}`}
                value={value || ''}
                onChange={(e) => updateConfig(name, e.target.value)}
                rows={4}
                className={`font-mono text-sm ${fieldError ? 'border-destructive' : ''}`}
              />
              {fieldDescription}
              {fieldErrorMsg}
            </div>
          );
        }
        
        // Password/secret fields
        if (name.includes('key') || name.includes('secret') || name.includes('password') || name.includes('token')) {
          return (
            <div className="space-y-1" key={name}>
              {fieldLabel}
              <Input
                type="password"
                placeholder={param.default || `Enter ${name}`}
                value={value || ''}
                onChange={(e) => updateConfig(name, e.target.value)}
                className={fieldError ? 'border-destructive' : ''}
              />
              {fieldDescription}
              {fieldErrorMsg}
            </div>
          );
        }
        
        return (
          <div className="space-y-1" key={name}>
            {fieldLabel}
            <Input
              placeholder={param.default || `Enter ${name}`}
              value={value || ''}
              onChange={(e) => updateConfig(name, e.target.value)}
              className={fieldError ? 'border-destructive' : ''}
            />
            {fieldDescription}
            {fieldErrorMsg}
          </div>
        );

      case 'number':
        if (param.min !== undefined && param.max !== undefined) {
          return (
            <div className="space-y-2" key={name}>
              {fieldLabel}
              <div className="flex items-center gap-4">
                <Slider
                  value={[value ?? param.default ?? param.min]}
                  onValueChange={([v]) => updateConfig(name, v)}
                  min={param.min}
                  max={param.max}
                  step={1}
                  className="flex-1"
                />
                <span className="text-sm font-medium w-12 text-right">
                  {value ?? param.default ?? param.min}
                </span>
              </div>
              {fieldDescription}
              {fieldErrorMsg}
            </div>
          );
        }
        
        return (
          <div className="space-y-1" key={name}>
            {fieldLabel}
            <Input
              type="number"
              min={param.min}
              max={param.max}
              placeholder={String(param.default ?? '')}
              value={value ?? ''}
              onChange={(e) => updateConfig(name, parseFloat(e.target.value) || 0)}
              className={fieldError ? 'border-destructive' : ''}
            />
            {fieldDescription}
            {fieldErrorMsg}
          </div>
        );

      case 'boolean':
        return (
          <div className="flex items-center justify-between py-2" key={name}>
            <div>
              <Label>{name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</Label>
              {fieldDescription}
            </div>
            <Switch
              checked={value ?? param.default ?? false}
              onCheckedChange={(v) => updateConfig(name, v)}
            />
          </div>
        );

      case 'array':
      case 'object':
        return (
          <div className="space-y-1" key={name}>
            {fieldLabel}
            <Textarea
              placeholder={param.type === 'array' ? '["item1", "item2"]' : '{"key": "value"}'}
              value={typeof value === 'string' ? value : JSON.stringify(value || (param.type === 'array' ? [] : {}), null, 2)}
              onChange={(e) => {
                try {
                  updateConfig(name, JSON.parse(e.target.value));
                } catch {
                  updateConfig(name, e.target.value);
                }
              }}
              rows={4}
              className={`font-mono text-sm ${fieldError ? 'border-destructive' : ''}`}
            />
            {fieldDescription}
            {fieldErrorMsg}
          </div>
        );

      default:
        return (
          <div className="space-y-1" key={name}>
            {fieldLabel}
            <Input
              placeholder={`Enter ${name}`}
              value={value || ''}
              onChange={(e) => updateConfig(name, e.target.value)}
            />
            {fieldDescription}
          </div>
        );
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (!schema) {
    return (
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>No schema available for this tool</AlertDescription>
      </Alert>
    );
  }

  // Group params: required first, then optional
  const requiredParams = Object.entries(schema.params).filter(([_, p]) => p.required);
  const optionalParams = Object.entries(schema.params).filter(([_, p]) => !p.required);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 pb-4 border-b">
        <div className="p-2 rounded-lg bg-gray-100 dark:bg-gray-800">
          <Settings className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </div>
        <div>
          <h3 className="font-semibold">{schema.name}</h3>
          <p className="text-sm text-muted-foreground">{schema.description}</p>
        </div>
        <Badge variant="outline" className="ml-auto">Dynamic</Badge>
      </div>

      <Tabs defaultValue="config" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="examples">Examples</TabsTrigger>
          <TabsTrigger value="outputs">Outputs</TabsTrigger>
        </TabsList>

        {/* Configuration Tab */}
        <TabsContent value="config" className="space-y-4">
          {/* Required Fields */}
          {requiredParams.length > 0 && (
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-muted-foreground">Required</h4>
              {requiredParams.map(([name, param]) => renderField(name, param))}
            </div>
          )}

          {/* Optional Fields */}
          {optionalParams.length > 0 && (
            <div className="space-y-4 pt-4 border-t">
              <h4 className="text-sm font-medium text-muted-foreground">Optional</h4>
              {optionalParams.map(([name, param]) => renderField(name, param))}
            </div>
          )}

          {/* Validation Status */}
          {validation && (
            <Alert variant={validation.valid ? 'default' : 'destructive'}>
              {validation.valid ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>
                {validation.valid 
                  ? 'Configuration is valid' 
                  : `${Object.keys(validation.errors).length} error(s) found`}
              </AlertDescription>
            </Alert>
          )}

          {/* Validate Button */}
          <Button 
            onClick={validateConfig} 
            variant="outline" 
            className="w-full"
            disabled={validating}
          >
            {validating ? (
              <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <CheckCircle className="h-4 w-4 mr-2" />
            )}
            Validate Configuration
          </Button>
        </TabsContent>

        {/* Examples Tab */}
        <TabsContent value="examples" className="space-y-4">
          {schema.examples?.basic && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Basic Example</h4>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={() => applyExample(schema.examples!.basic!)}
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Apply
                </Button>
              </div>
              <pre className="p-3 bg-muted rounded-lg text-xs overflow-auto">
                {JSON.stringify(schema.examples.basic, null, 2)}
              </pre>
            </div>
          )}

          {schema.examples?.advanced && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-medium">Advanced Example</h4>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={() => applyExample(schema.examples!.advanced!)}
                >
                  <Copy className="h-3 w-3 mr-1" />
                  Apply
                </Button>
              </div>
              <pre className="p-3 bg-muted rounded-lg text-xs overflow-auto">
                {JSON.stringify(schema.examples.advanced, null, 2)}
              </pre>
            </div>
          )}

          <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
            <Lightbulb className="h-4 w-4 text-blue-600 mt-0.5" />
            <p className="text-xs text-blue-700 dark:text-blue-300">
              Click "Apply" to use an example as your starting configuration
            </p>
          </div>
        </TabsContent>

        {/* Outputs Tab */}
        <TabsContent value="outputs" className="space-y-4">
          <p className="text-sm text-muted-foreground">
            This tool produces the following outputs:
          </p>
          
          {Object.entries(schema.outputs).map(([name, output]) => (
            <div key={name} className="p-3 bg-muted/50 rounded-lg">
              <div className="flex items-center gap-2">
                <Code className="h-4 w-4 text-muted-foreground" />
                <span className="font-mono text-sm">{name}</span>
                <Badge variant="outline" className="text-xs">{output.type}</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{output.description}</p>
            </div>
          ))}

          <div className="p-3 bg-muted/50 rounded-lg">
            <p className="text-xs text-muted-foreground">
              Access outputs in subsequent nodes using: <code className="px-1 py-0.5 bg-muted rounded">{'{{node_id.output_name}}'}</code>
            </p>
          </div>
        </TabsContent>
      </Tabs>

      {/* Test Button */}
      {onTest && (
        <Button 
          onClick={onTest} 
          variant="outline" 
          className="w-full"
        >
          <TestTube className="h-4 w-4 mr-2" />
          Test Tool
        </Button>
      )}
    </div>
  );
}
