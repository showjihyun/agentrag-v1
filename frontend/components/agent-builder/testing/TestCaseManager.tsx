'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/Toast';
import {
  Plus,
  Play,
  Trash2,
  Edit2,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';

interface TestCase {
  id: string;
  name: string;
  description?: string;
  input: Record<string, any>;
  expectedOutput?: any;
  status?: 'pending' | 'running' | 'passed' | 'failed';
  lastRun?: string;
  duration?: number;
  error?: string;
}

interface TestCaseManagerProps {
  agentId: string;
  testCases?: TestCase[];
  onRunTest?: (testCaseId: string) => Promise<void>;
  onRunAll?: () => Promise<void>;
  onAddTestCase?: (testCase: Omit<TestCase, 'id'>) => Promise<void>;
  onUpdateTestCase?: (testCaseId: string, testCase: Partial<TestCase>) => Promise<void>;
  onDeleteTestCase?: (testCaseId: string) => Promise<void>;
}

export function TestCaseManager({
  agentId,
  testCases = [],
  onRunTest,
  onRunAll,
  onAddTestCase,
  onUpdateTestCase,
  onDeleteTestCase,
}: TestCaseManagerProps) {
  const { toast } = useToast();
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const [editingCase, setEditingCase] = React.useState<TestCase | null>(null);
  const [formData, setFormData] = React.useState({
    name: '',
    description: '',
    input: '{}',
    expectedOutput: '',
  });

  const handleOpenDialog = (testCase?: TestCase) => {
    if (testCase) {
      setEditingCase(testCase);
      setFormData({
        name: testCase.name,
        description: testCase.description || '',
        input: JSON.stringify(testCase.input, null, 2),
        expectedOutput: testCase.expectedOutput
          ? JSON.stringify(testCase.expectedOutput, null, 2)
          : '',
      });
    } else {
      setEditingCase(null);
      setFormData({
        name: '',
        description: '',
        input: '{}',
        expectedOutput: '',
      });
    }
    setIsDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      const input = JSON.parse(formData.input);
      const expectedOutput = formData.expectedOutput
        ? JSON.parse(formData.expectedOutput)
        : undefined;

      const testCase = {
        name: formData.name,
        description: formData.description,
        input,
        expectedOutput,
      };

      if (editingCase && onUpdateTestCase) {
        await onUpdateTestCase(editingCase.id, testCase);
        toast({
          title: 'Test case updated',
          description: 'Test case has been updated successfully',
        });
      } else if (onAddTestCase) {
        await onAddTestCase(testCase);
        toast({
          title: 'Test case created',
          description: 'Test case has been created successfully',
        });
      }

      setIsDialogOpen(false);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Invalid JSON',
        description: 'Please check your input and expected output JSON',
      });
    }
  };

  const handleRunTest = async (testCaseId: string) => {
    if (!onRunTest) return;

    try {
      await onRunTest(testCaseId);
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Test failed',
        description: 'Failed to run test case',
      });
    }
  };

  const handleRunAll = async () => {
    if (!onRunAll) return;

    try {
      await onRunAll();
      toast({
        title: 'Tests running',
        description: `Running ${testCases.length} test cases`,
      });
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Tests failed',
        description: 'Failed to run test cases',
      });
    }
  };

  const getStatusIcon = (status?: TestCase['status']) => {
    switch (status) {
      case 'passed':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      default:
        return <Clock className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const passedCount = testCases.filter((t) => t.status === 'passed').length;
  const failedCount = testCases.filter((t) => t.status === 'failed').length;

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Test Cases</CardTitle>
              <CardDescription>
                Manage and run test cases for your agent
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleRunAll}
                disabled={testCases.length === 0 || !onRunAll}
              >
                <Play className="h-4 w-4 mr-2" />
                Run All
              </Button>
              <Button onClick={() => handleOpenDialog()}>
                <Plus className="h-4 w-4 mr-2" />
                Add Test
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Summary */}
          {testCases.length > 0 && (
            <div className="flex gap-4 mb-4 p-4 bg-muted rounded-lg">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{testCases.length} Total</Badge>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span className="text-sm">{passedCount} Passed</span>
              </div>
              <div className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-500" />
                <span className="text-sm">{failedCount} Failed</span>
              </div>
            </div>
          )}

          {/* Test Cases List */}
          <ScrollArea className="h-[400px] w-full">
            {testCases.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <p>No test cases yet</p>
                <Button
                  variant="link"
                  onClick={() => handleOpenDialog()}
                  className="mt-2"
                >
                  Create your first test case
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                {testCases.map((testCase) => (
                  <div
                    key={testCase.id}
                    className="border rounded-lg p-4 space-y-3"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(testCase.status)}
                        <div>
                          <div className="font-semibold">{testCase.name}</div>
                          {testCase.description && (
                            <div className="text-sm text-muted-foreground">
                              {testCase.description}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRunTest(testCase.id)}
                          disabled={!onRunTest}
                        >
                          <Play className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleOpenDialog(testCase)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => onDeleteTestCase?.(testCase.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {testCase.lastRun && (
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>
                          Last run:{' '}
                          {new Date(testCase.lastRun).toLocaleString()}
                        </span>
                        {testCase.duration && (
                          <span>Duration: {testCase.duration}ms</span>
                        )}
                      </div>
                    )}

                    {testCase.error && (
                      <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                        {testCase.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>
              {editingCase ? 'Edit Test Case' : 'Add Test Case'}
            </DialogTitle>
            <DialogDescription>
              Define input and expected output for testing
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                placeholder="Test case name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="What does this test verify?"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="input">Input (JSON)</Label>
              <Textarea
                id="input"
                value={formData.input}
                onChange={(e) =>
                  setFormData({ ...formData, input: e.target.value })
                }
                placeholder='{"query": "test query"}'
                className="font-mono text-sm min-h-[100px]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="expectedOutput">
                Expected Output (JSON, optional)
              </Label>
              <Textarea
                id="expectedOutput"
                value={formData.expectedOutput}
                onChange={(e) =>
                  setFormData({ ...formData, expectedOutput: e.target.value })
                }
                placeholder='{"result": "expected result"}'
                className="font-mono text-sm min-h-[100px]"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={!formData.name}>
              {editingCase ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
