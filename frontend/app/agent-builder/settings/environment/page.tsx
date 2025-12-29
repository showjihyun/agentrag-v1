'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Trash2, Eye, EyeOff, Save, Copy, Database, Download, Upload, Search, AlertCircle, CheckCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

interface EnvVariable {
  id: string;
  key: string;
  value: string;
  description: string;
  isSecret: boolean;
  isNew?: boolean;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function EnvironmentVariablesPage() {
  const { toast } = useToast();
  const [variables, setVariables] = useState<EnvVariable[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [variableToDelete, setVariableToDelete] = useState<string | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadVariables();
  }, []);

  const loadVariables = async () => {
    try {
      setLoading(true);
      // Try to load from backend first
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/agent-builder/environment-variables`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setVariables(data.variables || []);
      } else {
        // Fallback to localStorage
        const saved = localStorage.getItem('environment_variables');
        if (saved) {
          setVariables(JSON.parse(saved));
        }
      }
    } catch (error) {
      // Fallback to localStorage
      const saved = localStorage.getItem('environment_variables');
      if (saved) {
        setVariables(JSON.parse(saved));
      }
    } finally {
      setLoading(false);
    }
  };

  const addVariable = () => {
    const newVar: EnvVariable = {
      id: Date.now().toString(),
      key: '',
      value: '',
      description: '',
      isSecret: false,
      isNew: true,
    };
    setVariables([...variables, newVar]);
    setHasChanges(true);
  };

  const updateVariable = (id: string, field: keyof EnvVariable, value: any) => {
    setVariables(
      variables.map((v) => (v.id === id ? { ...v, [field]: value } : v))
    );
    setHasChanges(true);
  };

  const confirmDelete = (id: string) => {
    setVariableToDelete(id);
    setDeleteDialogOpen(true);
  };

  const deleteVariable = () => {
    if (variableToDelete) {
      setVariables(variables.filter((v) => v.id !== variableToDelete));
      setHasChanges(true);
      setDeleteDialogOpen(false);
      setVariableToDelete(null);
      toast({
        title: 'Variable Deleted',
        description: 'The environment variable has been removed.',
      });
    }
  };

  const toggleSecret = (id: string) => {
    setShowSecrets({ ...showSecrets, [id]: !showSecrets[id] });
  };

  const copyValue = (value: string) => {
    navigator.clipboard.writeText(value);
    toast({
      title: 'Copied',
      description: 'Value copied to clipboard.',
    });
  };

  const copyUsage = (key: string) => {
    navigator.clipboard.writeText(`{{$env.${key}}}`);
    toast({
      title: 'Copied',
      description: 'Usage syntax copied to clipboard.',
    });
  };

  const saveVariables = async () => {
    // Validate
    const emptyKeys = variables.filter(v => !v.key.trim());
    if (emptyKeys.length > 0) {
      toast({
        title: 'Validation Error',
        description: 'All variables must have a key name.',
        variant: 'destructive',
      });
      return;
    }

    const duplicateKeys = variables.filter((v, i, arr) => 
      arr.findIndex(x => x.key === v.key) !== i
    );
    if (duplicateKeys.length > 0) {
      toast({
        title: 'Validation Error',
        description: 'Duplicate key names are not allowed.',
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);
    try {
      // Try to save to backend
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/api/agent-builder/environment-variables`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({ variables: variables.map(v => ({ ...v, isNew: undefined })) }),
      });

      if (!response.ok) {
        throw new Error('Failed to save to backend');
      }

      // Also save to localStorage as backup
      localStorage.setItem('environment_variables', JSON.stringify(variables));
      
      setVariables(variables.map(v => ({ ...v, isNew: false })));
      setHasChanges(false);
      
      toast({
        title: '✅ Saved',
        description: 'Environment variables saved successfully.',
      });
    } catch (error) {
      // Fallback to localStorage only
      localStorage.setItem('environment_variables', JSON.stringify(variables));
      setVariables(variables.map(v => ({ ...v, isNew: false })));
      setHasChanges(false);
      
      toast({
        title: '✅ Saved Locally',
        description: 'Variables saved to local storage.',
      });
    } finally {
      setSaving(false);
    }
  };

  const exportVariables = () => {
    const envContent = variables
      .map(v => `${v.key}=${v.isSecret ? '***' : v.value}${v.description ? ` # ${v.description}` : ''}`)
      .join('\n');
    
    const blob = new Blob([envContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'environment.env';
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: 'Exported',
      description: 'Environment variables exported to file.',
    });
  };

  const importVariables = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      const lines = content.split('\n').filter(line => line.trim() && !line.startsWith('#'));
      
      const imported: EnvVariable[] = lines.map((line, index) => {
        const [key, ...valueParts] = line.split('=');
        const valueWithComment = valueParts.join('=');
        const [value, ...commentParts] = valueWithComment.split('#');
        
        return {
          id: `imported-${Date.now()}-${index}`,
          key: (key || '').trim(),
          value: (value || '').trim(),
          description: commentParts.join('#').trim(),
          isSecret: false,
          isNew: true,
        };
      });

      setVariables([...variables, ...imported]);
      setHasChanges(true);
      
      toast({
        title: 'Imported',
        description: `${imported.length} variables imported.`,
      });
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const filteredVariables = variables.filter(v =>
    v.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
    v.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="container mx-auto p-6 max-w-5xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Database className="h-8 w-8" />
            Environment Variables
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage environment variables accessible across all workflows
          </p>
        </div>
        {hasChanges && (
          <Badge variant="outline" className="text-orange-600 border-orange-300">
            Unsaved Changes
          </Badge>
        )}
      </div>

      {/* Info Banner */}
      <Card className="mb-6 border-blue-200 bg-blue-50 dark:bg-blue-950/20 dark:border-blue-900">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100 mb-2">
                How to use environment variables:
              </h3>
              <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1 ml-4 list-disc">
                <li>
                  Reference in workflows: <code className="bg-blue-100 dark:bg-blue-900 px-1 rounded">{'{{$env.VARIABLE_NAME}}'}</code>
                </li>
                <li>Secret variables are encrypted at rest</li>
                <li>Changes take effect immediately for new workflow executions</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search and Actions */}
      <div className="flex items-center gap-4 mb-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search variables..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button onClick={addVariable} size="sm">
          <Plus className="w-4 h-4 mr-1" />
          Add Variable
        </Button>
        <Button onClick={saveVariables} size="sm" disabled={saving || !hasChanges}>
          <Save className="w-4 h-4 mr-1" />
          {saving ? 'Saving...' : 'Save All'}
        </Button>
      </div>

      {/* Variables List */}
      <Card>
        <div className="divide-y">
          {loading ? (
            <div className="p-4 space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="grid grid-cols-12 gap-4">
                  <Skeleton className="col-span-3 h-10" />
                  <Skeleton className="col-span-4 h-10" />
                  <Skeleton className="col-span-3 h-10" />
                  <Skeleton className="col-span-2 h-10" />
                </div>
              ))}
            </div>
          ) : filteredVariables.length === 0 ? (
            <div className="p-12 text-center">
              <Database className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">
                {searchQuery ? 'No matching variables' : 'No Environment Variables'}
              </h3>
              <p className="text-muted-foreground mb-4">
                {searchQuery 
                  ? 'Try a different search term'
                  : 'Add your first environment variable to get started'}
              </p>
              {!searchQuery && (
                <Button onClick={addVariable}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Variable
                </Button>
              )}
            </div>
          ) : (
            filteredVariables.map((variable) => (
              <div key={variable.id} className={`p-4 hover:bg-muted/50 transition-colors ${variable.isNew ? 'bg-green-50 dark:bg-green-950/20' : ''}`}>
                <div className="grid grid-cols-12 gap-4 items-start">
                  {/* Key */}
                  <div className="col-span-3">
                    <Label className="text-xs text-muted-foreground mb-1">Key</Label>
                    <Input
                      value={variable.key}
                      onChange={(e) =>
                        updateVariable(variable.id, 'key', e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '_'))
                      }
                      placeholder="VARIABLE_NAME"
                      className="font-mono text-sm"
                    />
                  </div>

                  {/* Value */}
                  <div className="col-span-4">
                    <Label className="text-xs text-muted-foreground mb-1">Value</Label>
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
                          title={showSecrets[variable.id] ? 'Hide value' : 'Show value'}
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
                        title="Copy value"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Description */}
                  <div className="col-span-3">
                    <Label className="text-xs text-muted-foreground mb-1">
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
                      <span className="text-xs text-muted-foreground">Secret</span>
                    </label>
                    <Button
                      onClick={() => confirmDelete(variable.id)}
                      size="sm"
                      variant="ghost"
                      className="px-2"
                      title="Delete variable"
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                </div>

                {/* Usage Example */}
                {variable.key && (
                  <button
                    onClick={() => copyUsage(variable.key)}
                    className="mt-2 text-xs text-muted-foreground font-mono bg-muted px-2 py-1 rounded hover:bg-muted/80 transition-colors flex items-center gap-1"
                    title="Click to copy"
                  >
                    <Copy className="w-3 h-3" />
                    {'{{$env.'}{variable.key}{'}}'}
                  </button>
                )}
              </div>
            ))
          )}
        </div>
      </Card>

      {/* Security Notice */}
      <Card className="mt-6 border-yellow-200 bg-yellow-50 dark:bg-yellow-950/20 dark:border-yellow-900">
        <CardContent className="pt-6">
          <h3 className="text-sm font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
            Security Best Practices:
          </h3>
          <ul className="text-sm text-yellow-800 dark:text-yellow-200 space-y-1 ml-4 list-disc">
            <li>Mark sensitive values (API keys, passwords) as "Secret"</li>
            <li>Never commit environment variables to version control</li>
            <li>Rotate secrets regularly</li>
            <li>Use different values for development and production</li>
          </ul>
        </CardContent>
      </Card>

      {/* Export/Import */}
      <div className="mt-6 flex gap-4">
        <Button variant="outline" onClick={exportVariables} disabled={variables.length === 0}>
          <Download className="w-4 h-4 mr-2" />
          Export Variables (.env)
        </Button>
        <label>
          <Button variant="outline" asChild>
            <span>
              <Upload className="w-4 h-4 mr-2" />
              Import from File
            </span>
          </Button>
          <input
            type="file"
            accept=".env,.txt"
            onChange={importVariables}
            className="hidden"
          />
        </label>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Variable?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this environment variable?
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={deleteVariable} className="bg-destructive text-destructive-foreground">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
