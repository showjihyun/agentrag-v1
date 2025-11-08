'use client';

import { useState, useEffect } from 'react';
import { Play, Loader2, CheckCircle, XCircle, Clock, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/hooks/use-toast';
import { agentBuilderAPI, Block, BlockTestResult } from '@/lib/api/agent-builder';

interface BlockTestPanelProps {
  blockId: string;
}

export default function BlockTestPanel({ blockId }: BlockTestPanelProps) {
  const { toast } = useToast();
  const [block, setBlock] = useState<Block | null>(null);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testInput, setTestInput] = useState<Record<string, any>>({});
  const [testResult, setTestResult] = useState<BlockTestResult | null>(null);

  useEffect(() => {
    loadBlock();
  }, [blockId]);

  const loadBlock = async () => {
    try {
      setLoading(true);
      const blockData = await agentBuilderAPI.getBlock(blockId);
      setBlock(blockData);
      
      // Initialize test input with default values based on schema
      if (blockData.input_schema?.properties) {
        const defaultInput: Record<string, any> = {};
        Object.entries(blockData.input_schema.properties).forEach(([key, schema]: [string, any]) => {
          if (schema.type === 'string') defaultInput[key] = '';
          else if (schema.type === 'number') defaultInput[key] = 0;
          else if (schema.type === 'boolean') defaultInput[key] = false;
          else if (schema.type === 'array') defaultInput[key] = [];
          else if (schema.type === 'object') defaultInput[key] = {};
        });
        setTestInput(defaultInput);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load block',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRunTest = async () => {
    if (!block) return;

    try {
      setTesting(true);
      setTestResult(null);
      
      const result = await agentBuilderAPI.testBlock(blockId, { input_data: testInput });
      setTestResult(result);
      
      if (result.success) {
        toast({
          title: 'Test Passed',
          description: `Block executed successfully in ${result.duration_ms}ms`,
        });
      } else {
        toast({
          title: 'Test Failed',
          description: result.error || 'Block execution failed',
          variant: 'destructive',
        });
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to execute test',
        variant: 'destructive',
      });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveTestCase = () => {
    toast({
      title: 'Test Case Saved',
      description: 'Test case saved successfully',
    });
  };

  const handleInputChange = (key: string, value: any) => {
    setTestInput((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const renderInputField = (key: string, schema: any) => {
    const value = testInput[key];

    if (schema.type === 'string') {
      return (
        <Input
          value={value || ''}
          onChange={(e) => handleInputChange(key, e.target.value)}
          placeholder={schema.description || `Enter ${key}`}
        />
      );
    } else if (schema.type === 'number') {
      return (
        <Input
          type="number"
          value={value || 0}
          onChange={(e) => handleInputChange(key, parseFloat(e.target.value) || 0)}
          placeholder={schema.description || `Enter ${key}`}
        />
      );
    } else if (schema.type === 'boolean') {
      return (
        <select
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          value={value ? 'true' : 'false'}
          onChange={(e) => handleInputChange(key, e.target.value === 'true')}
        >
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
      );
    } else {
      return (
        <Input
          value={typeof value === 'object' ? JSON.stringify(value) : value || ''}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              handleInputChange(key, parsed);
            } catch {
              handleInputChange(key, e.target.value);
            }
          }}
          placeholder={`Enter ${key} (JSON)`}
        />
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!block) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Block not found</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Block Info */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{block.name}</CardTitle>
              <CardDescription className="capitalize">{block.block_type} Block</CardDescription>
            </div>
            <Badge variant="outline">{block.version || '1.0.0'}</Badge>
          </div>
        </CardHeader>
        {block.description && (
          <CardContent>
            <p className="text-sm text-muted-foreground">{block.description}</p>
          </CardContent>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Test Input</CardTitle>
            <CardDescription>
              Provide input values to test the block
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {block.input_schema?.properties ? (
              Object.entries(block.input_schema.properties).map(([key, schema]: [string, any]) => (
                <div key={key} className="space-y-2">
                  <Label htmlFor={key}>
                    {key}
                    {block.input_schema?.required?.includes(key) && (
                      <span className="text-destructive ml-1">*</span>
                    )}
                  </Label>
                  {renderInputField(key, schema)}
                  {schema.description && (
                    <p className="text-xs text-muted-foreground">{schema.description}</p>
                  )}
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No input parameters defined</p>
            )}

            <Separator />

            <div className="flex gap-2">
              <Button 
                onClick={handleRunTest} 
                disabled={testing}
                className="flex-1"
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
              <Button 
                variant="outline" 
                onClick={handleSaveTestCase}
                disabled={!testResult}
              >
                <Save className="mr-2 h-4 w-4" />
                Save
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Output Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Test Output</CardTitle>
            <CardDescription>
              Results from the block execution
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!testResult ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Play className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-sm text-muted-foreground">
                  Run a test to see the output
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Status */}
                <div className="flex items-center gap-2">
                  {testResult.success ? (
                    <>
                      <CheckCircle className="h-5 w-5 text-green-500" />
                      <span className="font-medium text-green-500">Test Passed</span>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-5 w-5 text-destructive" />
                      <span className="font-medium text-destructive">Test Failed</span>
                    </>
                  )}
                </div>

                <Separator />

                {/* Metrics */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Duration
                    </span>
                    <span className="font-medium">{testResult.duration_ms}ms</span>
                  </div>
                </div>

                <Separator />

                {/* Output */}
                {testResult.success ? (
                  <div className="space-y-2">
                    <Label>Output</Label>
                    <ScrollArea className="h-[200px] rounded-md border p-4">
                      <pre className="text-xs">
                        {JSON.stringify(testResult.output, null, 2)}
                      </pre>
                    </ScrollArea>
                  </div>
                ) : (
                  <Alert variant="destructive">
                    <AlertDescription>
                      <div className="space-y-2">
                        <p className="font-medium">Error</p>
                        <pre className="text-xs whitespace-pre-wrap">
                          {testResult.error}
                        </pre>
                      </div>
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
