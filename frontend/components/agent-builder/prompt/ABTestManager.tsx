'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import {
  Plus,
  Play,
  Pause,
  CheckCircle,
  TrendingUp,
  Users,
  Target,
  Clock,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';

interface ABTestManagerProps {
  agentId: string;
}

interface ABTest {
  id: string;
  name: string;
  status: 'draft' | 'running' | 'completed' | 'paused';
  variants: Array<{
    id: string;
    name: string;
    prompt: string;
    traffic_percentage: number;
    executions: number;
    success_rate: number;
    avg_response_time: number;
    avg_cost: number;
  }>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  winner?: string;
}

export function ABTestManager({ agentId }: ABTestManagerProps) {
  const { toast } = useToast();
  const [tests, setTests] = useState<ABTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newTestName, setNewTestName] = useState('');
  const [variantA, setVariantA] = useState('');
  const [variantB, setVariantB] = useState('');

  useEffect(() => {
    loadTests();
  }, [agentId]);

  const loadTests = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getABTests(agentId);
      setTests(data.tests || []);
    } catch (error) {
      console.error('Failed to load A/B tests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTest = async () => {
    if (!newTestName || !variantA || !variantB) {
      toast({
        title: 'Validation Error',
        description: 'Please fill in all fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      await agentBuilderAPI.createABTest(agentId, {
        name: newTestName,
        variants: [
          { name: 'Variant A', prompt: variantA, traffic_percentage: 50 },
          { name: 'Variant B', prompt: variantB, traffic_percentage: 50 },
        ],
      });

      toast({
        title: 'Success',
        description: 'A/B test created successfully',
      });

      setCreateDialogOpen(false);
      setNewTestName('');
      setVariantA('');
      setVariantB('');
      loadTests();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to create A/B test',
        variant: 'destructive',
      });
    }
  };

  const handleStartTest = async (testId: string) => {
    try {
      await agentBuilderAPI.startABTest(agentId, testId);
      toast({
        title: 'Test Started',
        description: 'A/B test is now running',
      });
      loadTests();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to start test',
        variant: 'destructive',
      });
    }
  };

  const handlePauseTest = async (testId: string) => {
    try {
      await agentBuilderAPI.pauseABTest(agentId, testId);
      toast({
        title: 'Test Paused',
        description: 'A/B test has been paused',
      });
      loadTests();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to pause test',
        variant: 'destructive',
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      draft: 'secondary',
      running: 'default',
      completed: 'outline',
      paused: 'destructive',
    };
    return <Badge variant={variants[status] || 'secondary'}>{status}</Badge>;
  };

  const getWinnerVariant = (test: ABTest) => {
    if (!test.winner) return null;
    return test.variants.find((v) => v.id === test.winner);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">A/B Tests</h3>
          <p className="text-sm text-muted-foreground">
            Compare different prompts to find the best performer
          </p>
        </div>
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create A/B Test
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Create New A/B Test</DialogTitle>
              <DialogDescription>
                Compare two prompt variants to see which performs better
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="test-name">Test Name</Label>
                <Input
                  id="test-name"
                  value={newTestName}
                  onChange={(e) => setNewTestName(e.target.value)}
                  placeholder="e.g., Clarity vs Brevity"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="variant-a">Variant A (50% traffic)</Label>
                <Textarea
                  id="variant-a"
                  value={variantA}
                  onChange={(e) => setVariantA(e.target.value)}
                  placeholder="Enter first prompt variant..."
                  rows={4}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="variant-b">Variant B (50% traffic)</Label>
                <Textarea
                  id="variant-b"
                  value={variantB}
                  onChange={(e) => setVariantB(e.target.value)}
                  placeholder="Enter second prompt variant..."
                  rows={4}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreateTest}>Create Test</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {tests.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No A/B tests yet. Create one to start comparing prompts.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {tests.map((test) => (
            <Card key={test.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <CardTitle>{test.name}</CardTitle>
                      {getStatusBadge(test.status)}
                    </div>
                    <CardDescription>
                      Created {new Date(test.created_at).toLocaleDateString()}
                      {test.started_at && ` • Started ${new Date(test.started_at).toLocaleDateString()}`}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    {test.status === 'draft' && (
                      <Button size="sm" onClick={() => handleStartTest(test.id)}>
                        <Play className="mr-2 h-4 w-4" />
                        Start Test
                      </Button>
                    )}
                    {test.status === 'running' && (
                      <Button size="sm" variant="outline" onClick={() => handlePauseTest(test.id)}>
                        <Pause className="mr-2 h-4 w-4" />
                        Pause
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {test.variants.map((variant) => {
                    const isWinner = test.winner === variant.id;
                    return (
                      <Card key={variant.id} className={isWinner ? 'border-green-500 border-2' : ''}>
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <h4 className="font-semibold">{variant.name}</h4>
                              {isWinner && (
                                <Badge variant="default" className="bg-green-500">
                                  <CheckCircle className="mr-1 h-3 w-3" />
                                  Winner
                                </Badge>
                              )}
                            </div>
                            <Badge variant="outline">{variant.traffic_percentage}% traffic</Badge>
                          </div>

                          <div className="grid grid-cols-4 gap-4 mb-3">
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Executions</div>
                              <div className="text-lg font-semibold">{variant.executions}</div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Success Rate</div>
                              <div className="text-lg font-semibold">{variant.success_rate}%</div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Avg Time</div>
                              <div className="text-lg font-semibold">{variant.avg_response_time.toFixed(2)}s</div>
                            </div>
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Avg Cost</div>
                              <div className="text-lg font-semibold">${variant.avg_cost.toFixed(4)}</div>
                            </div>
                          </div>

                          <details className="text-sm">
                            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                              View prompt
                            </summary>
                            <pre className="mt-2 p-3 bg-muted rounded-md overflow-auto text-xs">
                              {variant.prompt}
                            </pre>
                          </details>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
