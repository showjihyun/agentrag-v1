'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { 
  Code, 
  Play, 
  Save, 
  Plus, 
  Trash2, 
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';

interface ToolParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'object' | 'array';
  required: boolean;
  description: string;
  default?: any;
}

interface CustomTool {
  id?: string;
  name: string;
  description: string;
  category: string;
  code: string;
  language: 'python' | 'javascript';
  parameters: ToolParameter[];
  version?: string;
}

interface CustomToolBuilderProps {
  onSave: (tool: CustomTool) => Promise<void>;
  existingTool?: CustomTool;
}

export function CustomToolBuilder({ onSave, existingTool }: CustomToolBuilderProps) {
  const [tool, setTool] = useState<CustomTool>(existingTool || {
    name: '',
    description: '',
    category: 'custom',
    code: `def execute(params, context):
    """
    Custom tool implementation.
    
    Args:
        params: Tool parameters
        context: Execution context (env, workflow, etc.)
    
    Returns:
        dict: Tool execution result
    """
    # Your code here
    result = params.get('input', '')
    
    return {
        'success': True,
        'output': result
    }`,
    language: 'python',
    parameters: []
  });

  const [testParams, setTestParams] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddParameter = () => {
    setTool({
      ...tool,
      parameters: [
        ...tool.parameters,
        {
          name: '',
          type: 'string',
          required: true,
          description: ''
        }
      ]
    });
  };

  const handleUpdateParameter = (index: number, field: keyof ToolParameter, value: any) => {
    const newParams = [...tool.parameters];
    newParams[index] = { ...newParams[index], [field]: value };
    setTool({ ...tool, parameters: newParams });
  };

  const handleRemoveParameter = (index: number) => {
    setTool({
      ...tool,
      parameters: tool.parameters.filter((_, i) => i !== index)
    });
  };

  const handleTest = async () => {
    setTesting(true);
    setError(null);
    
    try {
      // Mock test execution
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setTestResult({
        success: true,
        output: 'Test execution successful!',
        execution_time_ms: 145,
        timestamp: new Date().toISOString()
      });
    } catch (err: any) {
      setError(err.message);
      setTestResult({
        success: false,
        error: err.message
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    
    try {
      await onSave(tool);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const codeTemplates = {
    python: `def execute(params, context):
    """Custom tool implementation."""
    # Your code here
    return {'success': True, 'output': 'result'}`,
    javascript: `async function execute(params, context) {
    // Your code here
    return { success: true, output: 'result' };
}`
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Custom Tool Builder</h2>
        <p className="text-muted-foreground">
          Create your own custom tools with Python or JavaScript
        </p>
      </div>

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="name">Tool Name</Label>
            <Input
              id="name"
              value={tool.name}
              onChange={(e) => setTool({ ...tool, name: e.target.value })}
              placeholder="e.g., Weather API"
            />
          </div>

          <div>
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={tool.description}
              onChange={(e) => setTool({ ...tool, description: e.target.value })}
              placeholder="Describe what this tool does..."
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="category">Category</Label>
            <select
              id="category"
              value={tool.category}
              onChange={(e) => setTool({ ...tool, category: e.target.value })}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="custom">Custom</option>
              <option value="api">API</option>
              <option value="data">Data Processing</option>
              <option value="utility">Utility</option>
              <option value="ai">AI/ML</option>
            </select>
          </div>

          <div>
            <Label htmlFor="language">Language</Label>
            <div className="flex gap-2">
              <Button
                variant={tool.language === 'python' ? 'default' : 'outline'}
                onClick={() => setTool({ ...tool, language: 'python', code: codeTemplates.python })}
              >
                Python
              </Button>
              <Button
                variant={tool.language === 'javascript' ? 'default' : 'outline'}
                onClick={() => setTool({ ...tool, language: 'javascript', code: codeTemplates.javascript })}
              >
                JavaScript
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Code Editor */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Code className="h-5 w-5" />
            Code Implementation
          </CardTitle>
          <CardDescription>
            Write your tool logic in {tool.language}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            value={tool.code}
            onChange={(e) => setTool({ ...tool, code: e.target.value })}
            className="font-mono text-sm min-h-[300px]"
            placeholder="Enter your code here..."
          />
          <p className="text-xs text-muted-foreground mt-2">
            Tip: Use <code>params</code> to access input parameters and <code>context</code> for environment variables
          </p>
        </CardContent>
      </Card>

      {/* Parameters */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Parameters</CardTitle>
              <CardDescription>
                Define input parameters for your tool
              </CardDescription>
            </div>
            <Button onClick={handleAddParameter} size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Add Parameter
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {tool.parameters.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              No parameters defined. Click "Add Parameter" to get started.
            </p>
          ) : (
            <div className="space-y-4">
              {tool.parameters.map((param, index) => (
                <div key={index} className="p-4 border rounded-lg space-y-3">
                  <div className="flex items-center justify-between">
                    <Badge variant="outline">Parameter {index + 1}</Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveParameter(index)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={param.name}
                        onChange={(e) => handleUpdateParameter(index, 'name', e.target.value)}
                        placeholder="parameter_name"
                      />
                    </div>

                    <div>
                      <Label>Type</Label>
                      <select
                        value={param.type}
                        onChange={(e) => handleUpdateParameter(index, 'type', e.target.value)}
                        className="w-full px-3 py-2 border rounded-md"
                      >
                        <option value="string">String</option>
                        <option value="number">Number</option>
                        <option value="boolean">Boolean</option>
                        <option value="object">Object</option>
                        <option value="array">Array</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <Label>Description</Label>
                    <Input
                      value={param.description}
                      onChange={(e) => handleUpdateParameter(index, 'description', e.target.value)}
                      placeholder="Describe this parameter..."
                    />
                  </div>

                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={param.required}
                      onChange={(e) => handleUpdateParameter(index, 'required', e.target.checked)}
                      className="rounded"
                    />
                    <Label>Required</Label>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Test Execution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-5 w-5" />
            Test Execution
          </CardTitle>
          <CardDescription>
            Test your tool with sample parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {tool.parameters.map((param) => (
            <div key={param.name}>
              <Label>{param.name} {param.required && <span className="text-red-500">*</span>}</Label>
              <Input
                value={testParams[param.name] || ''}
                onChange={(e) => setTestParams({ ...testParams, [param.name]: e.target.value })}
                placeholder={`Enter ${param.type} value...`}
              />
            </div>
          ))}

          <Button onClick={handleTest} disabled={testing} className="w-full">
            {testing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Testing...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Run Test
              </>
            )}
          </Button>

          {testResult && (
            <div className={`p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
              <div className="flex items-start gap-2">
                {testResult.success ? (
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                )}
                <div className="flex-1">
                  <p className="font-medium text-sm">
                    {testResult.success ? 'Test Passed' : 'Test Failed'}
                  </p>
                  <pre className="text-xs mt-2 overflow-x-auto">
                    {JSON.stringify(testResult, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <p className="font-medium text-sm text-red-900">Error</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <Button variant="outline">Cancel</Button>
        <Button onClick={handleSave} disabled={saving || !tool.name || !tool.code}>
          {saving ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="h-4 w-4 mr-2" />
              Save Tool
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
