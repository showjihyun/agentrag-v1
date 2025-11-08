'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Bug,
  Clock,
  Zap,
} from 'lucide-react';

interface ExecutionStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: string;
  endTime?: string;
  duration?: number;
  input?: any;
  output?: any;
  error?: string;
}

interface ExecutionDebuggerProps {
  executionId: string;
  steps: ExecutionStep[];
  currentStep?: number;
  onStepTo?: (stepIndex: number) => void;
  onReset?: () => void;
}

export function ExecutionDebugger({
  executionId,
  steps,
  currentStep = 0,
  onStepTo,
  onReset,
}: ExecutionDebuggerProps) {
  const [selectedStep, setSelectedStep] = React.useState(currentStep);
  const [isPaused, setIsPaused] = React.useState(false);

  const step = steps[selectedStep];

  const handleStepForward = () => {
    if (selectedStep < steps.length - 1) {
      const nextStep = selectedStep + 1;
      setSelectedStep(nextStep);
      onStepTo?.(nextStep);
    }
  };

  const handleReset = () => {
    setSelectedStep(0);
    setIsPaused(false);
    onReset?.();
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Execution Debugger</CardTitle>
            <CardDescription>
              Step through execution: {selectedStep + 1} / {steps.length}
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsPaused(!isPaused)}
              title={isPaused ? 'Resume' : 'Pause'}
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={handleStepForward}
              disabled={selectedStep >= steps.length - 1}
              title="Step forward"
            >
              <SkipForward className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={handleReset}
              title="Reset"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Timeline */}
        <div className="space-y-2">
          <div className="text-sm font-semibold">Execution Timeline</div>
          <ScrollArea className="w-full">
            <div className="flex gap-2 pb-2">
              {steps.map((s, index) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedStep(index)}
                  className={`
                    flex-shrink-0 px-3 py-2 rounded-md text-xs font-medium
                    transition-colors border
                    ${
                      index === selectedStep
                        ? 'bg-primary text-primary-foreground border-primary'
                        : 'bg-background hover:bg-accent border-border'
                    }
                  `}
                >
                  <div className="flex items-center gap-2">
                    <span>{index + 1}</span>
                    {s.status === 'completed' && (
                      <span className="text-green-500">✓</span>
                    )}
                    {s.status === 'failed' && (
                      <span className="text-red-500">✗</span>
                    )}
                    {s.status === 'running' && (
                      <Zap className="h-3 w-3 animate-pulse" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Step Details */}
        {step && (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="input">Input</TabsTrigger>
              <TabsTrigger value="output">Output</TabsTrigger>
              <TabsTrigger value="variables">Variables</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm font-semibold mb-1">Step Name</div>
                  <div className="text-sm">{step.name}</div>
                </div>
                <div>
                  <div className="text-sm font-semibold mb-1">Status</div>
                  <Badge
                    variant={
                      step.status === 'completed'
                        ? 'default'
                        : step.status === 'failed'
                        ? 'destructive'
                        : 'secondary'
                    }
                  >
                    {step.status}
                  </Badge>
                </div>
              </div>

              {step.duration && (
                <div>
                  <div className="text-sm font-semibold mb-1 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    Duration
                  </div>
                  <div className="text-sm">{step.duration}ms</div>
                </div>
              )}

              {step.error && (
                <div>
                  <div className="text-sm font-semibold mb-1 flex items-center gap-2 text-destructive">
                    <Bug className="h-4 w-4" />
                    Error
                  </div>
                  <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                    {step.error}
                  </div>
                </div>
              )}
            </TabsContent>

            <TabsContent value="input">
              <ScrollArea className="h-[300px] w-full rounded-md border p-4">
                <pre className="text-xs">
                  {JSON.stringify(step.input, null, 2)}
                </pre>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="output">
              <ScrollArea className="h-[300px] w-full rounded-md border p-4">
                <pre className="text-xs">
                  {JSON.stringify(step.output, null, 2)}
                </pre>
              </ScrollArea>
            </TabsContent>

            <TabsContent value="variables">
              <div className="text-sm text-muted-foreground">
                Variable inspector coming soon...
              </div>
            </TabsContent>
          </Tabs>
        )}
      </CardContent>
    </Card>
  );
}
