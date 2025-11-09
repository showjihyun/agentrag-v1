/**
 * Condition Node Configuration Panel
 * Advanced settings for condition nodes
 */

import React, { useState } from 'react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, Plus, X } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ConditionNodeConfigProps {
  data: any;
  onChange: (data: any) => void;
}

export function ConditionNodeConfig({ data, onChange }: ConditionNodeConfigProps) {
  const [condition, setCondition] = useState(data.condition || '');
  const [branches, setBranches] = useState(data.branches || [
    { name: 'true', label: 'True', color: '#10b981' },
    { name: 'false', label: 'False', color: '#ef4444' },
  ]);

  const handleConditionChange = (value: string) => {
    setCondition(value);
    onChange({ ...data, condition: value });
  };

  const handleBranchChange = (index: number, field: string, value: string) => {
    const newBranches = [...branches];
    newBranches[index] = { ...newBranches[index], [field]: value };
    setBranches(newBranches);
    onChange({ ...data, branches: newBranches });
  };

  const addBranch = () => {
    const newBranches = [...branches, { name: `branch${branches.length}`, label: `Branch ${branches.length}`, color: '#6366f1' }];
    setBranches(newBranches);
    onChange({ ...data, branches: newBranches });
  };

  const removeBranch = (index: number) => {
    if (branches.length <= 2) return; // Keep at least 2 branches
    const newBranches = branches.filter((_: any, i: number) => i !== index);
    setBranches(newBranches);
    onChange({ ...data, branches: newBranches });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Condition Expression</CardTitle>
          <CardDescription>
            Define the condition to evaluate (Python expression)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="condition">Expression</Label>
            <Textarea
              id="condition"
              value={condition}
              onChange={(e) => handleConditionChange(e.target.value)}
              placeholder="e.g., data['score'] > 0.8"
              rows={3}
              className="font-mono text-sm"
            />
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              <strong>Available variables:</strong> data, context, input
              <br />
              <strong>Example:</strong> {`data['type'] == 'urgent' or data['priority'] > 5`}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Branches</CardTitle>
          <CardDescription>
            Configure output branches for this condition
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {branches.map((branch: any, index: number) => (
            <div key={index} className="flex items-center gap-2 p-3 border rounded-lg">
              <div
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: branch.color }}
              />
              <div className="flex-1 grid grid-cols-2 gap-2">
                <div>
                  <Label className="text-xs">Name</Label>
                  <Input
                    value={branch.name}
                    onChange={(e) => handleBranchChange(index, 'name', e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs">Label</Label>
                  <Input
                    value={branch.label}
                    onChange={(e) => handleBranchChange(index, 'label', e.target.value)}
                    className="h-8 text-sm"
                  />
                </div>
              </div>
              {branches.length > 2 && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => removeBranch(index)}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>
          ))}

          <Button
            variant="outline"
            size="sm"
            onClick={addBranch}
            className="w-full"
          >
            <Plus className="h-4 w-4 mr-2" />
            Add Branch
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Examples</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="text-xs space-y-2">
            <div>
              <Badge variant="outline" className="mb-1">Simple comparison</Badge>
              <code className="block bg-muted p-2 rounded text-xs">
                {`data['score'] > 0.8`}
              </code>
            </div>
            <div>
              <Badge variant="outline" className="mb-1">Multiple conditions</Badge>
              <code className="block bg-muted p-2 rounded text-xs">
                {`data['type'] == 'urgent' and data['priority'] > 5`}
              </code>
            </div>
            <div>
              <Badge variant="outline" className="mb-1">String matching</Badge>
              <code className="block bg-muted p-2 rounded text-xs">
                'error' in data['message'].lower()
              </code>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
