'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Settings, 
  Play, 
  Save, 
  Info,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

interface ToolParameter {
  name: string;
  type: string;
  required: boolean;
  description?: string;
  placeholder?: any;
  default?: any;
  enum?: string[];
  min?: number;
  max?: number;
}

interface ToolConfig {
  tool_id: string;
  tool_name: string;
  description: string;
  parameters: ToolParameter[];
  examples?: any[];
}

interface ToolConfigurationPanelProps {
  toolConfig: ToolConfig;
  initialValues?: Record<string, any>;
  onSave: (values: Record<string, any>) => void;
  onTest?: (values: Record<string, any>) => Promise<any>;
}

export function ToolConfigurationPanel({
  toolConfig,
  initialValues = {},
  onSave,
  onTest
}: ToolConfigurationPanelProps) {
  const [values, setValues] = useState<Record<string, any>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    // Set default values
    const defaults: Record<string, any> = {};
    toolConfig.parameters.forEach(param => {
      if (param.default !== undefined && values[param.name] === undefined) {
        defaults[param.name] = param.default;
      }
    });
    if (Object.keys(defaults).length > 0) {
      setValues(prev => ({ ...defaults, ...prev }));
    }
  }, [toolConfig]);

  const handleChange = (name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    toolConfig.parameters.forEach(param => {
      const value = values[param.name];

      // Required check
      if (param.required && (value === undefined || value === null || value === '')) {
        newErrors[param.name] = `${param.name} is required`;
      }

      // Type validation
      if (value !== undefined && value !== null && value !== '') {
        if (param.type === 'number') {
          const num = Number(value);
          if (isNaN(num)) {
            newErrors[param.name] = 'Must be a number';
          } else {
            if (param.min !== undefined && num < param.min) {
              newErrors[param.name] = `Must be at least ${param.min}`;
            }
            if (param.max !== undefined && num > param.max) {
              newErrors[param.name] = `Must be at most ${param.max}`;
            }
          }
        }

        // Enum validation
        if (param.enum && !param.enum.includes(value)) {
          newErrors[param.name] = `Must be one of: ${param.enum.join(', ')}`;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (validate()) {
      onSave(values);
    }
  };

  const handleTest = async () => {
    if (!onTest || !validate()) return;

    setTesting(true);
    setTestResult(null);

    try {
      const result = await onTest(values);
      setTestResult({ success: true, data: result });
    } catch (error: any) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setTesting(false);
    }
  };

  const renderParameter = (param: ToolParameter) => {
    const value = values[param.name];
    const error = errors[param.name];
    const isAdvanced = !param.required && param.name !== 'url' && param.name !== 'method';

    if (isAdvanced && !showAdvanced) return null;

    return (
      <div key={param.name} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={param.name} className="flex items-center gap-2">
            {param.name}
            {param.required && <span className="text-red-500">*</span>}
            {param.description && (
              <div className="relative group">
                <Info className="h-3 w-3 text-muted-foreground cursor-help" />
                <div className="absolute left-0 bottom-full mb-2 w-64 p-2 bg-black text-white text-xs rounded shadow-lg hidden group-hover:block z-10">
                  {param.description}
                </div>
              </div>
            )}
          </Label>
          {param.default !== undefined && (
            <Badge variant="outline" className="text-xs">
              default: {String(param.default)}
            </Badge>
          )}
        </div>

        {/* Render input based on type */}
        {param.enum ? (
          // Select for enum
          <select
            id={param.name}
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            className={`w-full px-3 py-2 border rounded-md ${error ? 'border-red-500' : ''}`}
          >
            <option value="">Select {param.name}</option>
            {param.enum.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        ) : param.type === 'boolean' ? (
          // Checkbox for boolean
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id={param.name}
              checked={value || false}
              onChange={(e) => handleChange(param.name, e.target.checked)}
              className="rounded"
            />
            <span className="text-sm text-muted-foreground">
              {param.description || 'Enable this option'}
            </span>
          </div>
        ) : param.type === 'number' ? (
          // Number input
          <Input
            id={param.name}
            type="number"
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            placeholder={param.placeholder ? String(param.placeholder) : undefined}
            min={param.min}
            max={param.max}
            className={error ? 'border-red-500' : ''}
          />
        ) : param.type === 'object' || param.type === 'array' ? (
          // Textarea for object/array
          <Textarea
            id={param.name}
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : value || ''}
            onChange={(e) => {
              try {
                const parsed = JSON.parse(e.target.value);
                handleChange(param.name, parsed);
              } catch {
                handleChange(param.name, e.target.value);
              }
            }}
            placeholder={param.placeholder ? JSON.stringify(param.placeholder, null, 2) : '{}'}
            rows={4}
            className={`font-mono text-sm ${error ? 'border-red-500' : ''}`}
          />
        ) : (
          // Text input for string
          <Input
            id={param.name}
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            placeholder={param.placeholder || ''}
            className={error ? 'border-red-500' : ''}
          />
        )}

        {error && (
          <p className="text-sm text-red-500 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {error}
          </p>
        )}

        {param.min !== undefined || param.max !== undefined ? (
          <p className="text-xs text-muted-foreground">
            Range: {param.min !== undefined ? `${param.min}` : '∞'} - {param.max !== undefined ? `${param.max}` : '∞'}
          </p>
        ) : null}
      </div>
    );
  };

  const requiredParams = toolConfig.parameters.filter(p => p.required);
  const optionalParams = toolConfig.parameters.filter(p => !p.required);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              {toolConfig.tool_name} Configuration
            </CardTitle>
            <CardDescription>{toolConfig.description}</CardDescription>
          </div>
          <Badge variant="secondary">{toolConfig.tool_id}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Required Parameters */}
        {requiredParams.length > 0 && (
          <div className="space-y-4">
            <h3 className="font-semibold text-sm">Required Parameters</h3>
            {requiredParams.map(renderParameter)}
          </div>
        )}

        {/* Optional Parameters */}
        {optionalParams.length > 0 && (
          <div className="space-y-4">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-sm font-semibold hover:text-primary"
            >
              {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              Advanced Options ({optionalParams.length})
            </button>
            {showAdvanced && optionalParams.map(renderParameter)}
          </div>
        )}

        {/* Examples */}
        {toolConfig.examples && toolConfig.examples.length > 0 && (
          <div className="space-y-3">
            <h3 className="font-semibold text-sm">Examples</h3>
            <div className="space-y-2">
              {toolConfig.examples.map((example, index) => (
                <div key={index} className="p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-2">{example.name || `Example ${index + 1}`}</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      const exampleValues = { ...example };
                      delete exampleValues.name;
                      delete exampleValues.result;
                      setValues(exampleValues);
                    }}
                  >
                    Load Example
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Test Result */}
        {testResult && (
          <div className={`p-4 rounded-lg ${
            testResult.success 
              ? 'bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800' 
              : 'bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800'
          }`}>
            <div className="flex items-start gap-2">
              {testResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="font-medium text-sm mb-2 text-gray-900 dark:text-gray-100">
                  {testResult.success ? 'Test Successful' : 'Test Failed'}
                </p>
                <pre className="text-xs overflow-x-auto bg-white dark:bg-gray-900 p-3 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">
                  {JSON.stringify(testResult.success ? testResult.data : testResult.error, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t">
          {onTest && (
            <Button
              variant="outline"
              onClick={handleTest}
              disabled={testing}
            >
              {testing ? (
                <>
                  <Play className="h-4 w-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Test
                </>
              )}
            </Button>
          )}
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save Configuration
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
