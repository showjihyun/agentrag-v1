'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  X, 
  Play, 
  Save, 
  Info,
  AlertCircle,
  CheckCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface NodeData {
  id: string;
  type: string;
  label: string;
  tool_id?: string;
  config?: Record<string, any>;
}

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

interface NodeConfigurationPanelProps {
  node: NodeData;
  onClose: () => void;
  onSave: (config: Record<string, any>) => void;
  onTest?: (config: Record<string, any>) => Promise<any>;
}

export function NodeConfigurationPanel({
  node,
  onClose,
  onSave,
  onTest
}: NodeConfigurationPanelProps) {
  console.log('🎨 NodeConfigurationPanel rendered with node:', node);
  
  const [toolConfig, setToolConfig] = useState<any>(null);
  const [values, setValues] = useState<Record<string, any>>(node.config || {});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    console.log('🔄 useEffect triggered, fetching tool config...');
    fetchToolConfig();
  }, [node.tool_id]);

  const fetchToolConfig = async () => {
    console.log('🔍 NodeConfigurationPanel - Node data:', node);
    console.log('🔍 Tool ID:', node.tool_id);
    
    if (!node.tool_id) {
      console.warn('⚠️ No tool_id found in node data');
      setLoading(false);
      return;
    }

    try {
      console.log('📡 Fetching tool config for:', node.tool_id);
      const response = await fetch(`/api/agent-builder/marketplace/${node.tool_id}`);
      
      if (!response.ok) {
        console.error('❌ API response not OK:', response.status, response.statusText);
        throw new Error('Failed to fetch tool config');
      }
      
      const data = await response.json();
      console.log('✅ Tool config loaded:', data);
      setToolConfig(data);

      // Set default values only if not already set
      setValues(prev => {
        const defaults: Record<string, any> = {};
        data.parameters?.forEach((param: ToolParameter) => {
          if (param.default !== undefined && prev[param.name] === undefined) {
            defaults[param.name] = param.default;
          }
        });
        console.log('📝 Setting default values:', defaults);
        return Object.keys(defaults).length > 0 ? { ...defaults, ...prev } : prev;
      });
    } catch (error) {
      console.error('❌ Failed to load tool config:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validate = (): boolean => {
    if (!toolConfig?.parameters) return true;

    const newErrors: Record<string, string> = {};

    toolConfig.parameters.forEach((param: ToolParameter) => {
      const value = values[param.name];

      if (param.required && (value === undefined || value === null || value === '')) {
        newErrors[param.name] = `${param.name} is required`;
      }

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
    const isAdvanced = !param.required;

    if (isAdvanced && !showAdvanced) return null;

    return (
      <div key={param.name} className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor={param.name} className="text-sm flex items-center gap-1 text-gray-200">
            {param.name}
            {param.required && <span className="text-red-400">*</span>}
          </Label>
          {param.default !== undefined && (
            <Badge variant="outline" className="text-xs text-gray-400 border-gray-600">
              {String(param.default)}
            </Badge>
          )}
        </div>

        {param.description && (
          <p className="text-xs text-gray-400">{param.description}</p>
        )}

        {param.type === 'select' && (param as any).options ? (
          <select
            id={param.name}
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            className={`w-full px-2 py-1.5 text-sm border rounded bg-gray-800 text-gray-100 border-gray-600 ${error ? 'border-red-500' : ''}`}
          >
            <option value="">Select...</option>
            {(param as any).options.map((option: any) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : param.type === 'chat' ? (
          <div className="border border-gray-600 rounded-lg p-3 bg-gray-800/50">
            <Textarea
              id={param.name}
              value={value || ''}
              onChange={(e) => handleChange(param.name, e.target.value)}
              placeholder="Enter your message for the AI agent..."
              rows={4}
              className="text-sm bg-gray-900 text-gray-100 border-gray-600"
            />
            <p className="text-xs text-gray-500 mt-2">
              💡 This will be sent to the AI agent for processing
            </p>
          </div>
        ) : param.enum ? (
          <select
            id={param.name}
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            className={`w-full px-2 py-1.5 text-sm border rounded bg-gray-800 text-gray-100 border-gray-600 ${error ? 'border-red-500' : ''}`}
          >
            <option value="">Select...</option>
            {param.enum.map(option => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        ) : param.type === 'boolean' ? (
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id={param.name}
              checked={value || false}
              onChange={(e) => handleChange(param.name, e.target.checked)}
              className="rounded"
            />
            <span className="text-xs text-muted-foreground">Enable</span>
          </div>
        ) : param.type === 'number' ? (
          <Input
            id={param.name}
            type="number"
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            placeholder={param.placeholder ? String(param.placeholder) : undefined}
            min={param.min}
            max={param.max}
            className={`text-sm bg-gray-800 text-gray-100 border-gray-600 ${error ? 'border-red-500' : ''}`}
          />
        ) : param.type === 'object' || param.type === 'array' ? (
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
            rows={3}
            className={`font-mono text-xs bg-gray-800 text-gray-100 border-gray-600 ${error ? 'border-red-500' : ''}`}
          />
        ) : (
          <Input
            id={param.name}
            type="text"
            value={value || ''}
            onChange={(e) => handleChange(param.name, e.target.value)}
            placeholder={param.placeholder || ''}
            className={`text-sm bg-gray-800 text-gray-100 border-gray-600 ${error ? 'border-red-500' : ''}`}
          />
        )}

        {error && (
          <p className="text-xs text-red-500 flex items-center gap-1">
            <AlertCircle className="h-3 w-3" />
            {error}
          </p>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="w-96 h-full bg-gray-900 border-l border-gray-700 flex items-center justify-center">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
      </div>
    );
  }

  // If no tool config, show basic node configuration
  if (!toolConfig && !node.tool_id) {
    return (
      <div className="w-96 h-full bg-gray-900 border-l border-gray-700 flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
          <div>
            <h3 className="font-semibold">{node.label}</h3>
            <p className="text-xs text-muted-foreground">Basic Node Configuration</p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="block-name" className="text-sm">Block Name</Label>
            <Input
              id="block-name"
              value={node.label}
              className="text-sm"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description" className="text-sm">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe what this block does..."
              rows={2}
              className="text-sm"
            />
          </div>
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
            <p className="text-sm text-yellow-800">
              ⚠️ No tool configuration available for this node type.
            </p>
            <p className="text-xs text-yellow-700 mt-1">
              Tool ID: {node.tool_id || 'Not specified'}
            </p>
          </div>
        </div>
        <div className="p-4 border-t">
          <Button onClick={handleSave} className="w-full" size="sm">
            <Save className="h-3 w-3 mr-2" />
            Apply Changes
          </Button>
        </div>
      </div>
    );
  }

  const requiredParams = toolConfig?.parameters?.filter((p: ToolParameter) => p.required) || [];
  const optionalParams = toolConfig?.parameters?.filter((p: ToolParameter) => !p.required) || [];

  return (
    <div className="w-96 h-full bg-gray-900 border-l border-gray-700 flex flex-col text-gray-100">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-white">{node.label}</h3>
          <p className="text-xs text-gray-400">{toolConfig?.description || 'Node Configuration'}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose} className="text-gray-400 hover:text-white">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900">
        {/* Block Name */}
        <div className="space-y-2">
          <Label htmlFor="block-name" className="text-sm text-gray-200">Block Name</Label>
          <Input
            id="block-name"
            value={node.label}
            onChange={(e) => {
              // Update node label
            }}
            className="text-sm bg-gray-800 text-gray-100 border-gray-600"
          />
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description" className="text-sm text-gray-200">Description</Label>
          <Textarea
            id="description"
            placeholder="Describe what this block does..."
            rows={2}
            className="text-sm bg-gray-800 text-gray-100 border-gray-600"
          />
        </div>

        {/* Tool Parameters */}
        {toolConfig && (
          <>
            {requiredParams.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-gray-200">Required Parameters</h4>
                {requiredParams.map(renderParameter)}
              </div>
            )}

            {optionalParams.length > 0 && (
              <div className="space-y-3">
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-200 hover:text-primary w-full"
                >
                  {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  Advanced Options ({optionalParams.length})
                </button>
                {showAdvanced && optionalParams.map(renderParameter)}
              </div>
            )}
          </>
        )}

        {/* Test Result */}
        {testResult && (
          <div className={`p-3 rounded text-sm ${
            testResult.success 
              ? 'bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800' 
              : 'bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800'
          }`}>
            <div className="flex items-start gap-2">
              {testResult.success ? (
                <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400 mt-0.5" />
              ) : (
                <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 mt-0.5" />
              )}
              <div className="flex-1">
                <p className="font-medium text-xs mb-1 text-gray-900 dark:text-gray-100">
                  {testResult.success ? 'Test Successful' : 'Test Failed'}
                </p>
                <pre className="text-xs overflow-x-auto bg-white dark:bg-gray-900 p-2 rounded border border-gray-200 dark:border-gray-700 text-gray-900 dark:text-gray-100">
                  {JSON.stringify(testResult.success ? testResult.data : testResult.error, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-700 space-y-2 bg-gray-900">
        {onTest && (
          <Button
            variant="outline"
            onClick={handleTest}
            disabled={testing}
            className="w-full"
            size="sm"
          >
            {testing ? (
              <>
                <Play className="h-3 w-3 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Play className="h-3 w-3 mr-2" />
                Test
              </>
            )}
          </Button>
        )}
        <Button onClick={handleSave} className="w-full" size="sm">
          <Save className="h-3 w-3 mr-2" />
          Apply Changes
        </Button>
      </div>
    </div>
  );
}
