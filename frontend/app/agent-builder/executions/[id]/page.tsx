'use client';

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Clock, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { agentBuilderAPI } from '@/lib/api/agent-builder';

interface ExecutionDetail {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  duration?: number;
  node_executions: Array<{
    node_id: string;
    node_name: string;
    status: string;
    input: any;
    output: any;
    error?: string;
    started_at: string;
    completed_at?: string;
  }>;
}

export default function ExecutionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const executionId = params.id as string;
  
  const [execution, setExecution] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadExecution();
  }, [executionId]);

  const loadExecution = async () => {
    try {
      setLoading(true);
      // Extract workflow_id from execution if needed, or get from URL params
      // For now, we'll need to modify the page to accept workflow_id
      // Temporary: try to get execution directly
      const data = await agentBuilderAPI.getExecution(executionId);
      setExecution(data as any);
    } catch (err: any) {
      setError(err.message || 'Failed to load execution');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  if (error || !execution) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/20">
          <CardContent className="pt-6">
            <p className="text-red-700 dark:text-red-300">
              {error || 'Execution not found'}
            </p>
            <Button
              onClick={() => router.back()}
              className="mt-4"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (execution.status) {
      case 'running':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusBadge = () => {
    switch (execution.status) {
      case 'running':
        return <Badge className="bg-blue-500">Running</Badge>;
      case 'completed':
        return <Badge className="bg-green-500">Completed</Badge>;
      case 'failed':
        return <Badge className="bg-red-500">Failed</Badge>;
    }
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back
        </Button>
        
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Execution Details</h1>
            <p className="text-muted-foreground mt-1">
              {execution.workflow_name}
            </p>
          </div>
          {getStatusBadge()}
        </div>
      </div>

      {/* Summary */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon()}
            Execution Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Execution ID</p>
              <p className="font-mono text-sm">{execution.id.substring(0, 8)}...</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Started</p>
              <p className="text-sm">{new Date(execution.started_at).toLocaleString()}</p>
            </div>
            {execution.completed_at && (
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-sm">{new Date(execution.completed_at).toLocaleString()}</p>
              </div>
            )}
            {execution.duration && (
              <div>
                <p className="text-sm text-muted-foreground">Duration</p>
                <p className="text-sm flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {(execution.duration / 1000).toFixed(2)}s
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Node Executions */}
      <Card>
        <CardHeader>
          <CardTitle>Node Executions</CardTitle>
          <CardDescription>
            Detailed execution log for each node
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!execution.node_executions || execution.node_executions.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No node execution data available
            </p>
          ) : (
            <div className="space-y-4">
              {execution.node_executions.map((nodeExec, idx) => (
                <Card key={idx} className={`border-l-4 ${nodeExec.status === 'failed' ? 'border-l-red-500' : 'border-l-blue-500'}`}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-base">{nodeExec.node_name}</CardTitle>
                        <CardDescription>
                          Node execution details
                        </CardDescription>
                      </div>
                      <Badge className={nodeExec.status === 'failed' ? 'bg-red-500' : 'bg-green-500'}>
                        {nodeExec.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {/* Timestamps */}
                    {(nodeExec.started_at || nodeExec.completed_at) && (
                      <div className="text-xs text-muted-foreground">
                        {nodeExec.started_at && <div>Started: {new Date(nodeExec.started_at).toLocaleString()}</div>}
                        {nodeExec.completed_at && <div>Completed: {new Date(nodeExec.completed_at).toLocaleString()}</div>}
                      </div>
                    )}
                    
                    {/* Input */}
                    <div>
                      <p className="text-sm font-medium mb-1">Input:</p>
                      <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(nodeExec.input, null, 2)}
                      </pre>
                    </div>
                    
                    {/* Output */}
                    <div>
                      <p className="text-sm font-medium mb-1">Output:</p>
                      <pre className="text-xs bg-muted p-2 rounded overflow-auto max-h-32">
                        {JSON.stringify(nodeExec.output, null, 2)}
                      </pre>
                    </div>
                    
                    {/* Error */}
                    {nodeExec.error && (
                      <div>
                        <p className="text-sm font-medium mb-1 text-red-500">Error:</p>
                        <pre className="text-xs bg-red-50 dark:bg-red-950/20 p-2 rounded overflow-auto">
                          {nodeExec.error}
                        </pre>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
