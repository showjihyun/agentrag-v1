'use client';

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Trash2, Eye, EyeOff, Save, Copy } from 'lucide-react';

interface EnvVariable {
  id: string;
  key: string;
  value: string;
  description: string;
  isSecret: boolean;
}

export default function EnvironmentVariablesPage() {
  const [variables, setVariables] = useState<EnvVariable[]>([
    {
      id: '1',
      key: 'API_BASE_URL',
      value: 'https://api.example.com',
      description: 'Base URL for external API',
      isSecret: false,
    },
    {
      id: '2',
      key: 'DATABASE_URL',
      value: 'postgresql://user:pass@localhost:5432/db',
      description: 'Database connection string',
      isSecret: true,
    },
  ]);

  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [editingId, setEditingId] = useState<string | null>(null);

  const addVariable = () => {
    const newVar: EnvVariable = {
      id: Date.now().toString(),
      key: '',
      value: '',
      description: '',
      isSecret: false,
    };
    setVariables([...variables, newVar]);
    setEditingId(newVar.id);
  };

  const updateVariable = (id: string, field: keyof EnvVariable, value: any) => {
    setVariables(
      variables.map((v) => (v.id === id ? { ...v, [field]: value } : v))
    );
  };

  const deleteVariable = (id: string) => {
    if (confirm('Are you sure you want to delete this variable?')) {
      setVariables(variables.filter((v) => v.id !== id));
    }
  };

  const toggleSecret = (id: string) => {
    setShowSecrets({ ...showSecrets, [id]: !showSecrets[id] });
  };

  const copyValue = (value: string) => {
    navigator.clipboard.writeText(value);
  };

  const saveVariables = () => {
    // TODO: Save to backend
    alert('Environment variables saved!');
    setEditingId(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Environment Variables
          </h1>
          <p className="text-gray-600">
            Manage environment variables accessible across all workflows
          </p>
        </div>

        {/* Info Banner */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">
            How to use environment variables:
          </h3>
          <ul className="text-sm text-blue-800 space-y-1 ml-4 list-disc">
            <li>
              Reference in workflows: <code className="bg-blue-100 px-1 rounded">{'{{$env.VARIABLE_NAME}}'}</code>
            </li>
            <li>Secret variables are encrypted at rest</li>
            <li>Changes take effect immediately for new workflow executions</li>
            <li>Use for API keys, URLs, and configuration values</li>
          </ul>
        </div>

        {/* Variables List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Variables</h2>
            <div className="flex gap-2">
              <Button onClick={addVariable} size="sm">
                <Plus className="w-4 h-4 mr-1" />
                Add Variable
              </Button>
              <Button onClick={saveVariables} size="sm" variant="default">
                <Save className="w-4 h-4 mr-1" />
                Save All
              </Button>
            </div>
          </div>

          <div className="divide-y">
            {variables.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                No environment variables defined. Click "Add Variable" to create one.
              </div>
            ) : (
              variables.map((variable) => (
                <div key={variable.id} className="p-4 hover:bg-gray-50">
                  <div className="grid grid-cols-12 gap-4 items-start">
                    {/* Key */}
                    <div className="col-span-3">
                      <Label className="text-xs text-gray-600 mb-1">Key</Label>
                      <Input
                        value={variable.key}
                        onChange={(e) =>
                          updateVariable(variable.id, 'key', e.target.value)
                        }
                        placeholder="VARIABLE_NAME"
                        className="font-mono text-sm"
                      />
                    </div>

                    {/* Value */}
                    <div className="col-span-4">
                      <Label className="text-xs text-gray-600 mb-1">Value</Label>
                      <div className="flex gap-1">
                        <Input
                          type={
                            variable.isSecret && !showSecrets[variable.id]
                              ? 'password'
                              : 'text'
                          }
                          value={variable.value}
                          onChange={(e) =>
                            updateVariable(variable.id, 'value', e.target.value)
                          }
                          placeholder="value"
                          className="font-mono text-sm flex-1"
                        />
                        {variable.isSecret && (
                          <Button
                            onClick={() => toggleSecret(variable.id)}
                            size="sm"
                            variant="ghost"
                            className="px-2"
                          >
                            {showSecrets[variable.id] ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </Button>
                        )}
                        <Button
                          onClick={() => copyValue(variable.value)}
                          size="sm"
                          variant="ghost"
                          className="px-2"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Description */}
                    <div className="col-span-3">
                      <Label className="text-xs text-gray-600 mb-1">
                        Description
                      </Label>
                      <Input
                        value={variable.description}
                        onChange={(e) =>
                          updateVariable(
                            variable.id,
                            'description',
                            e.target.value
                          )
                        }
                        placeholder="Optional description"
                        className="text-sm"
                      />
                    </div>

                    {/* Secret Toggle & Delete */}
                    <div className="col-span-2 flex items-end gap-2">
                      <label className="flex items-center gap-1 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={variable.isSecret}
                          onChange={(e) =>
                            updateVariable(
                              variable.id,
                              'isSecret',
                              e.target.checked
                            )
                          }
                          className="rounded"
                        />
                        <span className="text-xs text-gray-600">Secret</span>
                      </label>
                      <Button
                        onClick={() => deleteVariable(variable.id)}
                        size="sm"
                        variant="ghost"
                        className="px-2"
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>

                  {/* Usage Example */}
                  {variable.key && (
                    <div className="mt-2 text-xs text-gray-500 font-mono bg-gray-50 px-2 py-1 rounded">
                      Usage: {'{{$env.'}{variable.key}{'}}'}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Security Notice */}
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-yellow-900 mb-2">
            Security Best Practices:
          </h3>
          <ul className="text-sm text-yellow-800 space-y-1 ml-4 list-disc">
            <li>Mark sensitive values (API keys, passwords) as "Secret"</li>
            <li>Never commit environment variables to version control</li>
            <li>Rotate secrets regularly</li>
            <li>Use different values for development and production</li>
            <li>Limit access to environment variables to authorized users only</li>
          </ul>
        </div>

        {/* Export/Import */}
        <div className="mt-6 flex gap-4">
          <Button variant="outline">
            Export Variables (.env)
          </Button>
          <Button variant="outline">
            Import from File
          </Button>
        </div>
      </div>
    </div>
  );
}
