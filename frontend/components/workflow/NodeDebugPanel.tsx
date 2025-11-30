'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Clock, AlertCircle, CheckCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NodeDebugPanelProps {
  nodeId: string;
  nodeName: string;
  executionData?: {
    input: any;
    output: any;
    error?: string;
    duration: number;
    timestamp: string;
    status: 'success' | 'failed' | 'running' | 'pending' | 'skipped' | 'waiting';
  };
  onClose: () => void;
}

export function NodeDebugPanel({ 
  nodeId, 
  nodeName, 
  executionData,
  onClose 
}: NodeDebugPanelProps) {
  if (!executionData) {
    return (
      <Card className="w-96">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{nodeName}</span>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">
            No execution data available. Run the workflow to see results.
          </p>
        </CardContent>
      </Card>
    );
  }

  const StatusIcon = executionData.status === 'success' 
    ? CheckCircle 
    : executionData.status === 'failed' 
    ? AlertCircle 
    : Clock;

  const statusColor = 
    executionData.status === 'success' ? 'text-green-500' :
    executionData.status === 'failed' ? 'text-red-500' : 
    executionData.status === 'running' ? 'text-blue-500' :
    'text-gray-500';

  return (
    <Card className="w-96 max-h-[600px] overflow-auto shadow-lg">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="truncate">{nodeName}</span>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </CardTitle>
        <div className="flex items-center gap-2 text-sm">
          <Badge variant={
            executionData.status === 'success' ? 'default' :
            executionData.status === 'failed' ? 'destructive' : 'secondary'
          } className="flex items-center gap-1">
            <StatusIcon className={`w-3 h-3 ${statusColor}`} />
            {executionData.status}
          </Badge>
          <span className="text-muted-foreground text-xs">
            {executionData.duration}ms
          </span>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <Tabs defaultValue="output" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="input" className="text-xs">Input</TabsTrigger>
            <TabsTrigger value="output" className="text-xs">Output</TabsTrigger>
            <TabsTrigger value="error" className="text-xs">
              Error
              {executionData.error && (
                <span className="ml-1 w-2 h-2 bg-red-500 rounded-full" />
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="input" className="mt-4">
            <pre className="bg-muted p-3 rounded-lg text-xs overflow-auto max-h-80 font-mono">
              {JSON.stringify(executionData.input, null, 2)}
            </pre>
          </TabsContent>
          
          <TabsContent value="output" className="mt-4">
            <pre className="bg-muted p-3 rounded-lg text-xs overflow-auto max-h-80 font-mono">
              {JSON.stringify(executionData.output, null, 2)}
            </pre>
          </TabsContent>
          
          <TabsContent value="error" className="mt-4">
            {executionData.error ? (
              <div className="bg-destructive/10 p-3 rounded-lg">
                <p className="text-destructive text-xs font-mono whitespace-pre-wrap">
                  {executionData.error}
                </p>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">No errors</p>
            )}
          </TabsContent>
        </Tabs>
        
        <div className="mt-4 pt-4 border-t text-xs text-muted-foreground space-y-1">
          <p>Executed: {new Date(executionData.timestamp).toLocaleString()}</p>
          <p className="font-mono">Node ID: {nodeId}</p>
        </div>
      </CardContent>
    </Card>
  );
}
