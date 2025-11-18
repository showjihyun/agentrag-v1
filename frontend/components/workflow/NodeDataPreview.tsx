'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  FileJson,
  Table as TableIcon,
  Code,
  Copy,
  Check,
  Download,
  Eye,
  EyeOff,
} from 'lucide-react';

interface NodeDataPreviewProps {
  nodeId: string;
  nodeName: string;
  inputData?: any;
  outputData?: any;
  executionTime?: number;
  status?: string;
}

export function NodeDataPreview({
  nodeId,
  nodeName,
  inputData,
  outputData,
  executionTime,
  status,
}: NodeDataPreviewProps) {
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState<'json' | 'table' | 'raw'>('json');
  const [showSensitive, setShowSensitive] = useState(false);

  const copyToClipboard = (data: any) => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadData = (data: any, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const maskSensitiveData = (data: any): any => {
    if (!data || typeof data !== 'object') return data;
    
    const sensitiveKeys = ['password', 'token', 'secret', 'key', 'api_key', 'apiKey'];
    const masked = Array.isArray(data) ? [...data] : { ...data };
    
    Object.keys(masked).forEach((key) => {
      if (sensitiveKeys.some((sk) => key.toLowerCase().includes(sk))) {
        masked[key] = showSensitive ? masked[key] : '••••••••';
      } else if (typeof masked[key] === 'object') {
        masked[key] = maskSensitiveData(masked[key]);
      }
    });
    
    return masked;
  };

  const renderTableView = (data: any) => {
    if (!data) return <p className="text-sm text-muted-foreground">No data</p>;
    
    // If data is an array of objects, render as table
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      const keys = Object.keys(data[0]);
      return (
        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                {keys.map((key) => (
                  <TableHead key={key}>{key}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.slice(0, 10).map((row, idx) => (
                <TableRow key={idx}>
                  {keys.map((key) => (
                    <TableCell key={key} className="font-mono text-xs">
                      {typeof row[key] === 'object'
                        ? JSON.stringify(row[key])
                        : String(row[key])}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {data.length > 10 && (
            <div className="p-2 text-xs text-center text-muted-foreground border-t">
              Showing 10 of {data.length} rows
            </div>
          )}
        </div>
      );
    }
    
    // If data is a single object, render as key-value table
    if (typeof data === 'object' && !Array.isArray(data)) {
      return (
        <div className="border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-1/3">Key</TableHead>
                <TableHead>Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(data).map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell className="font-medium">{key}</TableCell>
                  <TableCell className="font-mono text-xs">
                    {typeof value === 'object'
                      ? JSON.stringify(value)
                      : String(value)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      );
    }
    
    return <p className="text-sm text-muted-foreground">Data format not suitable for table view</p>;
  };

  const renderJsonView = (data: any) => {
    if (!data) return <p className="text-sm text-muted-foreground">No data</p>;
    
    const maskedData = maskSensitiveData(data);
    
    return (
      <pre className="text-xs bg-muted p-4 rounded-md overflow-x-auto max-h-96">
        {JSON.stringify(maskedData, null, 2)}
      </pre>
    );
  };

  const renderRawView = (data: any) => {
    if (!data) return <p className="text-sm text-muted-foreground">No data</p>;
    
    return (
      <pre className="text-xs bg-muted p-4 rounded-md overflow-x-auto max-h-96 whitespace-pre-wrap break-all">
        {JSON.stringify(data)}
      </pre>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Eye className="h-4 w-4" />
            {nodeName}
          </CardTitle>
          <div className="flex items-center gap-2">
            {status && (
              <Badge
                variant={
                  status === 'success'
                    ? 'default'
                    : status === 'error'
                    ? 'destructive'
                    : 'secondary'
                }
              >
                {status}
              </Badge>
            )}
            {executionTime !== undefined && (
              <Badge variant="outline" className="text-xs">
                {executionTime}ms
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs defaultValue="output" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="input">Input</TabsTrigger>
            <TabsTrigger value="output">Output</TabsTrigger>
          </TabsList>
          
          <TabsContent value="input" className="space-y-3">
            {/* View Mode Selector */}
            <div className="flex items-center justify-between">
              <div className="flex gap-1">
                <Button
                  variant={viewMode === 'json' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('json')}
                  className="h-7 px-2"
                >
                  <FileJson className="h-3 w-3 mr-1" />
                  JSON
                </Button>
                <Button
                  variant={viewMode === 'table' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className="h-7 px-2"
                >
                  <TableIcon className="h-3 w-3 mr-1" />
                  Table
                </Button>
                <Button
                  variant={viewMode === 'raw' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('raw')}
                  className="h-7 px-2"
                >
                  <Code className="h-3 w-3 mr-1" />
                  Raw
                </Button>
              </div>
              
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSensitive(!showSensitive)}
                  className="h-7 px-2"
                >
                  {showSensitive ? (
                    <EyeOff className="h-3 w-3" />
                  ) : (
                    <Eye className="h-3 w-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(inputData)}
                  className="h-7 px-2"
                >
                  {copied ? (
                    <Check className="h-3 w-3 text-green-600" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => downloadData(inputData, `${nodeId}-input.json`)}
                  className="h-7 px-2"
                >
                  <Download className="h-3 w-3" />
                </Button>
              </div>
            </div>
            
            {/* Data Display */}
            {viewMode === 'json' && renderJsonView(inputData)}
            {viewMode === 'table' && renderTableView(inputData)}
            {viewMode === 'raw' && renderRawView(inputData)}
          </TabsContent>
          
          <TabsContent value="output" className="space-y-3">
            {/* View Mode Selector */}
            <div className="flex items-center justify-between">
              <div className="flex gap-1">
                <Button
                  variant={viewMode === 'json' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('json')}
                  className="h-7 px-2"
                >
                  <FileJson className="h-3 w-3 mr-1" />
                  JSON
                </Button>
                <Button
                  variant={viewMode === 'table' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className="h-7 px-2"
                >
                  <TableIcon className="h-3 w-3 mr-1" />
                  Table
                </Button>
                <Button
                  variant={viewMode === 'raw' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('raw')}
                  className="h-7 px-2"
                >
                  <Code className="h-3 w-3 mr-1" />
                  Raw
                </Button>
              </div>
              
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSensitive(!showSensitive)}
                  className="h-7 px-2"
                >
                  {showSensitive ? (
                    <EyeOff className="h-3 w-3" />
                  ) : (
                    <Eye className="h-3 w-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => copyToClipboard(outputData)}
                  className="h-7 px-2"
                >
                  {copied ? (
                    <Check className="h-3 w-3 text-green-600" />
                  ) : (
                    <Copy className="h-3 w-3" />
                  )}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => downloadData(outputData, `${nodeId}-output.json`)}
                  className="h-7 px-2"
                >
                  <Download className="h-3 w-3" />
                </Button>
              </div>
            </div>
            
            {/* Data Display */}
            {viewMode === 'json' && renderJsonView(outputData)}
            {viewMode === 'table' && renderTableView(outputData)}
            {viewMode === 'raw' && renderRawView(outputData)}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
