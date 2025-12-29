'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI } from '@/lib/api/agent-builder';
import { ArrowLeft, Play, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';

interface TestResult {
  success: boolean;
  execution_id?: string;
  output?: any;
  error?: string;
  duration_ms?: number;
  timestamp: string;
}

export default function AgentTestPage() {
  const params = useParams();
  const router = useRouter();
  const { toast } = useToast();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testResults, setTestResults] = useState<TestResult[]>([]);

  useEffect(() => {
    loadAgent();
  }, [agentId]);

  const loadAgent = async () => {
    try {
      setLoading(true);
      const data = await agentBuilderAPI.getAgent(agentId);
      setAgent(data);
    } catch (error: any) {
      console.error('Failed to load agent:', error);
      toast({
        title: 'Error',
        description: error.message || 'Failed to load agent',
      });
    } finally {
      setLoading(false);
    }
  };

  const runTest = async () => {
    if (!testInput.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter test input',
      });
      return;
    }

    try {
      setTesting(true);
      const startTime = Date.now();

      // Execute agent
      const result = await agentBuilderAPI.executeAgent(agentId, {
        input: testInput,
      });

      const duration = Date.now() - startTime;

      const testResult: TestResult = {
        success: result.success || false,
        ...(result.execution_id && { execution_id: result.execution_id }),
        output: result.output || result.result,
        ...(result.error && { error: result.error }),
        duration_ms: duration,
        timestamp: new Date().toISOString(),
      };

      setTestResults([testResult, ...testResults]);

      if (testResult.success) {
        toast({
          title: 'Test Successful',
          description: 'Agent executed successfully',
        });
      } else {
        toast({
          title: 'Test Failed',
          description: testResult.error || 'Agent execution failed',
        });
      }
    } catch (error: any) {
      console.error('Test execution failed:', error);
      
      const testResult: TestResult = {
        success: false,
        error: error.message || 'Test execution failed',
        duration_ms: 0,
        timestamp: new Date().toISOString(),
      };

      setTestResults([testResult, ...testResults]);

      toast({
        title: 'Error',
        description: error.message || 'Test execution failed',
      });
    } finally {
      setTesting(false);
    }
  };

  const clearResults = () => {
    setTestResults([]);
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="container mx-auto p-6">
        <Card>
          <CardContent className="p-12 text-center">
            <XCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
            <h3 className="text-lg font-semibold mb-2">Agent Not Found</h3>
            <p className="text-muted-foreground mb-4">
              The agent you're looking for doesn't exist or you don't have access to it.
            </p>
            <Button onClick={() => router.push('/agent-builder/agents')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Agents
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push(`/agent-builder/agents/${agentId}`)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-3xl font-bold">Test Agent</h1>
            <p className="text-muted-foreground mt-1">
              {agent.name}
            </p>
          </div>
        </div>
        <Badge variant={agent.is_active ? 'default' : 'secondary'}>
          {agent.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </div>

      {/* Test Input */}
      <Card>
        <CardHeader>
          <CardTitle>Test Input</CardTitle>
          <CardDescription>
            Enter input to test your agent
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            placeholder="Enter test input..."
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            rows={4}
            className="font-mono"
          />
          <div className="flex items-center gap-2">
            <Button
              onClick={runTest}
              disabled={testing || !testInput.trim()}
            >
              {testing ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Test
                </>
              )}
            </Button>
            {testResults.length > 0 && (
              <Button variant="outline" onClick={clearResults}>
                Clear Results
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Test Results */}
      {testResults.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Test Results</h2>
          {testResults.map((result, index) => (
            <Card key={index}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {result.success ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-600" />
                    )}
                    <CardTitle className="text-base">
                      {result.success ? 'Success' : 'Failed'}
                    </CardTitle>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    {result.duration_ms !== undefined && (
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {result.duration_ms}ms
                      </div>
                    )}
                    <span>{new Date(result.timestamp).toLocaleString()}</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.execution_id && (
                  <div>
                    <div className="text-sm font-medium mb-1">Execution ID</div>
                    <code className="text-xs bg-muted p-2 rounded block">
                      {result.execution_id}
                    </code>
                  </div>
                )}
                
                {result.output && (
                  <div>
                    <div className="text-sm font-medium mb-1">Output</div>
                    <pre className="text-xs bg-muted p-4 rounded overflow-auto max-h-64">
                      {typeof result.output === 'string'
                        ? result.output
                        : JSON.stringify(result.output, null, 2)}
                    </pre>
                  </div>
                )}
                
                {result.error && (
                  <div>
                    <div className="text-sm font-medium mb-1 text-red-600">Error</div>
                    <pre className="text-xs bg-red-50 text-red-900 p-4 rounded overflow-auto">
                      {result.error}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {testResults.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <Play className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Test Results Yet</h3>
            <p className="text-muted-foreground">
              Enter test input above and click "Run Test" to see results here.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
